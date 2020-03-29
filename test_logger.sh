#! /usr/bin/env bash

rm log_event_data.out

gcc ./lib/cpp/log_keys.cpp -lstdc++ \
    -lX11       \
    -lXext      \
    -lXi        \
    -lyaml-cpp  \
    -lsqlite3   \
    -o log_event_data.out

./log_event_data.out