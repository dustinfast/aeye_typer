#! /usr/bin/env bash

rm test_logger.out

gcc ./lib/cpp/log_keys.cpp -lstdc++ \
    -lX11       \
    -lXext      \
    -lXi        \
    -lyaml-cpp  \
    -lsqlite3   \
    -o test_logger.out

./test_logger.out