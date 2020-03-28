#! /usr/bin/env bash

# Compile x_hook
gcc ./lib/cpp/x11_hook.cpp -lstdc++ -lX11 -lXext -lXi -o x11_hook.out

# Compile use_xdo
gcc ./lib/cpp/use_xdo.cpp -lxdo -o use_xdo.out