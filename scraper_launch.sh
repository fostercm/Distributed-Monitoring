#!/bin/bash

cd containers/scraper
docker build -t scraper .
cd ../dashboard
docker build -t dashboard .
cd ../../test
source startup.sh config.yml
cd ..