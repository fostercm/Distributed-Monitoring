import aiohttp
import asyncio
import os
from time import perf_counter
from typing import List
from redis import Redis

async def get_metrics(host: str, session: aiohttp.ClientSession) -> dict:
    
    # Start the timer
    start_time = perf_counter()
    
    try:
        # Make the request
        async with session.get(f"http://{host}") as response:
            response = await response.json()
    except:
        # Return the host and status
        return {
            "host": host,
            "status": False
        }
    
    # End the timer
    end_time = perf_counter()
    
    # Add the host, latency, and status to the response
    response["host"] = host
    response["latency"] = end_time - start_time
    response["status"] = True
    
    # Return the response
    return response

def update_host_data(data: List[dict], window_size: int) -> None:
    
    for host_data in data:
        # Get the host
        host = host_data["host"]
        
        if not host_data["status"]:
            # If the host is down, set the status to False
            redis.set(f"status:host:{host}", 0)
        else:
            # If the host is up, set the status to True
            redis.set(f"status:host:{host}", 1)
        
        # Loop through each metric
        for metric in ['cpu_usage', 'memory_available', 'memory_used', 'disk_available', 'disk_used', 'latency']:
            
            # Store the metric in Redis
            redis.rpush(f"metric:{metric}:host:{host}", host_data[metric] if host_data["status"] else -1)
            
            # Keep only the recent values
            if redis.llen(f"metric:{metric}:host:{host}") > window_size:
                redis.lpop(f"metric:{metric}:host:{host}")

async def fetch_metrics(endpoints: list, interval: int):
    
    # Create a session
    async with aiohttp.ClientSession() as session:
        
        # Loop forever
        while True:
            
            # Get the current time
            start_time = perf_counter()
            
            # Fetch metrics for each endpoint
            fetch_tasks = [get_metrics(endpoint, session) for endpoint in endpoints]
            results = await asyncio.gather(*fetch_tasks)
            
            # Write the results to Redis
            update_host_data(results, int(os.environ.get("SCRAPER_WINDOW_SIZE")))
            
            # Wait for the next interval
            remaining_time = interval - (perf_counter() - start_time)
            if remaining_time > 0:
                await asyncio.sleep(remaining_time)

# Connect to Redis
redis = Redis(host=os.environ.get("DB_HOST"), port=os.environ.get("DB_PORT"), decode_responses=True)

# Run the scraper
asyncio.run(
    fetch_metrics(
        os.environ.get("SCRAPER_ENDPOINTS").split(","),
        int(os.environ.get("SCRAPER_INTERVAL"))
    )
)