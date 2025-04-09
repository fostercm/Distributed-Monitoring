from redis import Redis
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import numpy as np
import os
import json

# Define helper functions
def get_data(host: str, container: str, metric: str) -> list:
    # Fetch data from Redis
    data = r.lrange(f"metric:{metric}:host:{host}:container:{container}", 0, -1)
    return [float(i) if float(i) != -1 else np.nan for i in data]

def get_latency(host: str) -> float:
    # Fetch latency from Redis
    latency = r.lrange(f"metric:network_latency:host:{host}", 0, -1)
    return [float(i) if float(i) != -1 else np.nan for i in latency]

def get_status(host: str, container: str) -> bool:
    # Fetch status from Redis
    status = r.lrange(f"metric:cpu_absolute_usage:host:{host}:container:{container}", -1, -1)[0]
    return status != "-1"

def remove_port(host: str) -> str:
    # Remove the port from the host
    if ":" in host:
        return host.split(":")[0]
    return host

# Get environment variables
db_port = os.environ.get("DB_PORT")
host = os.environ.get("HOST")
endpoints = json.loads(os.environ.get("ENDPOINTS"))
window_size = int(os.environ.get("WINDOW_SIZE"))
interval = int(os.environ.get("INTERVAL"))

# Connect to Redis
r = Redis.from_url(url=f"redis://{host}:{db_port}", decode_responses=True)
pubsub = r.pubsub()
pubsub.subscribe("dashboard_metrics")

# Streamlit UI
st.title("Metrics Dashboard")

# Choose a container
st.sidebar.header("Select a Container")
available_containers = [f"{remove_port(host)}/{container}" for host, containers in endpoints.items() for container in containers]
selected_containers = st.sidebar.multiselect("Containers:", available_containers, default=available_containers)

# Choose a server
st.sidebar.header("Select a Host")
available_hosts = [remove_port(host) for host in endpoints.keys()]
selected_hosts = st.sidebar.multiselect("Hosts:", available_hosts, default=available_hosts)

# Display container status
st.sidebar.header("Container Status")

# Live updating
status_placeholder = st.sidebar.empty()
chart_placeholder = st.empty()
fig, ax = plt.subplots(5,2, figsize=(15, 30))

# Define the metrics to be displayed
metrics = [
    ("cpu_absolute_usage", "CPU Absolute Usage", "CPU Usage (ms)"),
    ("cpu_percent_usage", "CPU Percent Usage", "CPU Usage (%)"),
    ("memory_absolute_usage", "Memory Absolute Usage", "Memory Usage (MB)"),
    ("memory_percent_usage", "Memory Percent Usage", "Memory Usage (%)"),
    ("network_input", "Network Input", "Network Input (MB)"),
    ("network_output", "Network Output", "Network Output (MB)"),
    ("disk_read", "Disk Read", "Disk Read (MB)"),
    ("disk_write", "Disk Write", "Disk Write (MB)")
]

# Metrics update loop
while True:
    
    # Initialize variables
    prev_status = None
    
    # Listen for go-ahead signal from Redis
    for message in pubsub.listen():
        if message['type'] == 'message':
    
            # Update the status
            # container_status = {(host, container) : get_status(host, container) for host, containers in endpoints.items() for container in containers}
            container_status = {container : get_status(*container.split("/")) for container in selected_containers}
            
            # Check if the status has changed
            if prev_status != container_status:
                status_placeholder.empty()
                status_content = ""
                for container, status in container_status.items():
                    color = "green" if status else "red"
                    status_content += f"<b style='color:{color};'>{container} is {'Active' if status else 'Inactive'}</b><br>"
                status_placeholder.markdown(status_content, unsafe_allow_html=True)
            
            # Store the previous status
            prev_status = container_status
            
            # Update the latency
            for host in selected_hosts:
                # Fetch latency data
                latency = get_latency(host)
                ax[0][1].clear()
                ax[0][1].plot(latency, marker="o", linestyle="-", label=host)
            
            # Update plot
            ax[0][1].set_title("Network Latency")
            ax[0][1].set_ylabel("Latency (ms)")
            ax[0][1].legend(loc="upper right")
            ax[0][1].set_xticks([])
            
            # Update the other metrics
            for i,(metric,title,ylabel) in enumerate(metrics):
            
                # Get new data
                df = pd.DataFrame()
                for container in container_status.keys():
    
                    # Fetch data from Redis
                    data = get_data(*container.split("/"), metric)
                    
                    # Place the data in the DataFrame
                    df[f"{container}"] = data
                
                # Plot the relevant data
                x, y = i//2, i%2
                x += 1
                ax[x][y].clear()
                for container in selected_containers:
                    if container in df.columns:
                        # Plot the data
                        ax[x][y].plot(df[container], marker="o", linestyle="-", label=container)
                
                ax[x][y].set_title(title)
                ax[x][y].set_xticks([])
                ax[x][y].set_ylabel(ylabel)
                
                if i == 0:
                    handles, labels = ax[x][y].get_legend_handles_labels()
                    ax[0][0].legend(handles, [f"Host: {split[0]}    Container: {split[1]}" for split in [label.split("/") for label in labels]], loc="center", bbox_to_anchor=(0.5, 0.5), fontsize="large")
                    ax[0][0].axis("off")
                    
            # Plot the data
            chart_placeholder.pyplot(fig)