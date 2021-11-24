#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import superglobal
import sys
import threading
import time
import logging
from logging.handlers import RotatingFileHandler

import RPi.GPIO as GPIO

from read_and_upload_all import start_measurement
from read_settings import get_settings
from utilities import logfile, stop_tv, stop_led, toggle_blink_led, start_led, stop_hdd_led, start_hdd_led, reboot, client_to_ap_mode, ap_to_client_mode, blink_led, miliseconds, shutdown, delete_settings, getStateFromStorage, setStateToStorage, update_wittypi_schedule, connect_internet_modem, get_default_gateway_linux, get_interface_upstatus_linux, get_pi_model, get_rpiscripts_version, runpostupgradescript, check_undervoltage, sync_time_ntp

from multiprocessing import Process, Queue, Value
from OLed import oled_off, oled_start_honeypi,oled_diag_data,oled_interface_data, oled_init, main, oled_measurement_data, oled_maintenance_data

logger = logging.getLogger('HoneyPi.main')

# global vars
superglobal = superglobal.SuperGlobal()
measurement = None
isActive = 0 # flag to know if measurement is active or not
measurement_stop = threading.Event() # create event to stop measurement
time_rising = 0 # will be set by button_pressed event if the button is rised
# the following will be overwritten by settings.json:
debug = 0
GPIO_BTN = 16
GPIO_LED = 21 # GPIO for led
LED_STATE = 0

def oled():
    oled_init()
    oled_start_honeypi()
    time.sleep(4)
    oled_diag_data()
    time.sleep(4)
    oled_measurement_data()
    time.sleep(4)
    oled_maintenance_data()
    time.sleep(4)
    oled_interface_data()
    oled_off()
    return

def timesync():
            ntptimediff=sync_time_ntp()
            logger.info('Time syncronized to NTP - diff: ' + ntptimediff)


def start_ap():
    global isActive, GPIO_LED
    start_led(GPIO_LED)
    t1 = threading.Thread(target=client_to_ap_mode)
    t1.start()
    t1.join()
    isActive = 1 # measurement shall start next time
    logger.info(">>> Connect yourself to HoneyPi-AccessPoint Wifi")
    superglobal.isMaintenanceActive=True
    #isMaintenanceActive=setStateToStorage('isMaintenanceActive', True)
    oled_init()
    oled_maintenance_data()

def stop_ap():
    global isActive, GPIO_LED
    stop_led(GPIO_LED)
    t2 = threading.Thread(target=ap_to_client_mode)
    t2.start()
    t2.join()
    isActive = 0 # measurement shall stop next time
    superglobal.isMaintenanceActive=False
    #isMaintenanceActive=setStateToStorage('isMaintenanceActive', False)
    oled_off()

def get_led_state(self):
    global GPIO_LED, LED_STATE
    LED_STATE = GPIO.input(GPIO_LED)
    return LED_STATE

def close_script():
    global measurement_stop
    measurement_stop.set()
    print("Exit!")
    GPIO.cleanup()
    sys.exit()

def toggle_measurement():
    global isActive, measurement_stop, measurement, GPIO_LED
    if isActive == 0:
        logger.info(">>> Button was pressed: Stop measurement / start AccessPoint")
        # stop the measurement by setting event's flag
        measurement_stop.set()
        start_ap() # finally start AP
    elif isActive == 1:
        logger.info(">>> Button was pressed: Start measurement / stop AccessPoint")
        if measurement.is_alive():
            logger.warning("Thread should not be active anymore")
        # start the measurement by clearing event's flag
        measurement_stop.clear() # reset flag
        measurement_stop = threading.Event() # create event to stop measurement
        measurement = threading.Thread(target=start_measurement, args=(measurement_stop,))
        measurement.start() # start measurement
        stop_ap() # finally stop AP
    else:
        logger.error("Button press recognized but undefined state of Maintenance Mode")
    # make signal, that job finished
    tblink = threading.Thread(target=toggle_blink_led, args = (GPIO_LED, 0.2))
    tblink.start()

def button_pressed(channel):
    global GPIO_BTN, LED_STATE, GPIO_LED
    LED_STATE = get_led_state(GPIO_LED)
    if GPIO.input(GPIO_BTN): # if port == 1
        button_pressed_rising("button_pressed")
    else: # if port != 1
        button_pressed_falling("button_pressed")

def button_pressed_rising(self):
    global time_rising, debug, GPIO_LED, LED_STATE
    time_rising = miliseconds()

    if debug:
        print("button_pressed_rising")

