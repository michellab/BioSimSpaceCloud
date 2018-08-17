#!/bin/bash

rsync -a --verbose ../../Acquire function/lib/ --exclude '__pycache__'

docker build -t chryswoods/acquire-identity-base:latest .
docker push chryswoods/acquire-identity-base:latest

#docker run --rm -it chryswoods/acquire-identity-base:latest
