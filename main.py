#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import sys
import threading
import time

import RPi.GPIO as GPIO 

from read_and_upload_all import start_measurement
from read_settings import get_settings
from utilities import stop_tv, stop_led, start_led, error_log, reboot, client_to_ap_mode, ap_to_client_mode

# global vars
measurement = None
isActive = 0 # flag to know if measurement is active or not
measurement_stop = threading.Event() # create event to stop measurement

def start_ap():
    global isActive
    isActive = 1 # measurement shall start next time
    print("AccessPoint start")
    start_led()
    GPIO.output(21,GPIO.HIGH) # GPIO for led
    client_to_ap_mode()
    time.sleep(0.4) 

def stop_ap():
    global isActive
    isActive = 0 # measurement shall stop next time
    print("AccessPoint stop")
    stop_led()
    GPIO.output(21,GPIO.LOW) # GPIO for led
    ap_to_client_mode()
    time.sleep(0.4) 

def close_script():
    global measurement_stop
    measurement_stop.set()
    print("Exit!")
    GPIO.cleanup()
    sys.exit()

def button_pressed(gpio):
    global isActive, measurement_stop, measurement
    print("Button was pressed")
    if isActive == 0:
        print("Button: Stop measurement")
        # stop the measurement by event's flag
        measurement_stop.set()
        start_ap() # finally start AP
    else:
        print("Button: Start measurement")
        if measurement.is_alive():
            print("Warning: Thread should not be active anymore")
        measurement_stop.clear() # reset flag
        measurement_stop = threading.Event() # create event to stop measurement
        measurement = threading.Thread(target=start_measurement, args=(measurement_stop,))
        measurement.start() # start measurement
        stop_ap() # finally stop AP

def main():
    global isActive, measurement_stop, measurement

    settings = get_settings() # read settings for number of GPIO pin

    # setup gpio
    gpio = settings["button_pin"] # read pin from settings
    GPIO.setwarnings(False) # Ignore warning for now
    GPIO.setmode(GPIO.BCM) # Zaehlweise der GPIO-PINS auf der Platine
    GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 17 to be an input pin and set initial value to be pulled low (off)
    GPIO.setup(21, GPIO.OUT) # Set pin 18 to led output

    # by default is AccessPoint down
    stop_ap()
    # stop HDMI power (save energy)
    print("Shutting down HDMI to save engery.")
    stop_tv()
    # start as seperate background thread
    # because Taster pressing was not recognised
    measurement_stop = threading.Event() # create event to stop measurement
    measurement = threading.Thread(target=start_measurement, args=(measurement_stop,))
    measurement.start() # start measurement

    # register button press event
    GPIO.add_event_detect(gpio, GPIO.FALLING, callback=button_pressed, bouncetime = 150)

    # Main Lopp: Cancel with STRG+C
    while True:
        time.sleep(0.01)  # wait 10 ms to give CPU chance to do other things
        pass

    print("This text will never be printed.")

if __name__ == '__main__':
    try:
        main()

    except (KeyboardInterrupt, SystemExit):
        close_script()

    except Exception as e:
        error_log(e, "Unhandled Exception in Main")
        time.sleep(60)
        reboot()