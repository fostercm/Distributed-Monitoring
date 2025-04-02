import yaml
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

# Validate the database configuration
if "Database" not in config:
    errors.append("Error: 'Database' field not found in the configuration file")
    
else:
    
    # Validate fields in the database configuration
    database = config["Database"]
    validate_field(database, "Host", str, errors)
    validate_field(database, "Port", int, errors)
    
# Validate the scraper configuration
if "Scraper" not in config:
    errors.append("Error: 'Scraper' field not found in the configuration file")
    
else:
    
    # Validate fields in the scraper configuration
    scraper = config["Scraper"]
    validate_field(scraper, "Host", str, errors)
    validate_field(scraper, "Endpoints", list, errors)
    for field in ["Interval", "Port", "Window Size"]:
        validate_field(scraper, field, int, errors)
    
    # Validate individual endpoints
    if "Endpoints" in scraper:
        for endpoint in scraper["Endpoints"]:
            if not isinstance(endpoint, str):
                errors.append("Error: Invalid endpoint configuration, requires a list of strings")
                break

# Exit if errors are found
if errors:
    for error in errors:
        print(error)
    exit(1)

# If no errors are found, write the configuration to a .env file
with open(".env", "w") as f:
    f.write(f"DB_HOST={database['Host']}\n")
    f.write(f"DB_PORT={database['Port']}\n")
    f.write(f"SCRAPER_INTERVAL={scraper['Interval']}\n")
    f.write(f"SCRAPER_ENDPOINTS={','.join(scraper['Endpoints'])}\n")
    f.write(f"SCRAPER_PORT={scraper['Port']}\n")
    f.write(f"SCRAPER_HOST={scraper['Host']}\n")
    f.write(f"SCRAPER_WINDOW_SIZE={scraper['Window Size']}\n")