import yaml
import json
import sys
import os

# Validate the config file
if len(sys.argv) != 2 or not isinstance(sys.argv[1], str) \
    or not os.path.exists(sys.argv[1]) \
    or os.path.splitext(sys.argv[1])[1] not in [".yml", ".yaml"]:
    print("Usage: metis <path>")
    print("Please provide a valid path to the configuration file (YAML)")
    exit(1)

# Read the configuration file
config_path = sys.argv[1]
with open(config_path, "r") as f:
        config = yaml.safe_load(f)

# Validate a config and field, store in errors list
def validate_field(config: dict, field: str, field_type: type, errors: list) -> None:
    if field not in config:
        errors.append(f"Error: '{field}' field not found in configuration")
    elif not isinstance(config[field], field_type):
        errors.append(f"Error: Invalid {config} configuration, requires a {field_type} for '{field}'")

# Store config errors
errors = []

# Validate the general configuration
if "General" not in config:
    errors.append("Error: 'General' field not found in the configuration file")
else:
    # Validate fields in the general configuration
    general = config["General"]
    validate_field(general, "Interval", int, errors)
    validate_field(general, "Window Size", int, errors)
    
    # Validate integer values
    for field in ["Interval", "Window Size"]:
        if field in general and general[field] < 1:
            errors.append(f"Error: '{field}' must be a positive integer")

# Validate the container configuration
if "Containers" not in config:
    errors.append("Error: 'Containers' field not found in the configuration file")

# Validate the port configuration
if "Ports" not in config:
    errors.append("Error: 'Ports' field not found in the configuration file")
else:
    # Validate fields in the port configuration
    port = config["Ports"]
    validate_field(port, "Database", int, errors)
    validate_field(port, "Dashboard", int, errors)

# Validate the host configuration
if "Host" not in config:
    errors.append("Error: 'Host' field not found in the configuration file")
        
# Exit if errors are found
if errors:
    for error in errors:
        print(error)
    exit(1)

# If no errors are found, write the configuration to a .env file
with open(".env", "w") as f:
    f.write(f"INTERVAL={general['Interval']}\n")
    f.write(f"WINDOW_SIZE={general['Window Size']}\n")
    f.write(f"ENDPOINTS={json.dumps(config['Containers'])}\n")
    f.write(f"DB_PORT={port['Database']}\n")
    f.write(f"DASHBOARD_PORT={port['Dashboard']}\n")
    f.write(f"HOST={config['Host']}\n")