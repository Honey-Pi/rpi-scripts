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
from maintenance import maintenance
from read_settings import get_settings, get_sensors
from utilities import stop_tv, stop_led, toggle_blink_led, start_led, stop_hdd_led, start_hdd_led, reboot, client_to_ap_mode, ap_to_client_mode, blink_led, miliseconds, shutdown, delete_settings, getStateFromStorage, setStateToStorage, connect_internet_modem, get_default_gateway_linux, get_interface_upstatus_linux, get_pi_model, get_rpiscripts_version, runpostupgradescript, check_undervoltage, sync_time_ntp, offlinedata_prepare, fix_fileaccess, whoami, is_system_datetime_valid
from constant import scriptsFolder, logfile, GPIO_BTN, GPIO_LED, local_tz
from wittypiutilities import check_wittypi, set_wittypi_rtc, update_wittypi_schedule, rtc_to_system, remove_wittypi_internet_timesync, continue_wittypi_schedule, add_halt_pin_event

from multiprocessing import Process, Queue, Value
from OLed import oled_off, oled_start_honeypi,oled_diag_data,oled_interface_data, oled_init, main, oled_measurement_data, oled_maintenance_data, oled_view_channels
from read_gps import init_gps, timesync_gps

from datetime import datetime
from datetime import timedelta


logger = logging.getLogger('HoneyPi.main')

# global vars
superglobal = superglobal.SuperGlobal()
measurement = None
settings = {}
workingOnButtonpressIsActive = False # flag to know if measurement is active or not
measurement_stop = threading.Event() # create event to stop measurement
maintenance_stop = threading.Event() # create event to stop maintenance
time_rising = 0 # will be set by button_pressed event if the button is rised
# the following will be overwritten by settings.json:
debug = 0
 # GPIO for led
LED_STATE = 0
bouncetime = 49 # ignoring further edges for 49ms for switch bounce handling
btn_rise = False # initial state for button

def oled():
    global settings
    oled_init()
    oled_start_honeypi()
    time.sleep(4)
    oled_diag_data()
    time.sleep(4)
    oled_measurement_data()
    time.sleep(4)
    oled_interface_data()
    ts_channels = settings["ts_channels"]
    oled_view_channels(offlinedata_prepare(ts_channels))
    time.sleep(4)
    oled_maintenance_data(settings)
    if not superglobal.isMaintenanceActive:
        oled_off()
    return

def timesync(settings, wittypi_status, loggername='HoneyPi.main'): # TODO outsource to utilities bc not related to main
    try:
        logger = logging.getLogger(loggername)
        ntptimediff_str = sync_time_ntp()
        ntptimediff_s = 0
        if ntptimediff_str:
            ntptimediff_str = str(round(float(ntptimediff_str.replace("s","")),2))
            ntptimediff_s = abs(int(float(ntptimediff_str)))

            if ntptimediff_s >= 60:
                logger.critical('Time syncronized to NTP - difference was: ' + ntptimediff_str + 's (more than 60 seconds)')
                set_wittypi_rtc(settings, wittypi_status)
            else:
                logger.info('Time syncronized to NTP - difference was: ' + ntptimediff_str + 's')
                if ('rtc_time_is_valid' in wittypi_status) and not wittypi_status['rtc_time_is_valid']:
                    set_wittypi_rtc(settings, wittypi_status)
        else:
            logger.error('Time synchronising NTP - not able to sync')

    except ValueError as ex:
        if str(ex) == "could not convert string to float":
            logger.error('Time syncronisation did not return the time difference')
        else:
            logger.exception("ValueError in timesync")
    except:
        logger.exception("Exception in timesync")
        
    return False

def gpstimesync(gpsSensor, blank=None): # TODO outsource to utilities bc not related to main
    try:
        timesync_gps(gpsSensor)
    except Exception as ex:
        logger.exception("Exception in gpstimesync")
    return False

def start_ap():
    global workingOnButtonpressIsActive, GPIO_LED, settings
    superglobal.isMaintenanceActive = True # measurement shall start next time
    start_led(GPIO_LED)
    t1 = threading.Thread(target=client_to_ap_mode)
    t1.start()
    t1.join(timeout=30)
    logger.info(">>> Starting HoneyPi-AccessPoint finished. Connect to HoneyPi-WiFi now.")
    workingOnButtonpressIsActive = False
    start_led(GPIO_LED)
    #start_maintenance()
    #pMaintenance = threading.Thread(target=maintenance, args=(maintenance_stop,))
    #pMaintenance.start()

    if settings['display']['enabled']:
        oled_init()
        oled_maintenance_data(settings)

