FROM ubuntu:20.04

# Build the image as root user
USER root

# Run some bash commands to install packages
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get -qq -y update && \
    apt-get -qq -y upgrade && \
    apt-get -qq -y install gcc g++ gfortran && \
    apt-get -qq -y install \
                    make automake autoconf libtool cmake rsync \ 
                    git wget tar zlib1g-dev&& \
    apt-get -qq -y install python python-dev && \
    apt-get -qq -y autoclean && \
    apt-get -qq -y autoremove && \
    rm -rf /var/lib/apt-get/lists/*

RUN wget https://herwig.hepforge.org/downloads/herwig-bootstrap && \
    chmod +x herwig-bootstrap && \
    ./herwig-bootstrap /herwig -j32

# Set the default directory
WORKDIR /generation/docker/
