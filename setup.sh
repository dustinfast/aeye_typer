#! /usr/bin/env bash

# Compile x_hook
gcc ./lib/cpp/log_keys.cpp -lstdc++ -lX11 -lXext -lXi -lyaml-cpp -lsqlite3 -o log_keys.out

# Compile use_xdo
gcc ./lib/cpp/use_xdo.cpp -lxdo -o use_xdo.out