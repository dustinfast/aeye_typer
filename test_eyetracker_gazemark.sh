#! /usr/bin/env bash

# A script for testing the on-screen eyetracker gaze marking

# Start eyetracker service
/opt/app/dependencies/tobii_pdk_install/platform_runtime/platform_runtime_IS4LARGE107_install.sh --install

# Compile the eyetracker conn test binary
LD_LIBRARY_PATH=/usr/lib/tobii/:$LD_LIBRARY_PATH

gcc lib/cpp/eyetracker_gazemark.cpp  \
    -o eye_tracker_gazemark.out \
    -lstdc++ -lX11 -lcairo      \
    -pthread /usr/lib/tobii/libtobii_stream_engine.so

# Run the test
./eye_tracker_gazemark.out

# Remove the binary
rm eye_tracker_gazemark.out