#!bin/bash

cd containers/endpoint
docker build -t endpoint .
docker run -p $1:8000 endpoint
cd ../..