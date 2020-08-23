
FROM nvidia/cuda:10.0-cudnn7-devel-ubuntu16.04
LABEL maintainer="carloscastillomvc@gmail.com"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        g++ \
        make \
        automake \
        autoconf \
        bzip2 \
        unzip \
        wget \
        sox \
        libtool \
        git \
        subversion \
        python2.7 \
        python3 \
        zlib1g-dev \
        gfortran \
        ca-certificates \
        patch \
        ffmpeg \
	vim && \
    rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python2.7 /usr/bin/python 

RUN git clone --depth 1 https://github.com/CarlosRCS9/kaldi.git /opt/kaldi && \
    cd /opt/kaldi && \
    cd /opt/kaldi/tools && \
    ./extras/install_mkl.sh && \
    make -j $(nproc) && \
    cd /opt/kaldi/src && \
    ./configure --shared --use-cuda && \
    make depend -j $(nproc) && \
    make -j $(nproc)

RUN apt-get install -y python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install torch

WORKDIR /opt/kaldi/
