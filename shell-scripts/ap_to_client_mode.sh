[ -z $BASH ] && { exec bash "$0" "$@" || exit; }
#!/bin/bash

# Stop AP Services
ifconfig uap0 down
systemctl stop hostapd.service
systemctl stop dnsmasq.service
ifconfig wlan0 up