def stop_ap():
    global workingOnButtonpressIsActive, GPIO_LED, settings
    stop_led(GPIO_LED)
    t2 = threading.Thread(target=ap_to_client_mode)
    t2.start()
    t2.join(timeout=30)
    workingOnButtonpressIsActive = False
    superglobal.isMaintenanceActive = False # measurement shall stop next time
    if settings['display']['enabled']:
        oled_off()

def get_led_state(self):
    global GPIO_LED, LED_STATE
    LED_STATE = GPIO.input(GPIO_LED)
    return LED_STATE

def close_script():
    global measurement_stop, maintenance_stop
    measurement_stop.set()
    maintenance_stop.set()
    logger.info('HoneyPi exiting due to external event!')
    print("Exit!")
    GPIO.cleanup()
    sys.exit()

def toggle_measurement():
    global workingOnButtonpressIsActive, measurement_stop, maintenance_stop, measurement, GPIO_LED
    if not workingOnButtonpressIsActive:
        workingOnButtonpressIsActive = True
        if not superglobal.isMaintenanceActive:
            logger.info(">>> Button was pressed: Stop measurement / start AccessPoint")
            # stop the measurement by setting event's flag
            measurement_stop.set()
            maintenance_stop.clear()
            start_ap() # finally start AP
            pMaintenance = threading.Thread(target=maintenance, args=(maintenance_stop, measurement_stop,))
            pMaintenance.start()
            pMaintenance.join(10)
            while pMaintenance.is_alive and measurement_stop.is_set():
                time.sleep(1)
            if not measurement_stop.is_set():
                measurement = threading.Thread(target=start_measurement, args=(measurement_stop,))
                measurement.start() # start measurement
        elif superglobal.isMaintenanceActive:
            logger.info(">>> Button was pressed: Start measurement / stop AccessPoint")
            if measurement.is_alive():
                logger.warning("Thread should not be active anymore")
            # start the measurement by clearing event's flag
            measurement_stop.clear() # reset flag
            maintenance_stop.set()
            #measurement_stop = threading.Event() '''Required here? already in global definition!'''# create event to stop measurement
            measurement = threading.Thread(target=start_measurement, args=(measurement_stop,))
            measurement.start() # start measurement
            stop_ap() # finally stop AP
        else:
            logger.error("Button press recognized but undefined state of Maintenance Mode")
        # make signal, that job finished
        tblink = threading.Thread(target=toggle_blink_led, args = (GPIO_LED, 0.2))
        tblink.start()

def button_pressed(channel):
    global GPIO_BTN, LED_STATE, GPIO_LED, bouncetime, btn_rise
    LED_STATE = get_led_state(GPIO_LED)
    btn_rise = not btn_rise
    if btn_rise:
        GPIO.remove_event_detect(GPIO_BTN)
        GPIO.add_event_detect(GPIO_BTN, GPIO.FALLING, callback=button_pressed, bouncetime=bouncetime)
        button_pressed_rising("button_pressed")
    else:
        GPIO.remove_event_detect(GPIO_BTN)
        GPIO.add_event_detect(GPIO_BTN, GPIO.RISING, callback=button_pressed, bouncetime=bouncetime)
        button_pressed_falling("button_pressed")

def button_pressed_rising(self):
    global time_rising, debug, GPIO_LED, LED_STATE
    time_rising_new = datetime.now(local_tz)
    logger.debug("button_pressed_rising")
    if time_rising is not None:
        logger.warning("Button rising occured multiple times without falling")
    time_rising = time_rising_new


