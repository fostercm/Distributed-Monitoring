import docker
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List

# This script provides an API to fetch container metrics using Docker's API.
app = FastAPI()

# Initialize Docker client
client = docker.from_env()

# Define the data model for container metrics
class ContainerMetrics(BaseModel):
    cpu_absolute_usage: float
    cpu_percent_usage: float
    
    memory_absolute_usage: float
    memory_percent_usage: float
    
    network_input: float
    network_output: float
    
    disk_read: float
    disk_write: float

# Define metrics extraction functions
def get_network_io(stats: dict) -> dict:
    """Extract network I/O (MB, MB) from container stats."""
    net_io = stats['networks']
    net_input = sum(interface['rx_bytes'] for interface in net_io.values())
    net_output = sum(interface['tx_bytes'] for interface in net_io.values())
    return {'network_input': net_input, 'network_output': net_output}

def get_disk_io(stats: dict) -> dict:
    """Extract disk I/O (MB, MB) from container stats."""
    block_io = stats['blkio_stats']['io_service_bytes_recursive']
    disk_read = sum(io['value'] for io in block_io if io['op'] == 'Read')
    disk_write = sum(io['value'] for io in block_io if io['op'] == 'Write')
    return {'disk_read': disk_read / 1e6, 'disk_write': disk_write / 1e6}

def get_cpu_stats(stats: dict) -> dict:
    """Extract CPU stats (ns, %) from container stats."""
    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
    system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
    cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
    return {'cpu_absolute_usage': cpu_delta / 1e6, 'cpu_percent_usage': cpu_percent}

def get_memory_stats(stats: dict) -> dict:
    """Extract memory stats (MB, %) from container stats."""
    memory = stats['memory_stats']['usage']
    limit = stats['memory_stats']['limit']
    memory_percent = (memory / limit) * 100
    return {'memory_absolute_usage': memory / 1e6, 'memory_percent_usage': memory_percent}

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Container Metrics API"}
    
# Define the API endpoint to fetch metrics for a specific container
@app.get("/metrics")
async def get_metrics(container_names: List[str] = Query(...)):
    """Fetch metrics for a specific container."""

    overall_metrics = {}
    
    # Validate container names
    for container_name in container_names:
        
        # Check if the container exists
        try:
            container = client.containers.get(container_name)
        except docker.errors.NotFound:
            return {"error": f"Container {container_name} not found"}
        
        # Get container stats
        stats = container.stats(stream=False)

        # Extract metrics
        network_io = get_network_io(stats)
        disk_io = get_disk_io(stats)
        cpu_stats = get_cpu_stats(stats)
        memory_stats = get_memory_stats(stats)
        
        # Combine metrics into a single dictionary
        overall_metrics[container_name] = {
            **cpu_stats,
            **memory_stats
            **network_io,
            **disk_io,
        }
    
    return overall_metrics