#! /usr/bin/env bash


# echo "Installing Tobii 4C eye-tracker..." 
# Note: This is done inside the container because systemd has to be up first.
# Install process adapted from https://github.com/Eitol/tobii_eye_tracker_linux_installer
cd docker/dependencies/tobii_eye_tracker_linux_installer
./install_all.sh 
cd ../../../

# echo "Compiling event logger..."
# gcc ./lib/cpp/log_keys.cpp -lstdc++ \
#     -lX11       \
#     -lXext      \
#     -lXi        \
#     -lyaml-cpp  \
#     -lsqlite3   \
#     -o log_event_data.out

# Compile use_xdo
# gcc ./lib/cpp/use_xdo.cpp -lxdo -o use_xdo.out