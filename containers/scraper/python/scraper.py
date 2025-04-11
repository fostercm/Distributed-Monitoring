import aiohttp
import asyncio
import os
from time import perf_counter
from typing import List, Dict
from redis.asyncio import Redis as AsyncRedis
from itertools import product
import json
from ping3 import ping

async def write_to_redis(redis: AsyncRedis, metric: str, host: str, container_name: str, value: str, window_size: int) -> None:
    
    # Remove port from host
    if ":" in host:
        host = host.split(":")[0]
    
    if container_name != None:
        # Get key
        key = f"metric:{metric}:host:{host}:container:{container_name}"
        
        # Store the metric in Redis
        await redis.rpush(key, value)
        
        # Keep only the recent values
        if await redis.llen(key) > window_size:
            await redis.lpop(key)
    else:
        # Get key
        key = f"metric:{metric}:host:{host}"
        
        # Store the metric in Redis
        await redis.rpush(key, value)
        
        # Keep only the recent values
        if await redis.llen(key) > window_size:
            await redis.lpop(key)

async def scrape_container_metrics(monitor_host: str, container_names: List[str], window_size: int, session: aiohttp.ClientSession) -> dict:
    
    try:
        # Make the request
        async with session.get(f"http://{monitor_host}/metrics", params={'container_names' : container_names}) as response:
            response = await response.json()
        
    except:
        # If the request fails, flag all containers as down
        response = {
            container : {
                "cpu_absolute_usage": -1,
                "cpu_percent_usage": -1,
                "memory_absolute_usage": -1,
                "memory_percent_usage": -1,
                "network_input": -1,
                "network_output": -1,
                "disk_read": -1,
                "disk_write": -1
            } for container in container_names
        }
    
    # Execute the write tasks concurrently
    write_tasks = [write_to_redis(redis,
                                  metric,
                                  monitor_host,
                                  container_name,
                                  response[container_name][metric],
                                  window_size
                                ) for container_name, metric in product(
                                    container_names, ['cpu_absolute_usage', 
                                                      'cpu_percent_usage', 
                                                      'memory_absolute_usage', 
                                                      'memory_percent_usage', 
                                                      'network_input', 
                                                      'network_output', 
                                                      'disk_read', 
                                                      'disk_write'])
                ]
    await asyncio.gather(*write_tasks)

async def get_network_latency(monitor_host: str, window_size: int) -> float:
    
    # Get the latency
    latencies = []
    for _ in range(5):
        try:
            # Measure the latency
            latency = ping(monitor_host.split(':')[0], timeout=0.1, unit='ms')
            latencies.append(latency)
        except Exception as e:
            # If the request fails, append None
            latencies.append(None)
    
    # If any request fails, set the latency to -1
    if any(latency == None for latency in latencies):
        latency = -1
    else:
        # Calculate the average latency
        latency = sum(latencies) / len(latencies)
    
    # Store the latency in Redis
    await write_to_redis(redis,
                          "network_latency",
                          monitor_host,
                          None,
                          latency,
                          window_size
                        )

async def scraper_loop(monitor_dicts: Dict[str,List[str]], interval: int, window_size: int) -> None:
    
    # Create a session
    async with aiohttp.ClientSession() as session:
        
        # Loop forever
        while True:
            
            # Get the current time
            start_time = perf_counter()
            
            # Fetch metrics for each endpoint
            scrape_tasks = [scrape_container_metrics(monitor_host, container_names, window_size, session) for monitor_host, container_names in monitor_dicts.items()]
            scrape_tasks.extend([get_network_latency(monitor_host, window_size) for monitor_host in monitor_dicts.keys()])
            await asyncio.gather(*scrape_tasks)
            
            # Publish redis message
            await redis.publish("dashboard_metrics", "uploaded")
            
            # Wait for the next interval
            remaining_time = interval - (perf_counter() - start_time)
            if remaining_time > 0:
                await asyncio.sleep(remaining_time)

# Connect to Redis
redis = AsyncRedis.from_url(url=f"redis://{os.environ.get("HOST")}:{os.environ.get("DB_PORT")}", decode_responses=True)

# Clear the Redis database
redis.flushdb()

# Run the scraper
asyncio.run(
    scraper_loop(
        json.loads(os.environ.get("ENDPOINTS")),
        int(os.environ.get("INTERVAL")),
        int(os.environ.get("WINDOW_SIZE"))
    )
)