def button_pressed_falling(self):
    global time_rising, debug, GPIO_LED, LED_STATE, settings
    time_falling = datetime.now(local_tz)
    logger.debug("button_pressed_falling")
    
    if time_rising is not None: 
        time_elapsed_td = time_falling-time_rising
        time_elapsed = time_elapsed_td / timedelta(milliseconds=1)
        logger.debug("Button was pressed for: " + str(round(time_elapsed,0)) + " miliseconds | From: " + time_rising.strftime("%a %d %b %Y %H:%M:%S.%f") + " until " + time_falling.strftime("%a %d %b %Y %H:%M:%S.%f"))
        time_rising = None # reset to prevent multiple fallings from the same rising
        
        MIN_TIME_TO_ELAPSE = 50
        MAX_TIME_TO_ELAPSE_OLED = 500 # miliseconds
        MAX_TIME_TO_ELAPSE_MAINTENANCE = 3000
        MIN_TIME_TO_ELAPSE_SHUTDOWN = 5000
        MAX_TIME_TO_ELAPSE_SHUTDOWN = 10000
        MAX_TIME_TO_ELAPSE_RESET = 15000

        if time_elapsed >= 0 and time_elapsed <= 30000:
            if time_elapsed > MIN_TIME_TO_ELAPSE and time_elapsed <= MAX_TIME_TO_ELAPSE_OLED:
                # button press to display values on LED
                if settings['display']['enabled']:
                    pOLed = threading.Thread(target=oled, args=())
                    pOLed.start()
            elif time_elapsed > MAX_TIME_TO_ELAPSE_OLED and time_elapsed <= MAX_TIME_TO_ELAPSE_MAINTENANCE:
                # button press to switch between measurement and maintenance
                tmeasurement = threading.Thread(target=toggle_measurement)
                tmeasurement.start()
            elif time_elapsed > MIN_TIME_TO_ELAPSE_SHUTDOWN and time_elapsed <= MAX_TIME_TO_ELAPSE_SHUTDOWN:
                # button press to shutdown raspberry
                tblink = threading.Thread(target=blink_led, args = (GPIO_LED, 0.1))
                tblink.start()
                logger.critical("Shutting down because button was pressed more than "+ str(MIN_TIME_TO_ELAPSE_SHUTDOWN/1000) + " seconds.")
                shutdown(settings)
            elif time_elapsed > MAX_TIME_TO_ELAPSE_SHUTDOWN and time_elapsed <= MAX_TIME_TO_ELAPSE_RESET:
                # button press to reset settings and shutdown
                if settings["enable_reset"]:
                    # reset settings and shutdown
                    tblink = threading.Thread(target=blink_led, args = (GPIO_LED, 0.1))
                    tblink.start()
                    delete_settings()
                    update_wittypi_schedule("")
                    logger.critical("Resetting settings and shutting down because button was pressed more than "+ str(MAX_TIME_TO_ELAPSE_SHUTDOWN/1000) + "seconds.")
                    shutdown(settings)
                else:
                    logger.critical("Button was pressed more than 10 seconds but NOT resetting settings and shutting down because feature disabled in webinterface.")
            else:
                time_elapsed_s = float("{0:.2f}".format(time_elapsed/1000)) # ms to s
                logger.warning("Too short Button press, too long Button press OR inteference occured. Button was pressed for: " + str(time_elapsed_s) + "s.")
    else:
        logger.warning("Button falling recognized but no button rising")

def halt_pin_event_detected(channel):
    if GPIO.input(channel) == 0:
        logger.info("Shutdown request detected by event raised from WittyPi (button pressed / Shutdown time) on channel " + str(channel))
        shutdown(settings)

