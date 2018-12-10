#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import Adafruit_DHT
import os
os.environ['PYTHON_EGG_CACHE'] = '/usr/local/pylons/python-eggs' 

def measure_dht(ts_sensor):
    fields = {}

    try:
        pin = int(ts_sensor["pin"])
        dht_type = int(ts_sensor["dht_type"])
        ts_field_temperature = ts_sensor["ts_field_temperature"]
        ts_field_humidity = ts_sensor["ts_field_humidity"]

        # setup sensor
        if dht_type == 2302:
            sensorDHT = Adafruit_DHT.AM2302
        elif dht_type == 11:
            sensorDHT = Adafruit_DHT.DHT11
        else:
            sensorDHT = Adafruit_DHT.DHT22

        try:
            humidity, temperature = Adafruit_DHT.read_retry(sensorDHT, pin)

            # Create returned dict if ts-field is defined
            if ts_field_temperature:
                fields[ts_field_temperature] = temperature
            if ts_field_humidity:
                fields[ts_field_humidity] = humidity

        except Exception as e:
            print("Reading DHT failed (DHT: " + str(dht_type) + "/" + str(sensorDHT) +", GPIO: " + str(pin) + "): " + str(e))

    except Exception as e:
        print("DHT missing params: " + str(e))
      
    return fields