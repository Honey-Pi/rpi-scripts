[ -z $BASH ] && { exec bash "$0" "$@" || exit; }
#!/bin/bash

# Stop AP Services

#ifconfig wlan0 down
systemctl stop hostapd.service
ifconfig uap0 down
iw dev uap0 del
iptables -D POSTROUTING -t nat -j MASQUERADE
sysctl net.ipv4.ip_forward=0
systemctl stop dnsmasq.service
#ifconfig wlan0 up
