#!/bin/bash

cd containers/scraper
docker build -t metis-scraper .
cd ../../test
source startup.sh config.yml
cd ..