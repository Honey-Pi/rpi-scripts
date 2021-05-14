[ -z $BASH ] && { exec bash "$0" "$@" || exit; }
#!/bin/bash
# file: update.sh
#
# This script will install required software for HoneyPi after an upgrade.
# It is recommended to run it in your home directory.
#

# check if sudo is used
if [ "$(id -u)" != 0 ]; then
    echo 'Sorry, you need to run this script with sudo'
    exit 1
fi

VERSION="v1.3"

echo '>>> Running post-upgrade script...'

if cmp -s /etc/network/interfaces /home/pi/HoneyPi/rpi-scripts/$VERSION/etc/network/interfaces
then
   echo "The interfaces file is already the correct file..."
else
   echo "The interfaces file is different..."
   mv /etc/network/interfaces /etc/network/interfaces.orig
   cp /home/pi/HoneyPi/rpi-scripts/$VERSION/etc/network/interfaces /etc/network/interfaces

fi
if cmp -s /home/pi/HoneyPi/update.sh /home/pi/HoneyPi/rpi-scripts/$VERSION/home/pi/HoneyPi/update.sh
then
   echo "The update.sh file is already the correct file..."
else
   echo "The update.sh file is different..."
   mv /home/pi/HoneyPi/update.sh /home/pi/HoneyPi/update.sh.orig
   cp /home/pi/HoneyPi/rpi-scripts/$VERSION/home/pi/HoneyPi/update.sh /home/pi/HoneyPi/update.sh
   chmod a+x /home/pi/HoneyPi/update.sh

fi
if cmp -s /etc/dhcpcd.conf /home/pi/HoneyPi/rpi-scripts/$VERSION/home/pi/HoneyPi/overlays/dhcpcd.conf
then
   echo "The dhcpcd.conf file is already the correct file..."
else
   echo "The dhcpcd.conf file is different..."
   mv /etc/dhcpcd.conf /etc/dhcpcd.conf.orig
   cp /home/pi/HoneyPi/rpi-scripts/$VERSION/home/pi/HoneyPi/overlays/dhcpcd.conf /etc/dhcpcd.conf
fi
if cmp -s /etc/dnsmasq.conf /home/pi/HoneyPi/rpi-scripts/$VERSION/home/pi/HoneyPi/overlays/dnsmasq.conf
then
   echo "The dnsmasq.conf file is already the correct file..."
else
   echo "The dnsmasq.conf file is different..."
   mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
   cp /home/pi/HoneyPi/rpi-scripts/$VERSION/home/pi/HoneyPi/overlays/dnsmasq.conf /etc/dnsmasq.conf

fi
if cmp -s /etc/default/hostapd /home/pi/HoneyPi/rpi-scripts/$VERSION/home/pi/HoneyPi/overlays/hostapd
then
   echo "The hostapd default conf file is already the correct file..."
else
   echo "The hostapd default conf file is different..."
   mv /etc/default/hostapd /etc/default/hostapd.orig
   cp /home/pi/HoneyPi/rpi-scripts/$VERSION/home/pi/HoneyPi/overlays/hostapd /etc/default/hostapd
fi
if cmp -s /etc/hostapd/hostapd.conf.tmpl /home/pi/HoneyPi/rpi-scripts/$VERSION/home/pi/HoneyPi/overlays/hostapd.conf.tmpl
then
   echo "The hostapd.conf.tmpl default conf file is already the correct file..."
else
   echo "The hostapd.conf.tmpl default conf file is different..."
   mv /etc/hostapd/hostapd.conf.tmpl /etc/hostapd/hostapd.conf.tmpl.orig
   cp /home/pi/HoneyPi/rpi-scripts/$VERSION/home/pi/HoneyPi/overlays/hostapd.conf.tmpl /etc/hostapd/hostapd.conf.tmpl
fi


echo "postupdatefinished 1" >> /var/www/html/version.txt
