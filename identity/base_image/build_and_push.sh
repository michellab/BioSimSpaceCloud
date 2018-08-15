#!/bin/bash

cp -a ../../Acquire function/lib/

docker build -t chryswoods/identity-login-base:latest .
docker push chryswoods/identity-login-base:latest

docker run --rm -it chryswoods/identity-login-base:latest

