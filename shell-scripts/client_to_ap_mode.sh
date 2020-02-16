[ -z $BASH ] && { exec bash "$0" "$@" || exit; }
#!/bin/bash

ifdown wlan0
ip addr add 192.168.4.1/24 broadcast 192.168.4.255 dev uap0 #dhcpcd not working
ifup uap0
systemctl stop dnsmasq.service
(systemctl restart hostapd.service || (systemctl unmask hostapd && systemctl start hostapd))& # if restart fails because service is masked => unmask
ifup wlan0
systemctl start dnsmasq.service
