#!/usr/bin/env python
# This file is part of HoneyPi which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import os
from datetime import datetime

def stop_tv():
    os.system("sudo /usr/bin/tvservice -o")

def stop_led():
    os.system("sudo bash -c \"echo 0 > /sys/class/leds/led0/brightness\"") #Turn off

def start_led():
    os.system("sudo bash -c \"echo 1 > /sys/class/leds/led0/brightness\"") #Turn on

def reboot():
    os.system("sudo reboot") # reboots the pi

def error_log(e, printText=None):
    try:
        if printText:
            printText = printText + " | " + repr(e)
            print(printText)
        else:
            printText = repr(e)

        file = '/home/pi/rpi-scripts/error.log'
        with open(file, "a") as myfile:
            myfile.write (str(datetime.now()) + " | " + printText + "\n")
        
        if os.path.getsize(file) > 100 * 1024:
            os.remove(file)
    except Exception: 
        pass