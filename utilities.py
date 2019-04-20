#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import os
import time
from datetime import datetime

scriptsFolder = '/home/pi/HoneyPi/rpi-scripts'
backendFolder = '/var/www/html/backend'

def stop_tv():
    os.system("sudo /usr/bin/tvservice -o")

def stop_led():
    os.system("sudo bash -c \"echo 0 > /sys/class/leds/led0/brightness\"") #Turn off

def start_led():
    os.system("sudo bash -c \"echo 1 > /sys/class/leds/led0/brightness\"") #Turn on

def blink_led():
    stop_led()
    time.sleep(0.25)
    start_led()
    time.sleep(0.25)
    stop_led()
    time.sleep(0.25)
    start_led()
    time.sleep(0.25)
    stop_led()
    time.sleep(0.25)
    start_led()
    time.sleep(0.25)
    stop_led()
    time.sleep(0.25)
    start_led()

def start_wlan():
    os.system("sudo ifconfig wlan0 up") # aktiviert die WLAN-Schnittstelle

def stop_wlan():
    os.system("sudo ifconfig wlan0 down") # deaktiviert die WLAN-Schnittstelle

def client_to_ap_mode():
    stop_wlan()
    # disable the connected network
    os.system("wpa_cli -i wlan0 disable_network 0")
    # Enable static ip
    os.system("sudo mv /etc/dhcpcd.conf.disabled /etc/dhcpcd.conf")
    # Restart DHCP server for IP Address
    os.system("sudo systemctl restart dhcpcd.service && sudo systemctl daemon-reload") # & will execute command in the background
    # restart AP Services
    os.system("sudo systemctl restart dnsmasq.service")
    os.system("sudo systemctl restart hostapd.service || (systemctl unmask hostapd && systemctl enable hostapd && systemctl start hostapd) &") # if restart fails because service is masked => unmask
    start_wlan()

def ap_to_client_mode():
    stop_wlan()
    # Stop AP Services
    os.system("sudo systemctl stop hostapd.service")
    os.system("sudo systemctl stop dnsmasq.service")
    # Disable static ip
    os.system("sudo mv /etc/dhcpcd.conf /etc/dhcpcd.conf.disabled")
    # Restart DHCP server for IP Address
    os.system("sudo systemctl restart dhcpcd.service && sudo systemctl daemon-reload") # & will execute command in the background
    # Start WPA Daemon
    os.system("sudo wpa_supplicant -i wlan0 -D wext -c /etc/wpa_supplicant/wpa_supplicant.conf -B")
    # activate the wifi connection with Id=0
    os.system("wpa_cli -i wlan0 enable_network 0")
    start_wlan()

def reboot():
    os.system("sudo reboot") # reboots the pi

def shutdown():
    os.system("sudo shutdown -h 0")

def miliseconds():
    return int(round(time.time() * 1000))

# reduce size if file is to big
def check_file(file, size=5, entries=10):
    try:
        # If bigger than 25MB
        if os.path.getsize(file) > size * 1024:
            readFile = open(file)
            lines = readFile.readlines()
            readFile.close()
            w = open(file,'w')
            # delete first 25 lines in file
            # but skip first entry because it is header
            del lines[1:entries]
            w.writelines(lines)
            w.close()
    except FileNotFoundError:
        pass

def error_log(e=None, printText=None):
    try:
        file = scriptsFolder + '/error.log'
        check_file(file, 10, 50) # reset file if it gets to big

        # generate printed text
        if printText and e:
            printText = printText + " | " + repr(e)
        elif e:
            printText = e
        else:
            printText = "No Text defined."

        print(printText)

        # write to file
        with open(file, "a") as myfile:
            myfile.write (str(datetime.now()) + " | " + printText + "\n")

    except Exception:
        pass
