#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import time
from sensors.bme280 import readBME280All # Source: http://bit.ly/bme280py
from sensors.sensor_utilities import computeAbsoluteHumidity
import logging

logger = logging.getLogger('HoneyPi.read_bme280')

def measure_bme280(ts_sensor):
    fields = {}

    i2c_addr = 0x76 # default value
    offset = 0

    try:
        if 'i2c_addr' in ts_sensor and ts_sensor["i2c_addr"] is not None:
            i2c_addr = int(ts_sensor["i2c_addr"],0)
    except Exception as ex:
        logger.error("Error getting I2C Adress, using default: '" + str(i2c_addr))

    try:
        logger.debug("Reading on  I2C Adress " + format(i2c_addr, "x"))
        temperature,pressure,humidity = readBME280All(i2c_addr)


        # ThingSpeak fields
        # Create returned dict if ts-field is defined
        if 'ts_field_temperature' in ts_sensor and isinstance(temperature, (int, float)):
            if 'offset' in ts_sensor and ts_sensor["offset"] is not None:
                offset = float(ts_sensor["offset"])
                temperature = temperature-offset
            fields[ts_sensor["ts_field_temperature"]] = round(temperature, 1)
        if 'ts_field_humidity' in ts_sensor and isinstance(humidity, (int, float)):
            fields[ts_sensor["ts_field_humidity"]] = round(humidity, 1)
        if 'ts_field_absolutehumidity' in ts_sensor and isinstance(humidity, (int, float)) and isinstance(temperature, (int, float)):
            absoluteHumidity = computeAbsoluteHumidity(humidity, temperature)
            fields[ts_sensor["ts_field_absolutehumidity"]] = absoluteHumidity
        if 'ts_field_air_pressure' in ts_sensor and isinstance(pressure, (int, float)):
            fields[ts_sensor["ts_field_air_pressure"]] = round(pressure, 1)
    except IOError as ex:
        if str(ex) == "[Errno 121] Remote I/O error":
            logger.error("Could not access BME280 Sensor on I2C Adress " + format(i2c_addr, "x") + "!")
        else:
            logger.exception("IOError in measure_bme280")
    except OSError:
            logger.exception("OSError in measure_bme280")
    except Exception as ex:
        logger.exception("Unhandled Exception in measure_bme280")

    return fields
