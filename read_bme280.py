#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import time
from sensors.bme280 import readBME280All # Source: http://bit.ly/bme280py
import logging

logger = logging.getLogger('HoneyPi.read_bme280')

def measure_bme280(ts_sensor):
    fields = {}

    i2c_addr = 0x76 # default value
    offset = 0

    try:
        if 'i2c_addr' in ts_sensor:
            i2c_addr = ts_sensor["i2c_addr"]

            if i2c_addr == "0x76":
                i2c_addr = 0x76
            elif i2c_addr == "0x77":
                i2c_addr = 0x77
            else:
                logger.warning("Undefined BME280 I2C Address '" + str(i2c_addr) + "'")

    except Exception as ex:
        logger.error("Error getting I2C Adress, using default: '" + str(i2c_addr))

    try:
        temperature,pressure,humidity = readBME280All(i2c_addr)

        # ThingSpeak fields
        # Create returned dict if ts-field is defined
        if 'ts_field_temperature' in ts_sensor and isinstance(temperature, (int, float)):
            if 'offset' in ts_sensor and ts_sensor["offset"] is not None:
                offset = float(ts_sensor["offset"])
                temperature = temperature-offset
            fields[ts_sensor["ts_field_temperature"]] = round(temperature, 2)
        if 'ts_field_humidity' in ts_sensor and isinstance(humidity, (int, float)):
            fields[ts_sensor["ts_field_humidity"]] = round(humidity, 2)
        if 'ts_field_air_pressure' in ts_sensor and isinstance(pressure, (int, float)):
            fields[ts_sensor["ts_field_air_pressure"]] = round(pressure, 2)
    except OSError:
        logger.error("No BME280 Sensor connected on I2C Adress.")
    except Exception as ex:
        logger.exception("Unhandled Exception in measure_bme280")

    return fields
