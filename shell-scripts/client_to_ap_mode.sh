#!/bin/bash
echo '>>> Stopping hostapd.service'
(systemctl stop hostapd.service || (systemctl unmask hostapd && systemctl stop hostapd))& # if stop fails because service is masked => unmask

systemctl restart dnsmasq 
# Fetch current wifi channel
echo '>>> Fetch current wifi channel'
CHANNEL=`iwlist wlan0 channel | grep Current | sed 's/.*Channel \([0-9]*\).*/\1/g'`
# if no network connected
if [ -z "$CHANNEL" ]; then
   echo "Info: Currently not connected to a network."
   CHANNEL="1"
fi
# prevent using 5Ghz (uap0: IEEE 802.11 Hardware does not support configured channel)
#HWMODE=g 2,4GHz
#HWMODE=a 5 GHz
if [ "$CHANNEL" -gt "13" ]; then
   echo "Info: A 5GHz (Channel: $CHANNEL) WiFi is connected."
   #HWMODE="a"
   HWMODE="g"
   CHANNEL="1"
else
   echo "Info: Select 2,4GHz (Channel: $CHANNEL) for AccessPoint"
   HWMODE="g"
fi
export CHANNEL && export HWMODE
# Create the virtual device
echo '>>> Create the virtual device uap0'
cat /etc/hostapd/hostapd.conf.tmpl | envsubst > /etc/hostapd/hostapd.conf
#unblock wlan interface

#nmcli radio wifi off
rfkill unblock wlan

/sbin/iw dev wlan0 interface add uap0 type __ap
ip link set uap0 up
ip addr add 192.168.4.1/24 broadcast 192.168.4.255 dev uap0 #dhcpcd not working as interface is created later

sleep 1
echo '>>> Enable routing'
# Routing
sysctl net.ipv4.ip_forward=1
# NAT
iptables -t nat -A POSTROUTING -j MASQUERADE
ifconfig wlan0 up

echo '>>> Starting hostapd.service'
(systemctl start hostapd.service || (systemctl unmask hostapd && systemctl start hostapd))& # if start fails because service is masked => unmask
#wait for hostapd to crash dhcpcd and restart it
sleep 5
echo '>>> Restarting dhcpcd'
systemctl restart dhcpcd

