#!/usr/bin/env bash

# Targeted Linux distribution is Ubuntu Linux 16.04 LTS
# Tested on  Ubuntu 18.10 x86_64 with Cinnamon. Kernel  4.18.0-16-generic

LIB_DIR=./lib

echo "********************************************************************"
echo "*** Updating apt..."

apt update

echo "********************************************************************"
echo "***Installing 3rd party linux deps..."
export XDG_RUNTIME_DIR=/run/user/`id -u`
/etc/init.d/dbus start
apt install -y        \
    gconf2      	  \
    gconf-service	  \
    libnotify4	      \
    libnotify-bin     \
    libappindicator1  \
    libnss3	          \
    libxss1           \
    libuv0.10         \
    usbutils

echo "********************************************************************"
echo "*** Installing Stream engine..."
apt --fix-broken install -y   \
    libsqlcipher0                           

echo "********************************************************************"
echo "*** Installing Tobii USB Host / Connections Handler:"
export RUNLEVEL=1
printf "#!/bin/sh\nexit 0" > /usr/sbin/policy-rc.d
dpkg -i tobiiusbservice_l64U14_2.1.5-28fd4a.deb

echo "********************************************************************"
echo "*** Installing Tobii Engine daemon (recommended) that offers extended functionality"
dpkg -i tobii_engine_linux-0.1.6.193_rc-Linux.deb

echo "********************************************************************"
echo "*** Install Tobii Config (recommended) to do screen setup and calibration..."
dpkg -i tobii_config_0.1.6.111_amd64.deb

echo "********************************************************************"
echo "*** Extracting Stream Engine Client and T2T Dev Libs..."
if [[ ! -e "${LIB_DIR}" ]]; then
    mkdir -p ${LIB_DIR}/t2t
    tar -xzvf stream_engine_linux_3.0.4.6031.tar.gz -C ${LIB_DIR}
    # tar -xzvf t2t_64.tar.gz -C ${LIB_DIR}/t2t
else
    echo "${LIB_DIR} already exist. Continue..."
fi

mkdir /usr/lib/tobii
cp -pR ${LIB_DIR}/lib/x64/*.so /usr/lib/tobii/
cp ./tobii.conf /etc/ld.so.conf.d/

mkdir /usr/include/tobii
cp -R ${LIB_DIR}/include/tobii/* /usr/include/tobii

# mkdir /opt/t2t_64
# cp -R ${LIB_DIR}/t2t/* /opt/t2t_64

rm -rf ${LIB_DIR}

# echo "********************************************************************"
# echo "*** Installing Tobii eye tracker manager..."
# dpkg -i ./Tobii.Pro.Eye.Tracker.Manager.Linux-1.12.1.deb

echo "********************************************************************"
echo "*** Eye-tracker installation complete."