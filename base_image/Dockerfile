# Build and install dependencies into the build container
FROM fnproject/python:3.7-dev as build-stage

WORKDIR /function

# Install libraries needed by python dependencies
RUN apt-get update && \
    apt-get install --no-install-recommends -qy \
    build-essential \
    gcc \
    cmake \
    libgnutls28-dev \
    libcurl4-gnutls-dev \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ADD requirements.txt .

RUN pip3 install --target /python/ --no-cache --no-cache-dir \
                 -r requirements.txt && \
    rm -fr ~/.cache/pip /tmp* requirements.txt func.yaml Dockerfile .venv

# Now transfer what is needed to the production container
FROM fnproject/python:3.7

WORKDIR /function

COPY --from=build-stage /function /function
COPY --from=build-stage /python /python

ENV PYTHONPATH=/python

# Copy in the updated version of oci's __init__.py that we
# have fixed to lazy load modules (thereby making it much quicker)
#ADD fast_oci__init__.py /usr/local/lib/python3.7/site-packages/oci/__init__.py
#ADD fast_oci_object_storage__init__.py /usr/local/lib/python3.7/site-packages/oci/object_storage/__init__.py
#ADD fast_oci_object_storage_models__init__.py /usr/local/lib/python3.7/site-packages/oci/object_storage/models/__init__.py
#ADD fast_oci__vendor__init__.py /usr/local/lib/python3.7/site-packages/oci/_vendor/__init__.py

# Add the function last as this is the thing that will change
# most often
ADD Acquire /function

RUN python3 -m compileall /function/Acquire/*

ENTRYPOINT ["bash"]
