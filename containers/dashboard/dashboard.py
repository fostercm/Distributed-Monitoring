from redis import Redis
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import numpy as np
import os
import time

# Define helper functions
def get_data(host: str, container: str, metric: str) -> list:
    # Fetch data from Redis
    data = r.lrange(f"metric:{metric}:host:{host}:container:{container}", 0, -1)
    return [float(i) if float(i) != -1 else np.nan for i in data]

def get_status(host: str, container: str) -> bool:
    # Fetch status from Redis
    status = r.lrange(f"metric:cpu_absolute_usage:host:{host}:container:{container}", 0, 1)
    return status != "-1"

# Get environment variables
# db_host = os.environ.get("DB_HOST")
# db_port = os.environ.get("DB_PORT")
# hosts = os.environ.get("SCRAPER_ENDPOINTS").split(",")
# window_size = int(os.environ.get("DASHBOARD_WINDOW_SIZE"))
# interval = int(os.environ.get("DASHBOARD_INTERVAL"))

db_host = "localhost"
db_port = 6379
hosts = {
    "localhost:8080" : ['endpoint8001', 'endpoint8002'],
}
window_size = 10

# Connect to Redis
r = Redis(host=db_host, port=db_port, decode_responses=True)
pubsub = r.pubsub()
pubsub.subscribe("dashboard_metrics")

# Streamlit UI
st.title("Metrics Dashboard")
st.sidebar.header("Select a Container")

# Choose a container
available_containers = [f"{host}/{container}" for host, containers in hosts.items() for container in containers]
selected_containers = st.sidebar.multiselect("Containers:", available_containers, default=available_containers)

# Live updating
status_placeholder = st.sidebar.empty()
chart_placeholder = st.empty()
fig, ax = plt.subplots(4,2, figsize=(15, 10))

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
    
    # Listen for go-ahead signal from Redis
    for message in pubsub.listen():
        if message['type'] == 'message':
    
            # Update the status
            status_placeholder.empty()
            container_status = {(host, container) : get_status(host, container) for host, containers in hosts.items() for container in containers}
            status_content = ""
            for (host, container), status in container_status.items():
                color = "green" if status else "red"
                status_content += f"<b style='color:{color};'>{host}/{container} is {'Active' if status else 'Inactive'}</b><br>"
            status_placeholder.markdown(status_content, unsafe_allow_html=True)
            
            # Update the metrics
            for i,(metric,title,ylabel) in enumerate(metrics):
            
                # Get new data
                df = pd.DataFrame()
                for (host, container) in container_status.keys():
    
                    # Fetch data from Redis
                    data = get_data(host, container, metric)
                    
                    # Place the data in the DataFrame
                    df[f"{host}/{container}"] = data
                
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