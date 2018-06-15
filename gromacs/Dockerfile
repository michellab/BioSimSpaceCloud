FROM python:3.6-slim-stretch
LABEL maintainer="Christopher Woods <Christopher.Woods@bristol.ac.uk>"

WORKDIR /function

RUN apt-get update && \
    apt-get install --no-install-recommends -qy \ 
    build-essential \ 
    gcc \
    cmake \
    wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
    
ADD requirements.txt /function/
RUN pip3 install --no-cache --no-cache-dir -r requirements.txt
RUN rm -fr ~/.cache/pip /tmp* requirements.txt func.yaml Dockerfile .venv

# Download gromacs source using wget
RUN wget ftp://ftp.gromacs.org/pub/gromacs/gromacs-2018.2.tar.gz

# Untar the file
RUN tar -zxvf gromacs-2018.2.tar.gz && \
    rm gromacs-2018.2.tar.gz

# Add the function last as this is the thing that will change
# most often
ADD function/* /function/

ENTRYPOINT ["python3", "func.py"]
