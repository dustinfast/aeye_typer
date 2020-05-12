#! /usr/bin/env bash

# A script for testing the on-screen eyetracker gaze marking cpp interface.
# Note: Passing any cmd line arg will cause resulting binary file to persist.

# Start eyetracker service iff needed
STATUS="$(systemctl is-active tobii-runtime-IS4LARGE107)"

if [ "${STATUS}" != "active" ]; then
    /opt/app/dependencies/tobii_pdk_install/platform_runtime/platform_runtime_IS4LARGE107_install.sh --install
fi

# Compile the eyetracker gazemark binary
LD_LIBRARY_PATH=/usr/lib/tobii/:/usr/include/cairo/:$LD_LIBRARY_PATH

gcc lib/cpp/eyetracker_gaze.cpp  \
    -o eye_tracker_gazemark.out \
    -lstdc++ -lX11 -lcairo \
    -lpthread -lboost_system  -lboost_thread  \
    -pthread /usr/lib/tobii/libtobii_stream_engine.so

# Run the test
./eye_tracker_gazemark.out

# Remove the binary if no cmd line arg
if [[ -z $1 ]]
then
    rm eye_tracker_gazemark.out
fi