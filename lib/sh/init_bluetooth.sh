#! /usr/bin/expect -f

# eeg_mac_address=$(cat _config.yaml | grep -o 'DEVICE_ID_EEG:.*' | cut -f2- -d:)
# echo "Using EEG with MAC address: $mac_address"

set prompt "#"
set mac_address "D0:1A:E7:BA:E3:BF"

set timeout 10

#####################################################################
# Do init
spawn bluetoothctl
expect -re $prompt

send "power on\r"
expect "Changing power on succeeded"

send "discoverable on\r"
expect "Changing discoverable on succeeded"

send "pairable on\r"
expect "Changing pairable on succeeded"

send_user "Turn on your EEG and press y to continue."
interact y return

send "exit\r"
expect eof


#####################################################################
# Do connect
spawn bluetoothctl
expect -re $prompt

send "scan on\r"
expect "\[NEW\] Device $mac_address"

send "connect $mac_address\r"
expect "Connection successful"

send "exit\r"
expect eof