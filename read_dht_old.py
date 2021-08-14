#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.


# This file is deprecated and not used because the Adafruit_DHT does not work with Raspberry Pi OS. (see: https://stackoverflow.com/a/66007330/6696623)

import Adafruit_DHT
import os
import logging
os.environ['PYTHON_EGG_CACHE'] = '/usr/local/pylons/python-eggs'

logger = logging.getLogger('HoneyPi.read_dht_old')

def measure_dht(ts_sensor):
    fields = {}

    try:
        pin = int(ts_sensor["pin"])
        dht_type = int(ts_sensor["dht_type"])

        # setup sensor
        if dht_type == 2302:
            sensorDHT = Adafruit_DHT.AM2302
        elif dht_type == 11:
            sensorDHT = Adafruit_DHT.DHT11
        else:
            sensorDHT = Adafruit_DHT.DHT22

    except Exception as ex1:
        logger.error("DHT missing param: " + repr(ex1))

    try:
        humidity, temperature = Adafruit_DHT.read_retry(sensorDHT, pin)

        # Create returned dict if ts-field is defined
        if 'ts_field_temperature' in ts_sensor and temperature is not None:
            if 'offset' in ts_sensor and ts_sensor["offset"] is not None:
                temperature = temperature-float(ts_sensor["offset"])
            fields[ts_sensor["ts_field_temperature"]] = round(temperature, 1)
        if 'ts_field_humidity' in ts_sensor and humidity is not None:
            fields[ts_sensor["ts_field_humidity"]] = round(humidity, 1)

    except Exception as ex:
        logger.exception("Reading DHT failed. DHT: " + str(dht_type) + " " + str(sensorDHT) + ", GPIO: " + str(pin))

    return fields
