#! /usr/bin/env bash

# Compile x_hook
gcc ./lib/cpp/x11_hook.cpp -lstdc++ -lX11 -lXext -lXi -o x11_hook.out