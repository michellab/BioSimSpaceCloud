#!/bin/bash

rsync -a --verbose ../../Acquire function/lib/ --exclude '__pycache__'

docker build -t chryswoods/acquire-access-base:latest .
docker push chryswoods/acquire-access-base:latest

#docker run --rm -it chryswoods/acquire-access-base:latest
