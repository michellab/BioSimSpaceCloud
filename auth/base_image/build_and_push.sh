#!/bin/bash
docker build -t chryswoods/auth-login-base:latest .
docker push chryswoods/auth-login-base:latest

docker run --rm -it chryswoods/auth-login-base:latest

