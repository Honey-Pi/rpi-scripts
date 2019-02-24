#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import os
from datetime import datetime

def stop_tv():
    os.system("sudo /usr/bin/tvservice -o")

def stop_led():
    os.system("sudo bash -c \"echo 0 > /sys/class/leds/led0/brightness\"") #Turn off

def start_led():
    os.system("sudo bash -c \"echo 1 > /sys/class/leds/led0/brightness\"") #Turn on

def client_to_ap_mode():
    # Disable router network
    os.system("wpa_cli disable_network 0")
    # pushing the wlan0 interface down
    os.system("sudo ip link set dev wlan0 down")
    # restart AP Services
    os.system("sudo systemctl restart dnsmasq.service")
    os.system("sudo systemctl restart hostapd.service")
    # bring up the wi-fi
    os.system("sudo ifconfig wlan0 up")

def ap_to_client_mode():
    # Stop AP Services
    os.system("sudo systemctl stop hostapd.service")
    os.system("sudo systemctl stop dnsmasq.service")
    # Start WPA Daemon
    os.system("sudo wpa_supplicant -i wlan0 -D wext -c /etc/wpa_supplicant/wpa_supplicant.conf -B")
    # Start dhclient for IP-Adresses
    os.system("sudo dhclient wlan0 &") # & will execute command in the background
    # Enable first router in list
    os.system("wpa_cli enable_network 0")

def start_wlan():
    os.system("sudo ifconfig wlan0 down")

def stop_wlan():
    os.system("sudo ifconfig wlan0 up") 

def reboot():
    os.system("sudo reboot") # reboots the pi

def shutdown():
    os.system("sudo shutdown -h 0")

def error_log(e=None, printText=None):
    try:
        file = '/home/pi/rpi-scripts/error.log'
        # reset file if to big
        if os.path.getsize(file) > 100 * 1024:
            os.remove(file)

        # generate printed text
        if printText and e:
            printText = printText + " | " + repr(e)
        elif e:
            printText = repr(e)
        else:
            printText = "No Text defined."

        print printText

        # write to file
        with open(file, "a") as myfile:
            myfile.write (str(datetime.now()) + " | " + printText + "\n")
        
    except Exception: 
        pass