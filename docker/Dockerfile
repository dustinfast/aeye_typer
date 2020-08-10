# The application's Dockerfile. 
# To build an image from it, run ./build.sh

FROM nvidia/cudagl:10.0-devel-ubuntu18.04

LABEL description="aeye_typer"
LABEL maintainer="Dustin Fast <dustin.fast@outlook.com>"

ENV CUDA_HOME=/usr/local/cuda
ENV CUDA_ROOT=$CUDA_HOME
ENV CUDA_TOOLKIT_ROOT_DIR=$CUDA_HOME
ENV PATH=$PATH:$CUDA_ROOT/bin:$HOME/bin
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CUDA_ROOT/lib64:/usr/local/cuda/extras/CUPTI/lib64/
ENV DEBIAN_FRONTEND=noninteractive

RUN echo "Updating apt-get..." && \
    apt-get update

RUN echo "Installing apt-utils..." && \
    apt-get install -y --no-install-recommends \
        apt-utils
RUN apt-get update

RUN echo "Installing 3rd party linux utils (apt-get)..." && \
    apt-get install -y --no-install-recommends \
        vim \
        git \
        curl \
        htop \
        wget \
        bzip2 \
        unzip \
        iotop \
        dos2unix \
        apt-file && apt-file update

RUN echo "Installing Python 3.6 (apt-get)..." && \
    apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get update
RUN apt-get install -y \
        python3-pip \
        python3.6-dev \
        python3.6 \
        python3-setuptools
RUN python3.6 -m pip install --upgrade pip

# TODO: RUN echo "Installing NVIDA components (apt-get)..." && \
    # apt-get install -y --no-install-recommends \
    # libcudnn7=7.6.4.38-1+cuda10.1  \
    # libcudnn7-dev=7.6.4.38-1+cuda10.1 \
    # libnvinfer6=6.0.1-1+cuda10.1 \
    # libnvinfer-dev=6.0.1-1+cuda10.1 \
    # libnvinfer-plugin6=6.0.1-1+cuda10.1\

RUN echo "Installing application dependencies (apt-get)..." && \
    apt-get install -y --no-install-recommends \
        gir1.2-wnck-3.0 \
        libboost-all-dev \
        python3-tk

RUN echo "Installing application dependencies(pip)..." && \
    python3.6 -m pip install \
        keras==2.3.1 \
        tensorflow-gpu==2.0.0 \
        tensorboardX \
        numpy \
        jupyter \
        pandas \
        pandas_profiling \
        sklearn \
        pyyaml \
        matplotlib \
        seaborn \
        sqlalchemy \
        cython \
        skl2onnx \
        pynput

RUN echo "Updating apt-get..." && \
    apt-get update 

RUN echo "Installing Tobii dependencies (apt-get)..." && \
    apt-get install -y --no-install-recommends \
        gconf2 \
        libnss3 \
        libxtst6 \
        libnotify4 \
        libasound2 \
        libxss-dev \
        default-jre \
        default-jdk \
        avahi-daemon \
        libappindicator1 \
        libcanberra-gtk3-module

RUN echo "Setting up workspace..."
# Make python3.6 the default python version
RUN ln -s -f /usr/bin/python3.6 /usr/bin/python
# Copy in custom .bashrc
COPY dependencies/.bashrc /root/.bashrc
# Create local codebase mount point
RUN mkdir -p /opt/app/src
RUN pwd

RUN echo "Settting up Tobii PDK..."
RUN mkdir -p /opt/app/dependencies/tobii_pdk_install
COPY dependencies/IS4LARGE107_UB16_x64_1.13.15_public.zip /opt/app/dependencies/tobii_pdk_install
WORKDIR /opt/app/dependencies/tobii_pdk_install
RUN unzip IS4LARGE107_UB16_x64_1.13.15_public.zip
RUN rm IS4LARGE107_UB16_x64_1.13.15_public.zip
WORKDIR /opt/app/dependencies/tobii_pdk_install/platform_runtime
RUN chmod 777 platform_runtime_IS4LARGE107_install.sh
WORKDIR /opt/app/dependencies/tobii_pdk_install/client_side/stream_engine
RUN mkdir /usr/lib/tobii
RUN cp -pR lib/x64/*.so /usr/lib/tobii/
RUN mkdir /usr/include/tobii
RUN cp -R include/tobii/* /usr/include/tobii

RUN echo "Settting up Tobii config..."
RUN mkdir -p /tmp/tobii_config
COPY dependencies/tobii_config_0.1.8_amd64.deb /tmp/tobii_config
WORKDIR /tmp/tobii_config
RUN dpkg -i tobii_config_0.1.8_amd64.deb
RUN rm -rf /tmp/tobii_config

RUN echo "Settting up Tobii manager..."
RUN mkdir -p /tmp/tobii_mgr
COPY dependencies/TobiiProEyeTrackerManager-2.1.0.deb /tmp/tobii_mgr
WORKDIR /tmp/tobii_mgr
RUN dpkg -i TobiiProEyeTrackerManager-2.1.0.deb
RUN rm -rf /tmp/tobii_mgr

RUN echo "Setting default working dir"
WORKDIR /opt/app/src

RUN echo "Setting up psuedo-systemd..."
ENV container docker
RUN (cd /lib/systemd/system/sysinit.target.wants/; \
    for i in ; \
    do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done)
RUN rm -rf /lib/systemd/system/multi-user.target.wants/
RUN rm -rf /etc/systemd/system/.wants/
RUN rm -rf /lib/systemd/system/local-fs.target.wants/
RUN rm -rf /lib/systemd/system/sockets.target.wants/udev
RUN rm -rf /lib/systemd/system/sockets.target.wants/initctl
RUN rm -rf /lib/systemd/system/basic.target.wants/
RUN rm -rf /lib/systemd/system/anaconda.target.wants/*
VOLUME [ “/sys/fs/cgroup” ]
CMD ["/sbin/init"]

