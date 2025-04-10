#!bin/bash

cd ../containers/endpoint
docker build -t endpoint .
docker run --name endpoint$1 -p $1:8000 endpoint
cd ../../scripts