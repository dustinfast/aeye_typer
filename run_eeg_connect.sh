#! /usr/bin/env bash

read -p "Ensure your EEG is turned off and press enter to continue"

eeg_mac_address=$(cat _config.yaml | grep -o 'DEVICE_ID_EEG:.*' | cut -f2- -d:)
echo "Connecting EEG with MAC address: $mac_address"

apt update &&
apt install -y bluetooth bluez bluez-tools rfkill libbluetooth-dev &&
echo "EnableGatt=true" >> /etc/bluetooth/main.conf

# Start for first time, then stop, then open new handler
/etc/init.d/bluetooth start
/etc/init.d/bluetooth stop
/usr/lib/bluetooth/bluetoothd -nEC --plugin=audio &

sleep 2

# Bring up bluetooth and connect to it
/opt/app/src/lib/sh/init_bluetooth.sh

