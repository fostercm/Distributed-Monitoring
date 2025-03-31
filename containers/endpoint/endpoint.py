from fastapi import FastAPI
from pydantic import BaseModel
import psutil
import os
import subprocess
import time

app = FastAPI()

class SystemMetrics(BaseModel):
    cpu_usage: float
    memory_available: float
    memory_used: float
    disk_available: float
    disk_used: float
    
    def __str__(self) -> str:
        return f"""
        CPU Usage: {self.cpu_usage}%
        Memory:
            Available: {self.memory_available} (GB)
            Used: {self.memory_used} (GB)
        Disk:
            Available: {self.disk_available} (GB)
            Used: {self.disk_used} (GB)
        """

def is_container():
    """Check if the process is running inside a Docker container."""
    return os.path.exists("/.dockerenv")

def get_cpu_usage():
    with open("/proc/stat", "r") as f:
        cpu_data = f.readline().split()
        cpu_times = list(map(int, cpu_data[1:]))  # Extract the CPU times (user, nice, system, idle, etc.)

    # Sleep for 1 second to get usage over time
    time.sleep(1)

    with open("/proc/stat", "r") as f:
        cpu_data = f.readline().split()
        new_cpu_times = list(map(int, cpu_data[1:]))

    # Calculate the difference in CPU times
    diff_times = [new - old for new, old in zip(new_cpu_times, cpu_times)]
    total_time = sum(diff_times)
    idle_time = diff_times[3]

    cpu_usage = (1 - idle_time / total_time) * 100
    return cpu_usage

def get_memory_info():
    with open("/proc/meminfo", "r") as f:
        mem_info = {line.split(":")[0].strip(): int(line.split(":")[1].strip().split()[0]) for line in f.readlines()}

    total_memory = mem_info.get("MemTotal", 0)
    free_memory = mem_info.get("MemFree", 0)
    available_memory = mem_info.get("MemAvailable", 0)

    memory_usage = total_memory - free_memory
    memory_percent = (memory_usage / total_memory) * 100

    return {
        "total": total_memory,
        "free": free_memory,
        "available": available_memory,
        "usage": memory_usage,
        "percent": memory_percent
    }

def get_disk_usage():
    result = subprocess.run(['df', '/'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception("Error running df command")
    
    output = result.stdout.decode('utf-8').splitlines()[1]
    total, used, available, percent = output.split()[1:5]
    total, used, available, percent = int(total), int(used), int(available), int(percent[:-1])
    
    return {
        "total": total,
        "used": used,
        "available": available,
        "percent": percent
    }

@app.get("/metrics", response_model=SystemMetrics)
async def metrics():
    # Define scale factor to convert bytes to GB
    scale_factor = 2**30
    
    # Get system information
    if is_container():
        cpu_usage = get_cpu_usage()
        memory_info = get_memory_info()
        disk_info = get_disk_usage()
        
        memory_available = memory_info["available"]
        memory_used = memory_info["usage"]
        disk_available = disk_info["available"]
        disk_used = disk_info["used"]
        
    else:
        psutil.cpu_percent(interval=None)
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        memory_available = memory_info.available
        memory_used = memory_info.used
        disk_available = disk_info.free
        disk_used = disk_info.used
    
    return SystemMetrics(
        cpu_usage=cpu_usage,
        memory_available=memory_available / scale_factor,
        memory_used=memory_used / scale_factor,
        disk_available=disk_available / scale_factor,
        disk_used=disk_used / scale_factor,
    )