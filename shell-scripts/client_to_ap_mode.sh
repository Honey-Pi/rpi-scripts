[ -z $BASH ] && { exec bash "$0" "$@" || exit; }
#!/bin/bash

# Start AP

echo '>>> Fetch current wifi channel'
CHANNEL=`iwlist wlan0 channel | grep Current | sed 's/.*Channel \([0-9]*\).*/\1/g'`
if [ -z "$CHANNEL" ]; then
   echo "Info: Currently not connected to wlan0."
   CHANNEL="1"
else
    echo "Info: wlan0 is connected to channel $CHANNEL."
fi
# prevent using 5Ghz (uap0: IEEE 802.11 Hardware does not support configured channel)
#HWMODE=g 2,4GHz
#HWMODE=a 5 GHz
if [ "$CHANNEL" -gt "13" ]; then
   echo "Info: A 5GHz (Channel $CHANNEL) WiFi is connected but AP will select 2,4GHz (Channel 1)."
   HWMODE="g"
   CHANNEL="1"
else
   echo "Info: Select 2,4GHz (Channel $CHANNEL) for AP."
   HWMODE="g"
fi
export CHANNEL && export HWMODE

echo '>>> Save channel to /etc/hostapd/hostapd.conf'
cat /etc/hostapd/hostapd.conf.tmpl | envsubst > /etc/hostapd/hostapd.conf
systemctl daemon-reload # not sure if this is required but makes sense because hostapd.conf has been changed

echo '>>> Stopping hostapd'
(systemctl stop hostapd.service || (systemctl unmask hostapd && systemctl stop hostapd)) # if stop fails because service is masked => unmask

echo '>>> Restarting dnsmasq'
systemctl restart dnsmasq

#unblock wlan interface
#nmcli radio wifi off
rfkill unblock wlan

echo '>>> Create the virtual device uap0'
/sbin/iw dev wlan0 interface add uap0 type __ap
ip link set uap0 up
ip addr add 192.168.4.1/24 broadcast 192.168.4.255 dev uap0 #dhcpcd not working as interface is created later

echo '>>> Enable routing'
sysctl net.ipv4.ip_forward=1
# NAT
iptables -t nat -A POSTROUTING -j MASQUERADE
ip link set wlan0 up

sleep 2 && echo '>>> Starting hostapd'
# try it multiple times for raspberry zero
(systemctl start hostapd.service || (sleep 5 && echo ">>> Starting hostapd 2" && systemctl start hostapd.service) || (sleep 5 && echo ">>> Starting hostapd 3" && systemctl start hostapd.service) || (sleep 5 && echo ">>> Starting hostapd 4" && hostapd /etc/hostapd/hostapd.conf))
# wait for hostapd to crash dhcpcd and restart it

sleep 2 && echo '>>> Restarting dhcpcd'
systemctl restart dhcpcd

sleep 2 && echo '>>> Restarting dhcpcd 2'
systemctl restart dhcpcd
