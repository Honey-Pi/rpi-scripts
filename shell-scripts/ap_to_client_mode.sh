[ -z $BASH ] && { exec bash "$0" "$@" || exit; }
#!/bin/bash

# Stop AP Services
ifdown uap0
systemctl stop hostapd.service
systemctl stop dnsmasq.service
ifup wlan0