def button_pressed_falling(self):
    global time_rising, debug, GPIO_LED, LED_STATE
    time_falling = miliseconds()
    time_elapsed = time_falling-time_rising
    time_rising = 0 # reset to prevent multiple fallings from the same rising
    MIN_TIME_TO_ELAPSE = 500 # miliseconds
    MAX_TIME_TO_ELAPSE = 3000

    if debug:
        print("button_pressed_falling")
    if time_elapsed >= 0 and time_elapsed <= 30000:
        if time_elapsed >= MIN_TIME_TO_ELAPSE and time_elapsed <= MAX_TIME_TO_ELAPSE:
            # normal button press to switch between measurement and maintenance
            tmeasurement = threading.Thread(target=toggle_measurement)
            tmeasurement.start()
        elif time_elapsed >= 50 and time_elapsed <= 500:
            if displaysettings["enabled"]:
                pOLed = threading.Thread(target=oled, args=())
                pOLed.start()
        elif time_elapsed >= 5000 and time_elapsed <= 10000:
            # shutdown raspberry
            tblink = threading.Thread(target=blink_led, args = (GPIO_LED, 0.1))
            tblink.start()
            shutdown()
        elif time_elapsed >= 10000 and time_elapsed <= 15000:
            # reset settings and shutdown
            tblink = threading.Thread(target=blink_led, args = (GPIO_LED, 0.1))
            tblink.start()
            delete_settings()
            update_wittypi_schedule("")
            logger.critical("Resettet settings because Button was pressed wore than 10seconds.")
            shutdown()
        elif debug:
            time_elapsed_s = float("{0:.2f}".format(time_elapsed/1000)) # ms to s
            logger.warning("Too short Button press, Too long Button press OR inteference occured: " + str(time_elapsed_s) + "s elapsed.")

def main():
    try:
        global isActive, measurement_stop, measurement, debug, GPIO_BTN, GPIO_LED

        # Zaehlweise der GPIO-PINS auf der Platine
        GPIO.setmode(GPIO.BCM)

        # read settings for number of GPIO pin
        settings = get_settings()
        debuglevel=int(settings["debuglevel"])
        debuglevel_logfile=int(settings["debuglevel_logfile"])

        logger = logging.getLogger('HoneyPi')
        logger.setLevel(logging.DEBUG)
        fh = RotatingFileHandler(logfile, maxBytes=5*1024*1024, backupCount=60)
        fh.setLevel(logging.getLevelName(debuglevel_logfile))
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.getLevelName(debuglevel))
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(fh)
        logger.addHandler(ch)

        time.sleep(1)

        if debuglevel <= 10:
            debug = True # flag to enable debug mode (HDMI output enabled and no rebooting)
        else:
            debug = False # flag to enable debug mode (HDMI output enabled and no rebooting)

        if debuglevel > 20:
            # stop HDMI power (save energy)
            logger.info('HoneyPi '+ get_rpiscripts_version() + ' Started on ' + get_pi_model() + ', Debuglevel: "' + logging.getLevelName(debuglevel) + '", Debuglevel logfile: "' + logging.getLevelName(debuglevel_logfile)+'"')
            stop_tv()
            stop_hdd_led()
        else:
            logger.info('HoneyPi '+ get_rpiscripts_version() + ' Started on ' + get_pi_model())
            start_hdd_led()
        global displaysettings
        displaysettings = settings["display"]
        q = Queue()
        if displaysettings["enabled"]:
            tOLed = threading.Thread(target=oled, args=())
            tOLed.start()

        if settings["offline"] != 3:
            ttimesync = threading.Thread(target=timesync, args=())
            ttimesync.start()
        else:
            logger.debug('Offline mode  - no time syncronization to NTP')

        #if displaysettings["enabled"]:
        #    tOLed.join()
        if settings["offline"] != 3:
            ttimesync.join()


        runpostupgradescript()

        GPIO_BTN = settings["button_pin"]
        GPIO_LED = settings["led_pin"]

        # setup LED as output
        GPIO.setup(GPIO_LED, GPIO.OUT)

        # blink with LED on startup
        tblink = threading.Thread(target=blink_led, args = (GPIO_LED,))
        tblink.start()

        # Call wvdial for surfsticks
        connect_internet_modem(settings)

        # check undervolate for since system start
        check_undervoltage()

        # start as seperate background thread
        # because Taster pressing was not recognised
        superglobal.isMaintenanceActive=False
        #isMaintenanceActive=setStateToStorage('isMaintenanceActive', False)
        measurement_stop = threading.Event() # create event to stop measurement
        measurement = threading.Thread(target=start_measurement, args=(measurement_stop,))
        measurement.start() # start measurement

        # setup Button
        GPIO.setup(GPIO_BTN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 16 to be an input pin and set initial value to be pulled low (off)
        bouncetime = 100 # ignoring further edges for 100ms for switch bounce handling
        # register button press event
        GPIO.add_event_detect(GPIO_BTN, GPIO.BOTH, callback=button_pressed, bouncetime=bouncetime)

        # Main Lopp: Cancel with STRG+C
        while True:
            time.sleep(0.2)  # wait 200 ms to give CPU chance to do other things
            pass

        print("This text will never be printed.")
    except Exception as ex:
        logger.critical("Unhandled Exception in main: " + repr(ex))
        if not debug:
            time.sleep(60)
            reboot()

if __name__ == '__main__':
    try:
        main()

    except (KeyboardInterrupt, SystemExit):
        close_script()

    except Exception as ex:
        logger.error("Unhandled Exception in __main__ " + repr(ex))
        if not debug:
            time.sleep(60)
            reboot()
