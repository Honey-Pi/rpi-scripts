#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import os
import time
from datetime import datetime
import urllib

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

def create_ap():
    os.system("sudo sh /home/pi/HoneyPi/create_uap.sh")
    os.system("ifdown uap0")

def client_to_ap_mode():
    os.system("ifdown wlan0")
    os.system("ip addr add 192.168.4.1/24 broadcast 192.168.4.255 dev uap0") #dhcpcd not working
    os.system("ifup uap0")
    os.system("sudo systemctl stop dnsmasq.service")
    os.system("(sudo systemctl restart hostapd.service || (systemctl unmask hostapd && systemctl start hostapd))&") # if restart fails because service is masked => unmask
    os.system("ifup wlan0")
    os.system("sudo systemctl start dnsmasq.service")

def ap_to_client_mode():
    # Stop AP Services
    os.system("ifdown uap0")
    os.system("sudo systemctl stop hostapd.service")
    os.system("sudo systemctl stop dnsmasq.service")
    os.system("ifup wlan0")

def reboot():
    os.system("sudo systemctl stop hostapd.service")
    os.system("sudo systemctl disable hostapd.service")
    os.system("sudo systemctl stop dnsmasq.service")
    os.system("sudo systemctl disable dnsmasq.service")
    os.system("sudo reboot") # reboots the pi

def shutdown():
    os.system("sudo shutdown -h 0")

def decrease_nice():
    pid = os.getpid()
    os.system("sudo renice -n -19 -p " + str(pid) + " >/dev/null")

def normal_nice():
    pid = os.getpid()
    os.system("sudo renice -n 0 -p " + str(pid) + " >/dev/null")

def start_single(file_path=".isActive"):
    file = scriptsFolder + '/' + file_path
    try:
        time_to_wait = 2*60 # 2 Minutes
        # wait as long as the file exists to block further measurements
        # because there is another HX711 process already running
        # but skip if the file is too old (time_to_wait)
        while os.path.exists(file):
            # skip waiting if file is older than 2 minutes
            # this is because the last routine could be canceled irregular
            # and the file could be still existing
            filetime = os.stat(file).st_mtime
            if filetime < time.time()-time_to_wait:
                print("Skiped waiting because the measurement process we are waiting for was likely not properly finished.")
                os.remove(file) # remove the old file
                break
            time.sleep(1)
            print("Measurement waits for a process to finish. Another measurement job is running at the moment.")
        # create file to stop other HX711 readings
        f = open(file, "x")
    except Exception as ex:
        print("start_single:" + str(ex))
        pass
    finally:
        decrease_nice()

def stop_single(file_path=".isActive"):
    file = scriptsFolder + '/' + file_path
    try:
        # remove file because reading HX711 finished
        if os.path.exists(file):
            os.remove(file)
        else:
            print('stop_single: File does not exists.')
    except Exception as ex:
        print("stop_single:" + str(ex))
        pass
    finally:
        normal_nice()

def miliseconds():
    return int(round(time.time() * 1000))

# reduce size if file is to big
def check_file(file, size=5, entries=25, skipFirst=0):
    try:
        # If bigger than 5MB
        if os.path.getsize(file) > size * 1024 * 1024:
            readFile = open(file)
            lines = readFile.readlines()
            readFile.close()
            w = open(file,'w')
            # delete first 25 lines in file
            # When CSV: skip first entry because it is header (skipFirst=1)
            del lines[skipFirst:entries]
            w.writelines(lines)
            w.close()
    except FileNotFoundError:
        pass

def error_log(e=None, printText=None):
    try:
        file = scriptsFolder + '/error.log'
        check_file(file) # reset file if it gets to big

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


def wait_for_internet_connection(maxTime=10):
    i = 0
    while i < maxTime:
        i+=1
        try:
            response = urllib.request.urlopen('http://www.msftncsi.com/ncsi.txt', timeout=1).read()

            if response == "Microsoft NCSI":
                print("Success: Connection established after " + str(i) + " seconds.")
                return True
        except:
            pass
        finally:
            time.sleep(1)

    return False

def delete_settings():
    os.remove(backendFolder + '/settings.json')
