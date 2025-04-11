#!bin/bash

# Python scraper
cd ../containers/scraper/python
docker build -t python_scraper .

# Go scraper
cd ../go
CGO_ENABLED=0 go build -o scraper.bin
docker build -t go_scraper .

# Dashboard
cd ../../dashboard
docker build -t dashboard .

# Python endpoint
cd ../endpoint/python
docker build -t python_endpoint .

# Go endpoint
cd ../go
CGO_ENABLED=0 go build -o endpoint.bin
docker build -t go_endpoint .

# Python monitor
cd ../../monitor/python
docker build -t python_monitor .

# Go monitor
cd ../go
CGO_ENABLED=0 go build -o monitor.bin
docker build -t go_monitor .

# Return to the original directory
cd ../../../scripts