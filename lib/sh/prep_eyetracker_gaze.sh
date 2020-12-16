#! /usr/bin/env bash

# Builds the eyetracker_gaze shared object file and starts the eyetracker
# service iff needed.


# Build the .so file
LD_LIBRARY_PATH=/usr/lib/tobii/:$LD_LIBRARY_PATH

gcc  -c -fPIC /opt/app/src/lib/cpp/eyetracker_gaze.cpp  \
    -o eyetracker_gaze.o        \
    -I/usr/include/python3.6m   \
    -lpython3.6m

gcc -shared  \
    -o /opt/app/src/lib/so/eyetracker_gaze.so eyetracker_gaze.o  \
    -lstdc++        \
    -lX11           \
    -lyaml-cpp      \
    -lboost_chrono  \
    -lboost_system  \
    -lboost_thread  \
    -pthread /usr/lib/tobii/libtobii_stream_engine.so  \
    -Wl,-rpath=/usr/lib/tobii/  \

rm eyetracker_gaze.o

# Start the eyetracker runtime service iff not already running
STATUS="$(systemctl is-active tobii-runtime-IS4LARGE107)"

if [ "${STATUS}" != "active" ]; then
    /opt/app/dependencies/tobii_pdk_install/platform_runtime/platform_runtime_IS4LARGE107_install.sh --install
fi
