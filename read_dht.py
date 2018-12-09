#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import Adafruit_DHT

def measure_dht(ts_sensor):
    pin = ts_sensor["pin"]
    dht_type = ts_sensor["dht_type"]
    ts_field_temperature = ts_sensor["ts_field_temperature"]
    ts_field_humidity = ts_sensor["ts_field_humidity"]

    humidity, temperature = None
    fields = {}

    if dht_type is not None and pin:
        # setup sensor
        sensorDHT = dht_type # Adafruit_DHT.DHT22
        try:
            humidity, temperature = Adafruit_DHT.read_retry(sensorDHT, pin)
        except:
            print("Reading DHT failed (" + dht_type + ").")

        # Create returned dict if ts-field is defined
        
        if ts_field_temperature and temperature is not None:
            fields[ts_field_temperature] = temperature
        if ts_field_humidity and humidity is not None:
            fields[ts_field_humidity] = humidity

    else:
        print("DHT type or PIN is not defined.")

    return fields