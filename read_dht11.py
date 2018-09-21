#!/usr/bin/env python
# This file is part of HoneyPi which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import Adafruit_DHT

def measure_dht11(ts_sensor):
    pin = ts_sensor["pin"]
    ts_field_temperature = ts_sensor["ts_field_temperature"]
    ts_field_humidity = ts_sensor["ts_field_humidity"]

    # setup sensor
    sensorDHT = Adafruit_DHT.DHT11
    try:
        humidity, temperature = Adafruit_DHT.read_retry(sensorDHT, pin)
    except:
        print("Reading DHT11 failed")

    # Create returned dict if ts-field is defined
    fields = {}
    if ts_field_temperature:
        fields[ts_field_temperature] = temperature
    if ts_field_humidity:
        fields[ts_field_humidity] = humidity
    return fields