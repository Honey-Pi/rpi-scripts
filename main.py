#!/usr/bin/env python
# This file is part of HoneyPi which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import os
import sys
import threading
import time

import RPi.GPIO as GPIO  # allgemeines Einbinden der GPIO-Funktion

from read_and_upload_all import start_measurement
from read_settings import get_settings
from utilities import stop_tv, stop_led, start_led

isActive = 0 # flag to know if measurement is active or not
measurement_stop = threading.Event() # create event to stop measurement

def start_ap():
    global isActive
    isActive = 1 # measurement shall start next time
    print("AccessPoint wird aktiviert")
    os.system("sudo ifconfig wlan0 up") 
    start_led()
    time.sleep(0.4) 

def stop_ap():
    global isActive
    isActive = 0 # measurement shall stop next time
    print("AccessPoint wird deaktiviert")
    os.system("sudo ifconfig wlan0 down")
    stop_led()
    time.sleep(0.4) 

def close_script():
    global measurement_stop
    measurement_stop.set()
    print("Exit!")
    sys.exit()

def main():
    global isActive, measurement_stop

    settings = get_settings() # read settings for number of GPIO pin

    # setup gpio
    gpio = settings["button_pin"] or 17 # read pin from settings, if not defined choose pin 17
    GPIO.setwarnings(False) # Ignore warning for now
    GPIO.setmode(GPIO.BCM) # Zaehlweise der GPIO-PINS auf der Platine, analog zu allen Beispielen
    GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 17 to be an input pin and set initial value to be pulled low (off)

    # by default is AccessPoint down
    stop_ap()
    # stop HDMI power (save energy)
    stop_tv()
    # start as seperate background thread
    # because Taster pressing was not recognised
    measurement_stop = threading.Event() # create event to stop measurement
    measurement = threading.Thread(target=start_measurement, args=(measurement_stop,))
    measurement.start() # start measurement

    while True:
        input_state = GPIO.input(gpio)
        if input_state == GPIO.HIGH:
            print("Taster wurde gedrueckt")
            if isActive == 0:
                print("Taster: Stoppe Messungen")
                # stop the measurement by event's flag
                measurement_stop.set()
                start_ap() # finally start AP
            else:
                print("Taster: Starte Messungen")
                if measurement.is_alive():
                    print("Fehler: Thread ist noch aktiv.")
                measurement_stop.clear() # reset flag
                measurement_stop = threading.Event() # create event to stop measurement
                measurement = threading.Thread(target=start_measurement, args=(measurement_stop,))
                measurement.start() # start measurement
                stop_ap() # finally stop AP
        time.sleep(0.0001) # short sleep is good

    print("Dieser Text wird nie erreicht.")

if __name__ == '__main__':
    try:
        main()

    except (KeyboardInterrupt, SystemExit):
        close_script()