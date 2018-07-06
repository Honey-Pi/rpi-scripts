#!/usr/bin/env python
import os
import sys
import threading
import time

import RPi.GPIO as GPIO  # allgemeines Einbinden der GPIO-Funktion

from read_and_upload_all import start_measurement
from read_settings import get_settings

settings = get_settings() # read settings for number of GPIO pin
i = 0 # flag to know if measurement is active or not
measurement_stop = threading.Event() # create event to stop measurement

def stop_tv():
    os.system("sudo /usr/bin/tvservice -o")

def stop_led():
    os.system("sudo bash -c \"echo 0 > /sys/class/leds/led0/brightness\"") #Turn off

def start_led():
    os.system("sudo bash -c \"echo 1 > /sys/class/leds/led0/brightness\"") #Turn on

def start_ap():
    global i
    i = 1 # measurement shall start next time
    print("AccessPoint wird aktiviert")
    os.system("sudo ifconfig wlan0 up") 
    start_led()
    time.sleep(0.4) 

def stop_ap():
    global i
    i = 0 # measurement shall stop next time
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
    global i, measurement_stop

    # setup gpio
    gpio = settings["button_pin"]
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
            if i == 0:
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