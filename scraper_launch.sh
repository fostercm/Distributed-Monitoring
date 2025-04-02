#!/bin/bash

cd containers/scraper/$1
docker build -t scraper .
cd ../../dashboard
docker build -t dashboard .
cd ../../test
source startup.sh config.yml
cd ..