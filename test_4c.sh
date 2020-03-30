#! /usr/bin/env bash

gcc lib/cpp/4c_connect.cpp  \
    -o 4c_connect.out       \
    -pthread /usr/lib/tobii/libtobii_stream_engine.so