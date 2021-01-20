[ -z $BASH ] && { exec bash "$0" "$@" || exit; }
#!/bin/bash

ifconfig wlan0 down
ip addr add 192.168.4.1/24 broadcast 192.168.4.255 dev uap0 #dhcpcd not working
ifconfig uap0 up
systemctl stop dnsmasq.service
(systemctl restart hostapd.service || (systemctl unmask hostapd && systemctl start hostapd))& # if restart fails because service is masked => unmask
ifconfig wlan0 up
systemctl start dnsmasq.service
