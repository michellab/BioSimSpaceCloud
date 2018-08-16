#!/bin/bash

cp -a ../../Acquire function/lib

docker build -t chryswoods/acquire-accounting-base:latest .
docker push chryswoods/acquire-accounting-base:latest

docker run --rm -it chryswoods/acquire-accounting-base:latest
