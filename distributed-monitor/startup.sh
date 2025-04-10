#!bin/bash

# Run the python setup script to configure the environment
python3 environment_setup.py $1

# Launch the docker container
docker-compose up -d

# Delete the .env file
rm .env