#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.
# Modified for sensor test

import math
import threading
from datetime import datetime
import time
import json

from read_settings import get_settings, get_sensors
from utilities import ap_to_client_mode, stop_led
from OLed import oled_off
from constant import GPIO_LED, timeToStopMaintenance
import superglobal

import RPi.GPIO as GPIO

from read_hx711 import measure_hx711
from constant import logfile, scriptsFolder

import logging

logger = logging.getLogger('HoneyPi.maintenance')

superglobal = superglobal.SuperGlobal()


def maintenance(maintenance_stop, measurement_stop):
    try:
        settings = get_settings()
        #measurementIsRunning.value = 1 # set flag
        timeMaintenanceStarted = datetime.now()
        datetime_now = timeMaintenanceStarted
        logger.debug('Maintenance mode started at: ' + timeMaintenanceStarted.strftime('%Y-%m-%d %H:%M'))
        #logger.debug('Now we measure the hx to determine start values')
        while not maintenance_stop.is_set():
            datetime_now = datetime.now()
            timeInMaintenance = datetime_now-timeMaintenanceStarted
            isTimeToStopMaintenance = (timeInMaintenance.total_seconds() >= timeToStopMaintenance)
            if isTimeToStopMaintenance:
                logger.warning('Automatically stopping Maintenance Mode as it was exeeding maxiumum runtime of ' + str (timeToStopMaintenance) + 'seconds')
                maintenance_stop.set()
                measurement_stop.clear()
            time.sleep(1)
        #logger.debug('Now we measure the hx again to determine end values')
        logger.debug('Maintenance mode ended at: ' + timeMaintenanceStarted.strftime('%Y-%m-%d %H:%M'))
        t2 = threading.Thread(target=ap_to_client_mode)
        t2.start()
        t2.join(timeout=30)
        superglobal.isMaintenanceActive = False # measurement shall stop next time
        stop_led(GPIO_LED)
        if settings['display']['enabled']:
            oled_off()
    except Exception as ex:
        logger.exception("Unhandled Exception in maintenance")

if __name__ == '__main__':
    try:
        start_maintenance()

    except (KeyboardInterrupt, SystemExit):
        pass

    except Exception as ex:
        logger.exception("Unhandled Exception in direct maintenance __main__")
