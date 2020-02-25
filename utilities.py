#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import os
import time
from datetime import datetime
import urllib
import json
import RPi.GPIO as GPIO

honeypiFolder = '/home/pi/HoneyPi'
scriptsFolder = honeypiFolder + '/rpi-scripts'
backendFolder = '/var/www/html/backend'
settingsFile = backendFolder + '/settings.json'

def stop_tv():
    os.system("sudo /usr/bin/tvservice -o")

def stop_led(gpio=21):
    # Turn Raspi-LED off
    os.system("sudo bash -c 'echo 0 > /sys/class/leds/led0/brightness'") # green LED
    os.system("sudo bash -c 'echo 0 > /sys/class/leds/led1/brightness'") # red LED
    # Setup GPIO LED
    GPIO.setmode(GPIO.BCM) # Counting the GPIO PINS on the board
    GPIO.setwarnings(False)
    GPIO.setup(gpio, GPIO.OUT) # Set pin as output
    GPIO.setwarnings(True)
    GPIO.output(gpio, GPIO.LOW)

def start_led(gpio=21):
    # Turn Raspi-LED on
    os.system("sudo bash -c 'echo 1 > /sys/class/leds/led0/brightness'") # green LED
    os.system("sudo bash -c 'echo 1 > /sys/class/leds/led1/brightness'") # red LED
    # Setup GPIO LED
    GPIO.setmode(GPIO.BCM) # Counting the GPIO PINS on the board
    GPIO.setwarnings(False)
    GPIO.setup(gpio, GPIO.OUT) # Set pin as output
    GPIO.setwarnings(True)
    GPIO.output(gpio, GPIO.HIGH)

def blink_led(gpio=21, duration=0.25):
    stop_led(gpio)
    time.sleep(duration)
    start_led(gpio)
    time.sleep(duration)
    stop_led(gpio)
    time.sleep(duration)
    start_led(gpio)
    time.sleep(duration)
    stop_led(gpio)
    time.sleep(duration)
    start_led(gpio)
    time.sleep(duration)
    stop_led(gpio)
    time.sleep(duration)
    start_led(gpio)

def create_ap():
    os.system("sudo sh " + scriptsFolder + "/shell-scripts/create_uap.sh")
    os.system("sudo ifdown uap0")

def client_to_ap_mode():
    os.system("sudo sh " + scriptsFolder + "/shell-scripts/client_to_ap_mode.sh")

def ap_to_client_mode():
    os.system("sudo sh " + scriptsFolder + "/shell-scripts/ap_to_client_mode.sh")

def reboot():
    os.system("sudo systemctl stop hostapd.service")
    os.system("sudo systemctl disable hostapd.service")
    os.system("sudo systemctl stop dnsmasq.service")
    os.system("sudo systemctl disable dnsmasq.service")
    os.system("sudo reboot")

def shutdown():
    os.system("sudo systemctl stop hostapd.service")
    os.system("sudo systemctl disable hostapd.service")
    os.system("sudo systemctl stop dnsmasq.service")
    os.system("sudo systemctl disable dnsmasq.service")
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

        dt = datetime.now()
        timestamp = dt.replace(microsecond=0)

        # write to file
        with open(file, "a") as myfile:
            myfile.write (str(timestamp) + " | " + printText + "\n")

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
    os.remove(settingsFile)

def clean_fields(ts_fields, countChannels, debug):
    if debug :
       print('Dictionary to be converted:')
       print(json.dumps(ts_fields))
    ts_fields_cleaned = {}
    fieldNew = {};
    for field in ts_fields:
        fieldNumber = int(field.replace('field',''))
        fieldNumberNew = fieldNumber - (8 * countChannels)
        if fieldNumberNew <= 8 and fieldNumberNew > 0 :
            if debug :
                print('Data to be converted:')
                print(ts_fields['field' + str(fieldNumber)])

            ts_fields_cleaned['field' + str(fieldNumberNew)]=ts_fields['field' + str(fieldNumber)]
            if debug :
                print('Field ' + str(fieldNumberNew) + ' written')
                print(json.dumps(ts_fields_cleaned['field' + str(fieldNumberNew)]))
    if debug :
        print('Cleaned dictionary:')
        print(json.dumps(ts_fields_cleaned))
    return ts_fields_cleaned

# decorater used to block function printing to the console
def blockPrinting(func):
    def func_wrapper(*args, **kwargs):
        # block all printing to the console
        sys.stdout = open(os.devnull, 'w')
        # call the method in question
        value = func(*args, **kwargs)
        # enable all printing to the console
        sys.stdout = sys.__stdout__
        # pass the return value of the method back
        return value

    return func_wrapper

def update_wittypi_schedule(schedule):
    try:
        wittypi_scheduleFile = backendFolder + "/schedule.wpi"
        # write values to file
        outfile = open(wittypi_scheduleFile, "w")
        outfile.truncate(0)
        outfile.write(schedule)
        outfile.close()
        if os.path.isfile('/home/pi/wittyPi/wittyPi.sh') and os.path.isfile('/home/pi/wittyPi/syncTime.sh') and os.path.isfile('/home/pi/wittyPi/runScript.sh'):
            # WittyPi 2
            print("Wittypi 2 or Wittypi Mini detected.")
            if len(schedule) > 1:
                os.system("sudo sh " + backendFolder + "/shell-scripts/change_wittypi.sh 1 > /dev/null")
            else:
                os.system("sudo sh " + backendFolder + "/shell-scripts/change_wittypi.sh 0 > /dev/null")
            return True
        elif os.path.isfile('/home/pi/wittypi/wittyPi.sh') and os.path.isfile('/home/pi/wittypi/syncTime.sh') and os.path.isfile('/home/pi/wittypi/runScript.sh'):
            # WittyPi 3
            print("Wittypi 3 or 3 Mini detected.")
            if len(schedule) > 1:
                os.system("sudo sh " + backendFolder + "/shell-scripts/change_wittypi.sh 1 > /dev/null")
            else:
                os.system("sudo sh " + backendFolder + "/shell-scripts/change_wittypi.sh 0 > /dev/null")
            return True
        else:
            error_log("WittyPi installation missing or incomplete")
    except Exception as ex:
        print("Error in function update_wittypi_schedule: " + str(ex))

    return False
