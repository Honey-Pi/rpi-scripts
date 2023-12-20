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

VERSION="v1.3.9-alpha-10"

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

# changes after v1.3.4
if cmp -s /etc/lighttpd/lighttpd.conf /home/pi/HoneyPi/rpi-scripts/$VERSION/home/pi/HoneyPi/overlays/lighttpd.conf
then
   echo "The lighttpd.conf default conf file is already the correct file..."
else
   echo "The lighttpd.conf default conf file is different..."
   cp /home/pi/HoneyPi/rpi-scripts/$VERSION/home/pi/HoneyPi/overlays/lighttpd.conf /etc/lighttpd/lighttpd.conf
   service lighttpd force-reload
fi

apt-get -y update --allow-releaseinfo-change

echo "Install required modules after v1.3.4...for for dht..."
apt-get -y install --no-install-recommends libgpiod2
pip3 install adafruit-circuitpython-dht

echo "Install required modules after v1.3.7 used for oled display..."
pip3 install Pillow smbus2
apt-get -y install --no-install-recommends libopenjp2-7 libtiff5

echo "Install required modules after v1.3.7 used for ds18b20..."
pip3 install ds18b20

echo "Install required modules after v1.3.7 used for rak811..."
pip3 install rak811

echo "Install required modules after v1.3.7 used for WittyPi..."
pip3 install smbus2 pytz

echo "Install required modules after v1.3.7 used for PA1010D..."
pip3 install pynmea2 timezonefinder
#pip3 install --upgrade pa1010d

echo "Install required modules after v1.3.7...for for dht..."
apt-get -y install python3-psutil
echo "Finished installing modules"

echo "Install required modules after v1.3.9 used for rak811 & WittyPi..."
if grep -q 'dtoverlay=pi3-miniuart-bt' /boot/config.txt; then
  echo 'Seems setting Pi3/4 Bluetooth to use mini-UART is done already, skip this step.'
else
  echo 'dtoverlay=pi3-miniuart-bt' >> /boot/config.txt
fi
echo "Install required modules after v1.3.9 used for WittyPi..."
echo '>>> Enable I2C'
if grep -q 'i2c-bcm2708' /etc/modules; then
  echo 'Seems i2c-bcm2708 module already exists, skip this step.'
else
  echo 'i2c-bcm2708' >> /etc/modules
fi
if grep -q 'i2c-dev' /etc/modules; then
  echo 'Seems i2c-dev module already exists, skip this step.'
else
  echo 'i2c-dev' >> /etc/modules
fi
if grep -q 'dtparam=i2c1=on' /boot/config.txt; then
  echo 'Seems i2c1 parameter already set, skip this step.'
else
  echo 'dtparam=i2c1=on' >> /boot/config.txt
fi
if grep -q 'dtparam=i2c_arm=on' /boot/config.txt; then
  echo 'Seems i2c_arm parameter already set, skip this step.'
else
  echo 'dtparam=i2c_arm=on' >> /boot/config.txt
fi


# required since version v1.4
echo '>>> Uninstall old numpy pip package - v1.4'
pip3 uninstall numpy
echo '>>> Install new NumPy package (from debian) - v1.4'
apt-get -y install --no-install-recommends python3-numpy


echo "Migrate autostart from rc.local to systemd service - v1.3.7..."
sed -i '/(sleep 2;python3/c\#' /etc/rc.local # disable autostart in rc.local
if cmp -s /lib/systemd/system/honeypi.service /home/pi/HoneyPi/rpi-scripts/$VERSION/home/pi/HoneyPi/overlays/honeypi.service
then
   echo "The honeypi.service file is already the correct file..."
else
   echo "The honeypi.service file is different..."
   cp /home/pi/HoneyPi/rpi-scripts/$VERSION/home/pi/HoneyPi/overlays/honeypi.service /lib/systemd/system/honeypi.service
   chmod 644 /lib/systemd/system/honeypi.service
   systemctl daemon-reload
   systemctl enable honeypi.service
fi

echo "postupdatefinished 1" >> /var/www/html/version.txt
