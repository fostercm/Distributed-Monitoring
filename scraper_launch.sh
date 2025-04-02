#!/bin/bash

cd containers/scraper
docker build -t scraper .
cd ../../test
source startup.sh config.yml
cd ..