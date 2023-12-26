[ -z $BASH ] && { exec bash "$0" "$@" || exit; }
#!/bin/bash

# Stop AP

systemctl stop hostapd.service
echo 'Stopping AP: Remove the virtual device uap0'
ip link set uap0 down
iw dev uap0 del
iptables -D POSTROUTING -t nat -j MASQUERADE
echo 'Stopping AP: Stop routing'
sysctl net.ipv4.ip_forward=0 --quiet
systemctl stop dnsmasq.service

# Additional stuff
echo "Disabling Power Save Mode for WiFi (important for some Raspberry 3 models)"
iw wlan0 set power_save off
