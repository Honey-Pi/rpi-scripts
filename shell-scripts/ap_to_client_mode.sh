[ -z $BASH ] && { exec bash "$0" "$@" || exit; }
#!/bin/bash

# Stop AP

systemctl stop hostapd.service
echo '>>> Remove the virtual device uap0'
ip link set uap0 down
iw dev uap0 del
iptables -D POSTROUTING -t nat -j MASQUERADE
echo '>>> Stop routing'
sysctl net.ipv4.ip_forward=0
systemctl stop dnsmasq.service
