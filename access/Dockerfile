FROM chryswoods/acquire-base:latest

ADD *.py $HOME/
RUN python3 -m compileall $HOME/*.py

ENTRYPOINT ["python", "route.py"]
