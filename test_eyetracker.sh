#! /usr/bin/env bash

rm test_eyetracker.out

gcc lib/cpp/4c_connect.cpp  \
    -o test_eyetracker.out       \
    -pthread /usr/lib/tobii/libtobii_stream_engine.so

./test_eyetracker.out