def main():
    try:
        global workingOnButtonpressIsActive, measurement_stop, measurement, debug, GPIO_BTN, GPIO_LED, settings

        # Zaehlweise der GPIO-PINS auf der Platine
        GPIO.setmode(GPIO.BCM)

        # read settings for number of GPIO pin
        settings = get_settings()
        debuglevel=int(settings["debuglevel"])
        debuglevel_logfile=int(settings["debuglevel_logfile"])

        # TODO outsource RotatingFileHandler as this code block is called multiple times
        logger = logging.getLogger('HoneyPi') # TODO make loggername as file name generic
        logger.setLevel(logging.DEBUG)
        try:
            fh = RotatingFileHandler(logfile, maxBytes=5*1024*1024, backupCount=60)
        except PermissionError:
            #set file access
            fix_fileaccess(scriptsFolder + '/err*.*')
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

        # check if wittypi or other RTC is connected and if RTC time is valid
        wittypi_status = check_wittypi(settings, False)
        if ('rtc_time_is_valid' in wittypi_status) and ('rtc_time_local' in wittypi_status) and wittypi_status['rtc_time_is_valid'] and (wittypi_status['rtc_time_local'] is not None):
            #set systemtime from RTC
            logger.info('Writing RTC time ' + wittypi_status['rtc_time_local'].strftime("%a %d %b %Y %H:%M:%S") + ' to system...')
            rtc_to_system()
            continue_wittypi_schedule()
        if wittypi_status['is_rtc_connected'] and not wittypi_status['service_active']:
            #add event to shutdown Pi from WittyPi button
            add_halt_pin_event(halt_pin_event_detected)

        if debuglevel > 20:
            # stop HDMI power (save energy)
            logger.info('HoneyPi '+ get_rpiscripts_version() + ' Started on ' + get_pi_model() + ' as User ' + whoami() + ', Debuglevel: "' + logging.getLevelName(debuglevel) + '", Debuglevel logfile: "' + logging.getLevelName(debuglevel_logfile)+'"')
            stop_tv()
            stop_hdd_led()
        else:
            logger.info('HoneyPi '+ get_rpiscripts_version() + ' Started on ' + get_pi_model() + ' as User ' + whoami())
            start_hdd_led()

        q = Queue() # TODO check is this used anywhere?

        # remove commands to set RTC time to internet from wittypi syncTime.sh
        remove_wittypi_internet_timesync()

        # check if GPS is configured and start background thread to sync time to GPS if required.
        gpsSensors = get_sensors(settings, 99)
        for (sensorIndex, gpsSensor) in enumerate(gpsSensors):
            init_gps(gpsSensor)
            tgpstimesync = threading.Thread(target=gpstimesync, args=(gpsSensor, None))
            tgpstimesync.start()
            break

        # check if Internet is configured and start background thread to sync time to NTP Servers if required.
        if settings["offline"] != 3:
            ttimesync = threading.Thread(target=timesync, args=(settings, wittypi_status))
            ttimesync.start()
        else:
            logger.debug('Offline mode - no time syncronization to NTP')

        # TODO add description what is done here and why
        runpostupgradescript()

        GPIO_BTN = settings["button_pin"]
        GPIO_LED = settings["led_pin"]

        # setup LED as output
        try:
            GPIO.setup(GPIO_LED, GPIO.OUT)
        except RuntimeError as ex:
            logger.critical("RuntimeError occuered on GPIO setup! Honeypi User '"+ whoami() + "' does not have access to GPIO!") # + str(ex))
            if not debug:
                time.sleep(60)
                reboot(settings)

        #create global variables
        if superglobal.isMaintenanceActive is None:
            superglobal.isMaintenanceActive=False
            logger.debug("Set initial state of isMaintenanceActive: '" + str(superglobal.isMaintenanceActive) + "'")
        #measurement_stop = threading.Event() '''Required here? already in global definition!'''# create event to stop measurement

        # Call wvdial for surfsticks
        connect_internet_modem(settings)

        # check undervoltage for since system start
        check_undervoltage()

        # setup Button
        try:
            GPIO.setup(GPIO_BTN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 16 to be an input pin and set initial value to be pulled low (off)
        except RuntimeError as ex:
            logger.critical("RuntimeError occuered on GPIO setup! Honeypi User '"+ whoami() + "' does not have access to GPIO!") # + str(ex))
            if not debug:
                time.sleep(60)
                reboot(settings)
        bouncetime = 100 # ignoring further edges for 100ms for switch bounce handling
        # register button press event
        GPIO.add_event_detect(GPIO_BTN, GPIO.RISING, callback=button_pressed, bouncetime=bouncetime)

        # TODO add description what is done here and why
        if settings['display']['enabled']:
            tOLed = threading.Thread(target=oled, args=())
            tOLed.start()

        # blink with LED on startup
        tblink = threading.Thread(target=blink_led, args = (GPIO_LED,))
        tblink.start()

        # Reading time from GPS if connected and configured
        if len(gpsSensors) >= 1:
            tgpstimesync.join(timeout=25)
            if tgpstimesync.is_alive():
                logger.warning("Thread to syncronize time with GPS is still not finished!")

        # Reading time from NTP Servers if connected to network
        if settings["offline"] != 3:
            ttimesync.join(timeout=25)
            if ttimesync.is_alive():
                logger.warning("Thread to syncronize time with NTP Server is still not finished!")

        if (not is_system_datetime_valid()):
            if len(gpsSensors) >= 1 and tgpstimesync.is_alive():
                logger.critical("Systemtime is still invalid! Waiting another 35 seconds for Thread to syncronize time with GPS")
                tgpstimesync.join(timeout=35)
                if tgpstimesync.is_alive():
                    logger.warning("Thread to syncronize time with GPS is still not finished!")
            elif settings["offline"] != 3 and ttimesync.is_alive():
                logger.critical("Systemtime is still invalid! Waiting another 35 seconds for Thread to syncronize time with NTP Servers")
                ttimesync.join(timeout=35)
                if ttimesync.is_alive():
                    logger.warning("Thread to syncronize time with NTP Server is still not finished!")
            else:
                logger.critical("All options to synchonize time failed and systemtime is still invalid")

        # start as seperate background thread
        # because Taster pressing was not recognised
        measurement = threading.Thread(target=start_measurement, args=(measurement_stop,))
        measurement.start() # start measurement

        # Main Lopp: Cancel with STRG+C
        while True:
            time.sleep(0.2)  # wait 200 ms to give CPU chance to do other things
            pass

        print("This text will never be printed.")

    except Exception as ex:
        logger.critical("Unhandled Exception in main: " + repr(ex))
        if not debug:
            time.sleep(60)
            reboot(settings)

if __name__ == '__main__':
    try:
        main()

    except (KeyboardInterrupt, SystemExit):
        close_script()

    except Exception as ex:
        logger.exception("Unhandled Exception in __main__ ")
