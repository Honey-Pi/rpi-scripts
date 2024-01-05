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
from utilities import ap_to_client_mode, stop_led, start_single, stop_single
from OLed import oled_off
from constant import GPIO_LED
import superglobal

import RPi.GPIO as GPIO

from read_hx711 import measure_weight
from constant import logfile, scriptsFolder

import logging

logger = logging.getLogger('HoneyPi.maintenance')

superglobal = superglobal.SuperGlobal()


def maintenance(maintenance_stop, measurement_stop):
    try:
        settings = get_settings()
        if 'led_pin' in settings:
            GPIO_LED = settings["led_pin"]
        timeToStopMaintenance = settings['timeToStopMaintenance']

        weightSensors = get_sensors(settings, 2)
        weightSensorsatStartMaintenance = weightSensors
        timeMaintenanceStarted = datetime.now()
        datetime_now = timeMaintenanceStarted
        logger.info('Maintenance mode started at: ' + timeMaintenanceStarted.strftime('%Y-%m-%d %H:%M'))
        logger.debug('Now we measure the hx to determine start values')
        weightbefore = []
        weightafter = []
        start_single()
        for (i, weight_sensor) in enumerate(weightSensors):
            weight=measure_weight(weight_sensor)
            weightbefore.append(weight)
            pin_dt = int(weight_sensor["pin_dt"])
            pin_sck = int(weight_sensor["pin_sck"])
            channel = weight_sensor["channel"]
            reference_unit = float(weight_sensor["reference_unit"])
            offset = int(weight_sensor["offset"])
            logger.debug('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel +  ' weight: ' + str(weightbefore[i]) + 'g when maintenance mode was started')
        stop_single()

        while not maintenance_stop.is_set():
            datetime_now = datetime.now()
            timeInMaintenance = datetime_now-timeMaintenanceStarted
            isTimeToStopMaintenance = (timeInMaintenance.total_seconds() >= timeToStopMaintenance)
            if isTimeToStopMaintenance:
                logger.warning('Automatically stopping Maintenance Mode as it was exeeding maxiumum runtime of ' + str (timeToStopMaintenance) + 'seconds')
                maintenance_stop.set()
                measurement_stop.clear()
            time.sleep(1)

        logger.debug('Now we measure the hx again to determine end values')
        start_single()
        for (i, weight_sensor) in enumerate(weightSensors):
            weight=measure_weight(weight_sensor)
            weightafter.append(weight)
            pin_dt = int(weight_sensor["pin_dt"])
            pin_sck = int(weight_sensor["pin_sck"])
            channel = weight_sensor["channel"]
            reference_unit = float(weight_sensor["reference_unit"])
            offset = int(weight_sensor["offset"])
            #if (weight_sensor["reference_unit"] == weightSensorsatStartMaintenance[i]["reference_unit"] and weight_sensor["offset"] == weightSensorsatStartMaintenance[i]["offset"]):
            logger.info('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel +  ' weight before: ' + str(weightbefore[i]) + 'g -  weight after: ' + str(weightafter[i]) + 'g , a difference of ' + str(int(weightafter[i]-weightbefore[i])) + 'g when maintenance mode was ended')
            #Neues offset berechnen : weight_sensor["offset2"]+(weightafter[i]-weightbefore[i])
            #else:
            #logger.warning('Calibration during maintenance for HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel)
            #eventuell aus weightSensorsatStartMaintenance[i] die differenz berechnen
        stop_single()

        logger.info('Maintenance mode ended at: ' + timeMaintenanceStarted.strftime('%Y-%m-%d %H:%M'))
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
