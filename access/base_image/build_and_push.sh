#!/bin/bash

cp -a ../../Acquire function/lib/

docker build -t chryswoods/acquire-access-base:latest .
docker push chryswoods/acquire-access-base:latest

docker run --rm -it chryswoods/acquire-access-base:latest
