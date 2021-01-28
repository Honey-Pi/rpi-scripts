#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import time
from sensors.bme280 import readBME280All # Source: http://bit.ly/bme280py
import logging

logger = logging.getLogger('HoneyPi.read_bme280')

def measure_bme280(ts_sensor):
    fields = {}
    i2c_addr = "0x76" # default value
    try:
        # setup BME280 sensor
        try:
            if 'i2c_addr' in ts_sensor:
                i2c_addr = ts_sensor["i2c_addr"]

                if i2c_addr == "0x76":
                    logger.debug("'BME680 on I2C Adress '" + i2c_addr + "'")
                elif i2c_addr == "0x77":
                    logger.debug("'BME680 on I2C Adress '" + i2c_addr + "'")

        except Exception as ex:
            logger.exception("Error getting  I2C Adress, using default '" + i2c_addr + "'" + repr(ex))
            pass

        try:
            offset = float(ts_sensor["offset"])
            logger.debug("'BME280 on I2C Adress '" + i2c_addr + "': The Temperature Offset is " + str(offset) + " °C")
        except:
            offset = 0
            logger.exception("'BME280 on I2C Adress '" + i2c_addr + "', no offset in configurtation")
            pass

        temperature,pressure,humidity = readBME280All(i2c_addr)

        # ThingSpeak fields
        # Create returned dict if ts-field is defined
        if 'ts_field_temperature' in ts_sensor and isinstance(temperature, (int, float)):
            if 'offset' in ts_sensor and ts_sensor["offset"] is not None:
                temperature = temperature-ts_sensor["offset"]
            fields[ts_sensor["ts_field_temperature"]] = round(temperature, 2)
        if 'ts_field_humidity' in ts_sensor and isinstance(humidity, (int, float)):
            fields[ts_sensor["ts_field_humidity"]] = round(humidity, 2)
        if 'ts_field_air_pressure' in ts_sensor and isinstance(pressure, (int, float)):
            fields[ts_sensor["ts_field_air_pressure"]] = round(pressure, 2)
    except OSError:
        logger.exception("No BME280 Sensor connected on I2C Adress '" + i2c_addr + "'")
    except Exception as ex:
        logger.exception("Unhandled Exception in measure_bme280 " + repr(ex))

    return fields
