#! /usr/bin/env bash

# A script for testing the on-screen eyetracker gaze marking cpp interface.
# Note: For dev convenience, passing any cmd line arg to this script will
# cause resulting binary file to persist. Else, it is removed on exit.

# Start eyetracker service iff needed
STATUS="$(systemctl is-active tobii-runtime-IS4LARGE107)"

if [ "${STATUS}" != "active" ]; then
    echo "Starting tobii service..."
    /opt/app/dependencies/tobii_pdk_install/platform_runtime/platform_runtime_IS4LARGE107_install.sh --install
fi

# Compile the eyetracker gazemark binary
LD_LIBRARY_PATH=/usr/lib/tobii/:$LD_LIBRARY_PATH

gcc lib/cpp/eyetracker_gaze.cpp  \
    -o eye_tracker_gazemark.out \
    -I/usr/include/python3.6m   \
    -lstdc++                    \
    -lX11                       \
    -lyaml-cpp                  \
    -lpython3.6m                \
    -lboost_system              \
    -lboost_thread              \
    -lpthread                   \
    -pthread /usr/lib/tobii/libtobii_stream_engine.so

# Run the test
./eye_tracker_gazemark.out

# Remove the binary if no cmd line arg
if [[ -z $1 ]]
then
    rm eye_tracker_gazemark.out
fi