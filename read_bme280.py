#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import time
from bme280 import readBME280All #http://bit.ly/bme280py

# global vars

def measure_bme280(ts_sensor):
    fields = {}
    try:
        temperature,pressure,humidity = readBME280All()

        # ThingSpeak fields
        # Create returned dict if ts-field is defined
        if 'ts_field_temperature' in ts_sensor:
            fields[ts_sensor["ts_field_temperature"]] = round(temperature,2)
        if 'ts_field_humidity' in ts_sensor:
            fields[ts_sensor["ts_field_humidity"]] = round(humidity,2)
        if 'ts_field_air_pressure' in ts_sensor:
            fields[ts_sensor["ts_field_air_pressure"]] = round(pressure,2)
    except OSError:
        print('No BME280 Sensor connected')

    return fields
