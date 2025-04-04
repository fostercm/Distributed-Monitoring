import aiohttp
import asyncio
import os
from time import perf_counter
from typing import List, Dict
from redis.asyncio import Redis as AsyncRedis
from itertools import product

async def write_to_redis(redis: AsyncRedis, metric: str, host: str, container_name: str, value: str, window_size: int) -> None:
    
    # Store the metric in Redis
    await redis.rpush(f"metric:{metric}:host:{host}:container:{container_name}", value)
    
    # Keep only the recent values
    if await redis.llen(f"metric:{metric}:host:{host}:container:{container_name}") > window_size:
        await redis.lpop(f"metric:{metric}:host:{host}:container:{container_name}")

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

async def scraper_loop(montor_dicts: Dict[str,List[str]], interval: int, window_size: int) -> None:
    
    # Create a session
    async with aiohttp.ClientSession() as session:
        
        # Loop forever
        while True:
            
            # Get the current time
            start_time = perf_counter()
            
            # Fetch metrics for each endpoint
            scrape_tasks = [scrape_container_metrics(monitor_host, container_names, window_size, session) for monitor_host, container_names in montor_dicts.items()]
            await asyncio.gather(*scrape_tasks)
            
            # Publish redis message
            await redis.publish("dashboard_metrics", "uploaded")
            
            # Wait for the next interval
            remaining_time = interval - (perf_counter() - start_time)
            if remaining_time > 0:
                await asyncio.sleep(remaining_time)

# Connect to Redis
# redis = AsyncRedis(url=f"redis://{os.environ.get("DB_HOST")}:{os.environ.get("DB_PORT")} decode_responses=True)
redis = AsyncRedis.from_url(url="redis://localhost:6379", decode_responses=True)

# Run the scraper
# asyncio.run(
#     scraper_loop(
#         os.environ.get("SCRAPER_ENDPOINTS").split(","),
#         int(os.environ.get("SCRAPER_INTERVAL")),
#         int(os.environ.get("SCRAPER_WINDOW_SIZE"))
#     )
# )

asyncio.run(
    scraper_loop(
        {
            "localhost:8080": ["endpoint8001", "endpoint8002"],
        },
        5,
        10
    )
)