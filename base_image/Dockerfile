FROM python:3.7-slim-stretch
LABEL maintainer="Christopher Woods <Christopher.Woods@bristol.ac.uk>"

USER root

RUN apt-get update && \
    apt-get install --no-install-recommends -qy \ 
    build-essential \ 
    gcc \
    cmake \
    libgnutls28-dev \
    libcurl4-gnutls-dev \
    wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Configure environment
ENV SHELL=/bin/bash \
    FN_USER=fnuser \
    FN_UID=1000 \
    FN_GID=100

ENV HOME=/home/$FN_USER

ADD fix-permissions /usr/bin/fix-permissions

# Create fn user with UID=1000 and in the 'users' group
# and make sure these dirs are writable by the `users` group.
RUN useradd -m -s /bin/bash -N -u $FN_UID $FN_USER && \
    fix-permissions $HOME

WORKDIR $HOME

ADD requirements.txt $HOME
RUN pip3 install --no-cache --no-cache-dir -r requirements.txt
RUN rm -fr ~/.cache/pip /tmp* requirements.txt func.yaml Dockerfile .venv

# Copy in the updated version of oci's __init__.py that we
# have fixed to lazy load modules (thereby making it much quicker)
ADD fast_oci__init__.py /usr/local/lib/python3.7/site-packages/oci/__init__.py
ADD fast_oci_object_storage__init__.py /usr/local/lib/python3.7/site-packages/oci/object_storage/__init__.py
ADD fast_oci_object_storage_models__init__.py /usr/local/lib/python3.7/site-packages/oci/object_storage/models/__init__.py
ADD fast_oci__vendor__init__.py /usr/local/lib/python3.7/site-packages/oci/_vendor/__init__.py

RUN /usr/bin/fix-permissions $HOME

# Become the $FN_USER so that nothing runs as root
USER $FN_USER

# Add the function last as this is the thing that will change
# most often
ADD function/* $HOME/

# Now byte-compile everything
USER root
RUN python3 -m compileall Acquire/*

ENTRYPOINT ["bash"]

USER $FN_USER

