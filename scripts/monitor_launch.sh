#!bin/bash

cd ../containers/monitor/$1
docker build -t $1_monitor .
docker run --name $1_monitor -p $2:8000 $1_monitor
cd ../../scripts