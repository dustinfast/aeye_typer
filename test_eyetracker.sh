#! /usr/bin/env bash

# A script for testing the on-screen eyetracker gaze marking

# Start eyetracker service iff needed
STATUS="$(systemctl is-active tobii-runtime-IS4LARGE107)"

if [ "${STATUS}" != "active" ]; then
    /opt/app/dependencies/tobii_pdk_install/platform_runtime/platform_runtime_IS4LARGE107_install.sh --install
fi

# Compile the eyetracker gazemark binary
LD_LIBRARY_PATH=/usr/lib/tobii/:/usr/include/cairo/:$LD_LIBRARY_PATH

gcc lib/cpp/eyetracker_gaze.cpp  \
    -o eye_tracker_gazemark.out \
    -lstdc++ -lX11 -lcairo      \
    -pthread /usr/lib/tobii/libtobii_stream_engine.so

# Run the test
./eye_tracker_gazemark.out

# Remove the binary
rm eye_tracker_gazemark.out