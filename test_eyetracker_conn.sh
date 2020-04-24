#! /usr/bin/env bash

# A script for testing the connection to the application's eyetracker

# Start eyetracker service
/opt/app/dependencies/tobii_pdk_install/platform_runtime/platform_runtime_IS4LARGE107_install.sh --install

# Compile the eyetracker conn test binary
LD_LIBRARY_PATH=/usr/lib/tobii/:$LD_LIBRARY_PATH

gcc lib/cpp/eyetracker_conntest.cpp  \
    -o test_eyetracker.out \
    -pthread /usr/lib/tobii/libtobii_stream_engine.so

# Run the test
./test_eyetracker.out

# Remove the binary
rm test_eyetracker.out