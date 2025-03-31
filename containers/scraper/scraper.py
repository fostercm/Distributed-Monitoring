import aiohttp
import asyncio
import os
from time import perf_counter
import requests

async def get_metrics(endpoint: str, session: aiohttp.ClientSession) -> dict:
    
    # Start the timer
    start_time = perf_counter()
    
    try:
        # Make the request
        async with session.get(endpoint) as response:
            response = await response.json()
    except:
        # Return the endpoint and status
        return {
            "endpoint": endpoint,
            "status": False
        }
    
    # End the timer
    end_time = perf_counter()
    
    # Add the endpoint, latency, and status to the response
    response["endpoint"] = endpoint
    response["latency"] = end_time - start_time
    response["status"] = True
    
    # Return the response
    return response

async def update_metrics(database: dict, metrics: list) -> None:
    print("Updating metrics")

async def update_endpoints(database: dict, endpoints: list) -> None:
    print("Updating endpoints")

async def fetch_metrics(endpoints: list, interval: int):
    
    # Create a session
    async with aiohttp.ClientSession() as session:
        
        # Loop forever
        while True:
            
            # Fetch metrics for each endpoint
            tasks = [get_metrics(endpoint, session) for endpoint in endpoints]
            results = await asyncio.gather(*tasks)
            
            for i,result in enumerate(results):
                print(endpoints[i], result)
            
            # Wait for the next interval
            await asyncio.sleep(interval)

# Run the scraper
asyncio.run(
    fetch_metrics(
        os.environ.get("SCRAPER_ENDPOINTS").split(","),
        int(os.environ.get("SCRAPER_INTERVAL"))
    )
)