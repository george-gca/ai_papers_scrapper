# Created by: George Araújo (george.gcac@gmail.com)
# ==================================================================

# FROM python:latest
FROM python:3.10

ARG GROUPID=901
ARG GROUPNAME=scrapper
ARG USERID=901
ARG USERNAME=user

# Environment variables

RUN APT_INSTALL="apt-get install -y --no-install-recommends" && \
    PIP_INSTALL="pip --no-cache-dir install --upgrade" && \

# ==================================================================
# Create a system group with name deeplearning and id 901 to avoid
#    conflict with existing uids on the host system
# Create a system user with id 901 that belongs to group deeplearning
# ------------------------------------------------------------------

    groupadd -r $GROUPNAME -g $GROUPID && \
    # useradd -u $USERID -r -g $GROUPNAME $USERNAME && \
    useradd -u $USERID -m -g $GROUPNAME $USERNAME && \

# ==================================================================
# libraries via apt-get
# ------------------------------------------------------------------

    rm -rf /var/lib/apt/lists/* && \
    apt-get update && \

    DEBIAN_FRONTEND=noninteractive $APT_INSTALL \
        curl \
        wget && \

# ==================================================================
# python libraries via pip
# ------------------------------------------------------------------

    $PIP_INSTALL \
        pip \
        wheel && \
    $PIP_INSTALL \
        "numpy<2" \
        openreview-py \
        pandas \
        scrapy \
        tqdm && \

# ==================================================================
# config & cleanup
# ------------------------------------------------------------------

    ldconfig && \
    apt-get clean && \
    apt-get autoremove && \
    rm -rf /var/lib/apt/lists/* /tmp/* ~/*

USER $USERNAME

