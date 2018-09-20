#!/bin/bash

rsync -a --verbose ../Acquire function/lib/ --exclude '__pycache__'

docker build -t chryswoods/acquire-base:latest .
docker push chryswoods/acquire-base:latest

#docker run --rm -it chryswoods/acquire-base:latest
