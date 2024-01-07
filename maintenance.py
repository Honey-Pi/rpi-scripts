#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.
# Modified for sensor test

import math
import threading
from datetime import datetime
import time
import json

from read_settings import get_settings, get_sensors, write_settings
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
        weightSensorsatStartMaintenance = []
        timeMaintenanceStarted = datetime.now()
        datetime_now = timeMaintenanceStarted
        logger.info('Maintenance mode started at: ' + timeMaintenanceStarted.strftime('%Y-%m-%d %H:%M'))
        logger.debug('Now we measure the hx to determine start values')
        #weightbefore = []
        #weightafter = []
        start_single()
        for (i, weight_sensor) in enumerate(weightSensors):
            weight=measure_weight(weight_sensor)
            weight_sensor["weightbefore"] = weight
            pin_dt = int(weight_sensor["pin_dt"])
            pin_sck = int(weight_sensor["pin_sck"])
            channel = weight_sensor["channel"]
            reference_unit = float(weight_sensor["reference_unit"])
            offset = int(weight_sensor["offset"])
            logger.debug('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel +  ' weight: ' + str(weight) + 'g when maintenance mode was started')
            weightSensorsatStartMaintenance.append(weight_sensor)
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
        settings = get_settings()
        #weightSensors = get_sensors(settings, 2)
        #for (i, weight_sensor) in enumerate(weightSensors):
        sensors = []
        try:
            sensors = settings["sensors"]
        except:
        # Key doesn't exist => keep empty array
            pass
        for i, sensor in enumerate(sensors):
            if "type" in sensor and sensor["type"] == 2:
                weight=measure_weight(sensor)
                #weightafter.append(weight)
                pin_dt = int(sensor["pin_dt"])
                pin_sck = int(sensor["pin_sck"])
                channel = sensor["channel"]
                reference_unit = float(sensor["reference_unit"])
                offset = int(sensor["offset"])
                offset2 = 0
                newoffset2 = 0
                startoffset2 = 0
                for j, weight_sensor in enumerate(weightSensorsatStartMaintenance):
                    if sensor["pin_dt"] == weight_sensor["pin_dt"] and sensor["pin_sck"] == weight_sensor["pin_sck"] and sensor["channel"] == weight_sensor["channel"]: #searching same sensor in config
                        if "offset2" in weight_sensor and type(weight_sensor["offset2"]) == int:
                            startoffset2 = weight_sensor["offset2"]
                        if "offset2" in sensor and type(sensor["offset2"]) == int:
                            offset2 = sensor["offset2"]
                        weightdifference = float(0 if weight is None else weight) - float(0 if weight_sensor["weightbefore"] is None else weight_sensor["weightbefore"])
                        newoffset2 = startoffset2 + int(round(weightdifference/10,0)*10)
                        if weight_sensor["reference_unit"] == sensor["reference_unit"] and weight_sensor["offset"] == sensor["offset"]:
                            if (offset2 == startoffset2):
                                if (offset2 == newoffset2):
                                    logger.info('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel +  ' weight before: ' + str(weight_sensor["weightbefore"]) + 'g -  weight after: ' + str(weight) + 'g , a difference of ' + str(float("{0:.1f}".format(weightdifference))) + 'g when maintenance mode was ended, no significant weight change, not updating offset2')
                                else:
                                    logger.info('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel +  ' weight before: ' + str(weight_sensor["weightbefore"]) + 'g -  weight after: ' + str(weight) + 'g , a difference of ' + str(float("{0:.1f}".format(weightdifference))) + 'g when maintenance mode was ended, updateing offset2 from ' + str(startoffset2) +'g  to: ' + str(newoffset2) + 'g')
                                    sensor["offset2"]=newoffset2
                                    sensors[i] = sensor
                                    settings["sensors"] = sensors
                                    write_settings(settings)
                            else:
                                logger.warning('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel +  ' weight before: ' + str(weight_sensor["weightbefore"]) + 'g -  weight after: ' + str(weight) + 'g , a difference of ' + str(float("{0:.1f}".format(weightdifference))) + 'g when maintenance mode was ended, not updateing offset2 to: ' + str(newoffset2) + 'g but keeping new value: ' + str(offset2) + 'g that was changed in maintenance mode from: '+ str(startoffset2))
                        else:
                            logger.warning('reference_unit changed from' + str(weight_sensor["reference_unit"]) + ' to: ' + str(sensor["reference_unit"]) + ', offset changed from: ' + str(weight_sensor["offset"]) + ' to: ' + str(sensor["offset"]))
                            logger.warning('Calibration during maintenance for HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ', not calculation a new offset')
                            #eventuell aus weight_sensor die differenz berechnen
                        break
                    else:
                        logger.debug("Another sensor")
                        continue
                    logger.warning('Sensor HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + 'did not exist at start of Maintenance!')
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
