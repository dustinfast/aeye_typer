#! /usr/bin/env bash

# Compile x_hook
gcc ./lib/cpp/x_hook.cpp -lstdc++ -lX11 -lXext -lXi -o x_hooker.out