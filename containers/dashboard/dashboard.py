from redis import Redis
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time

# Connect to Redis
r = Redis(host="localhost", port=6379, decode_responses=True)

def get_data(host, metric):
    # Check if the host is up
    if not get_status(host):
        return []

    # Fetch data from Redis
    data = r.lrange(f"metric:{metric}:host:{host}", 0, -1)
    if data:
        return [float(i) for i in data]
    else:
        return []

def get_status(host):
    # Check if the host is up
    status = r.get(f"status:host:{host}")
    if status == '1':
        return True
    else:
        return False

def remove_endpoint(host):
    return "/".join(host.split("/")[:-1])

hosts = ["172.24.1.57:8001/metrics",
         "172.24.1.57:8002/metrics",
         "172.24.1.57:8003/metrics"]
window_size = 10

# Streamlit UI
st.title("Metrics Dashboard")
st.sidebar.header("Select a Container")

# Choose a container
available_containers = [remove_endpoint(host) for host in hosts]
selected_containers = st.sidebar.multiselect("Containers:", available_containers, default=available_containers)

# Live updating
status_placeholder = st.sidebar.empty()
chart_placeholder = st.empty()
fig, ax = plt.subplots(2,2, figsize=(15, 10))

metrics = [
    ("cpu_usage", "CPU Usage", "CPU Usage (%)"),
    ("memory_used", "Memory Used", "Memory Used (GB)"),
    ("disk_used", "Disk Used", "Disk Used (GB)"),
    ("latency", "Latency", "Latency (ms)")
]

while True:
    
    # Update the status
    status_placeholder.empty()
    container_status = {container: get_status(container) for container in hosts}
    status_content = ""
    for container, status in container_status.items():
        color = "green" if status else "red"
        status_content += f"<b style='color:{color};'>{container} is {'Active' if status else 'Inactive'}</b><br>"
    status_placeholder.markdown(status_content, unsafe_allow_html=True)
    
    for i,(metric,title,ylabel) in enumerate(metrics):
    
        # Get new data
        df = pd.DataFrame()
        for host in hosts:
            # Fetch data from Redis
            data = get_data(host, metric)
            
            # Place the data in the DataFrame
            if len(data) == window_size:
                df[remove_endpoint(host)] = data
        
        # Plot the relevant data
        x, y = i//2, i%2
        ax[x][y].clear()
        for container in selected_containers:
            if container in df.columns:
                # Plot the data
                ax[x][y].plot(df[container], marker="o", linestyle="-", label=container)
        
        ax[x][y].set_title(title)
        ax[x][y].set_xticks([])
        ax[x][y].set_ylabel(ylabel)
        ax[x][y].legend()
            
    # Plot the data
    chart_placeholder.pyplot(fig)
    
    time.sleep(5)