FROM chryswoods/acquire-base:latest

# Need to be user root or Fn exits with
# {"message":"internal server error"}
USER root

ADD *.py $HOME/
RUN python3 -m compileall $HOME/*.py

ADD secret_key $HOME/

ENTRYPOINT ["python", "route.py"]
