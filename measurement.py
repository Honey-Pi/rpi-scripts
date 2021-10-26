#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.
# Modified for sensor test

import math
import threading
import time
from pprint import pprint
from time import sleep
import json

import RPi.GPIO as GPIO

from read_bme680 import measure_bme680, initBME680FromMain, burn_in_bme680, burn_in_time
from read_bme280 import measure_bme280
from read_ee895 import measure_ee895
from read_pcf8591 import measure_pcf8591
from read_ds18b20 import measure_temperature, filter_temperatur_values
from read_hx711 import measure_hx711
from read_dht import measure_dht
from read_dht_zero import measure_dht_zero
from read_aht10 import measure_aht10
from read_sht31 import measure_sht31
from read_hdc1008 import measure_hdc1008
from read_bh1750 import measure_bh1750
from read_max import measure_tc
from read_settings import get_settings, get_sensors
from utilities import logfile, start_single, stop_single, scriptsFolder, is_zero

import logging

logger = logging.getLogger('HoneyPi.measurement')

def measure_all_sensors(debug, filtered_temperature, ds18b20Sensors, bme680Sensors, bme680Inits, dhtSensors, aht10Sensors, sht31Sensors, hdc1008Sensors, bh1750Sensors, tcSensors, bme280Sensors, pcf8591Sensors, ee895Sensors, weightSensors, hxInits):

    ts_fields = {} # dict with all fields and values which will be tranfered to ThingSpeak later
    global burn_in_time
    try:

        logger.debug("Measurement for all configured sensors started...")
        try:
            # measure every sensor with type 0 (Ds18b20)
            for (sensorIndex, sensor) in enumerate(ds18b20Sensors):
                filter_temperatur_values(sensorIndex)
        except Exception as ex:
           logger.exception("Unhandled Exception in measure_all_sensors / ds18b20Sensors filter_temperatur_values")

        try:
            for (sensorIndex, sensor) in enumerate(ds18b20Sensors):
                if filtered_temperature is not None and len(filtered_temperature[sensorIndex]) > 0 and 'ts_field' in sensor:
                    # if we have at leat one filtered value we can upload
                    ds18b20_temperature = filtered_temperature[sensorIndex].pop()
                    if sensor["ts_field"] and ds18b20_temperature is not None:
                        if 'offset' in sensor and sensor["offset"] is not None:
                            ds18b20_temperature = ds18b20_temperature-float(sensor["offset"])
                        ds18b20_temperature = float("{0:.2f}".format(ds18b20_temperature)) # round to two decimals
                        ts_fields.update({sensor["ts_field"]: ds18b20_temperature})
                elif 'ts_field' in sensor:
                    # Case for filtered_temperature was not filled, use direct measured temperture in this case
                    ds18b20_temperature = measure_temperature(sensor)
                    if sensor["ts_field"] and ds18b20_temperature is not None:
                        if 'offset' in sensor and sensor["offset"] is not None:
                            ds18b20_temperature = ds18b20_temperature-float(sensor["offset"])
                        ds18b20_temperature = float("{0:.2f}".format(ds18b20_temperature)) # round to two decimals
                        ts_fields.update({sensor["ts_field"]: ds18b20_temperature})
        except Exception as ex:
            logger.exception("Unhandled Exception in measure_all_sensors / ds18b20Sensors")

        # measure BME680 (can only be two) [type 1]
        for (sensorIndex, bme680Sensor) in enumerate(bme680Sensors):
            if bme680Inits[sensorIndex] != None:
                bme680Init = bme680Inits[sensorIndex]
                sensor = bme680Init['sensor']
                gas_baseline = bme680Init['gas_baseline']
                bme680_values, gas_baseline = measure_bme680(sensor, gas_baseline, bme680Sensor, burn_in_time)
                ts_fields.update(bme680_values)
                bme680Init['gas_baseline'] = gas_baseline
                bme680Inits[sensorIndex]=bme680Init

        # measure every sensor with type 3 [DHT11/DHT22]
        for (i, sensor) in enumerate(dhtSensors):
            if is_zero():
                tempAndHum = measure_dht_zero(sensor)
            else:
                tempAndHum = measure_dht(sensor)
            ts_fields.update(tempAndHum)

        # measure every sensor with type 4 [MAX6675]
        for (i, sensor) in enumerate(tcSensors):
            tc_temp = measure_tc(sensor)
            ts_fields.update(tc_temp)

        # measure BME280 (can only be two) [type 5]
        for (sensorIndex, bme280Sensor) in enumerate(bme280Sensors):
            bme280_values = measure_bme280(bme280Sensor)
            if bme280_values is not None:
                ts_fields.update(bme280_values)

        # measure PCF8591 [type 6]
        for (i, sensor) in enumerate(pcf8591Sensors):
            pcf8591_values = measure_pcf8591(sensor)
            if pcf8591_values is not None:
                ts_fields.update(pcf8591_values)

        # measure EE895 (can only be one) [type 7]
        if ee895Sensors and len(ee895Sensors) == 1:
            ee895_values = measure_ee895(ee895Sensors[0])
            if ee895_values is not None:
                ts_fields.update(ee895_values)

        # measure AHT10 (can only be one) [type 8]
        if aht10Sensors and len(aht10Sensors) == 1:
            aht10_fields = measure_aht10(aht10Sensors[0])
            if aht10_fields is not None:
                ts_fields.update(aht10_fields)

        # measure sht31 (can only be one) [type 9]
        if sht31Sensors and len(sht31Sensors) == 1:
            sht31_fields = measure_sht31(sht31Sensors[0])
            if sht31_fields is not None:
                ts_fields.update(sht31_fields)

        # measure hdc1008 (can only be one) [type 10]
        if hdc1008Sensors and len(hdc1008Sensors) == 1:
            hdc1008_fields = measure_hdc1008(hdc1008Sensors[0])
            if hdc1008_fields is not None:
                ts_fields.update(hdc1008_fields)

        # measure bh1750 (can only be one) [type 11]
        if bh1750Sensors and len(bh1750Sensors) == 1:
            bh1750_fields = measure_bh1750(bh1750Sensors[0])
            if bh1750_fields is not None:
                ts_fields.update(bh1750_fields)

        # measure every sensor with type 2 [HX711]
        start_single()
        for (i, sensor) in enumerate(weightSensors):
            if hxInits is not None:
                hx711_fields = measure_hx711(sensor, ts_fields, hxInits[i])
                # hx711_fields = compensate_temperature(sensor, weight, ts_fields)
                ts_fields.update(hx711_fields)
            else:
                hx711_fields = measure_hx711(sensor, ts_fields)
                # hx711_fields = compensate_temperature(sensor, weight, ts_fields)
                ts_fields.update(hx711_fields)
        stop_single()

        # print all measurement values stored in ts_fields
        logger.debug("Measurement for all configured sensors finished...")

        if debug:
            ts_fields_content = ""
            for key, value in ts_fields.items():
                ts_fields_content = ts_fields_content + key + ": " + str(value) + " "
            logger.debug(ts_fields_content)
        return ts_fields, bme680Inits
    except Exception as ex:
        logger.exception("Unhandled Exception in measure_all_sensors")
        return ts_fields, bme680Inits

def measurement():
    # dict with all fields and values which will be tranfered to ThingSpeak later
    ts_fields = {}
    global burn_in_time
    try:

        # read settings
        settings = get_settings()

        debuglevel=int(settings["debuglevel"])
        debuglevel_logfile=int(settings["debuglevel_logfile"])

        logger = logging.getLogger('HoneyPi.measurement')
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(logfile)
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

        logger.info('Direct measurement started from webinterface.')

        # read configured sensors from settings.json
        ds18b20Sensors = get_sensors(settings, 0)
        bme680Sensors = get_sensors(settings, 1)
        weightSensors = get_sensors(settings, 2)
        dhtSensors = get_sensors(settings, 3)
        tcSensors = get_sensors(settings, 4)
        bme280Sensors = get_sensors(settings, 5)
        pcf8591Sensors = get_sensors(settings, 6)
        ee895Sensors = get_sensors(settings, 7)
        hdc1008Sensors = get_sensors(settings, 8)
        sht31Sensors = get_sensors(settings, 9)
        aht10Sensors = get_sensors(settings, 10)
        bh1750Sensors = get_sensors(settings, 11)
        bme680Inits = []

        # -- Run Pre Configuration --
        # if bme680 is configured
        for (sensorIndex, bme680Sensor) in enumerate(bme680Sensors):
            bme680Init = {}
            if 'burn_in_time' in bme680Sensor:
                burn_in_time = bme680Sensor["burn_in_time"]
            sensor = initBME680FromMain(bme680Sensor)
            bme680Init['sensor'] = sensor
            if 'ts_field_air_quality' in bme680Sensor:
                gas_baseline = burn_in_bme680(sensor, burn_in_time)
            else:
                gas_baseline = None
            bme680Init['gas_baseline'] = gas_baseline
            bme680Inits.append(bme680Init)

        ts_fields, bme680Inits = measure_all_sensors(False, None, ds18b20Sensors, bme680Sensors, bme680Inits, dhtSensors, aht10Sensors, sht31Sensors, hdc1008Sensors, bh1750Sensors, tcSensors, bme280Sensors, pcf8591Sensors, ee895Sensors, weightSensors, None)

    except Exception as ex:
        logger.exception("Unhandled Exception in direct measurement")

    return json.dumps(ts_fields)

if __name__ == '__main__':
    try:
        print(measurement())

    except (KeyboardInterrupt, SystemExit):
        pass

    except Exception as ex:
        logger.exception("Unhandled Exception in direct measurement __main__")
