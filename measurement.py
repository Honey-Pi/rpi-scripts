#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import math
import threading
import time
from pprint import pprint
from time import sleep
import json

import RPi.GPIO as GPIO

from read_bme680 import measure_bme680, initBME680FromMain
from read_bme280 import measure_bme280
from read_pcf8591 import measure_voltage
from read_ds18b20 import measure_temperature
from read_hx711 import measure_weight, compensate_temperature
from read_dht import measure_dht
from read_max import measure_tc
from read_settings import get_settings, get_sensors
from utilities import reboot, start_single, stop_single

def measurement():
    try:
        # load settings
        settings = get_settings()
        # read configured sensors from settings.json
        ds18b20Sensors = get_sensors(settings, 0)
        bme680Sensors = get_sensors(settings, 1)
        weightSensors = get_sensors(settings, 2)
        dhtSensors = get_sensors(settings, 3)
        tcSensors = get_sensors(settings, 4)
        bme280Sensors = get_sensors(settings, 5)
        voltageSensors = get_sensors(settings, 6)

        # if bme680 is configured
        if bme680Sensors and len(bme680Sensors) == 1:
            bme680IsInitialized = initBME680FromMain(bme680Sensors)
        else:
            bme680IsInitialized = 0

        # dict with all fields and values which will be tranfered to ThingSpeak later
        ts_fields = {}

        # measure every sensor with type 0
        for (sensorIndex, sensor) in enumerate(ds18b20Sensors):
            if 'ts_field' in sensor and 'device_id' in sensor:
                ts_field_ds18b20 = sensor["ts_field"]
                ds18b20_temperature = measure_temperature(sensor["device_id"])
                ts_fields.update({ts_field_ds18b20: ds18b20_temperature})
            else:
                print("DS18b20 missing param: ts_field or device_id")

        # measure BME680 (can only be one) [type 1]
        if bme680Sensors and len(bme680Sensors) == 1 and bme680IsInitialized:
            bme680_values = measure_bme680(bme680Sensors[0], 10)
            ts_fields.update(bme680_values)

        # measure every sensor with type 3 [DHT11/DHT22]
        for (i, sensor) in enumerate(dhtSensors):
            tempAndHum = measure_dht(sensor)
            ts_fields.update(tempAndHum)

        # measure every sensor with type 4 [MAX6675]
        for (i, sensor) in enumerate(tcSensors):
            tc_temp = measure_tc(sensor)
            ts_fields.update(tc_temp)

        # measure BME280 (can only be one) [type 5]
        if bme280Sensors and len(bme280Sensors) == 1:
            bme280_values = measure_bme280(bme280Sensors[0])
            ts_fields.update(bme280_values)

        # measure YL-40 PFC8591 (can only be one) [type 6]
        if voltageSensors and len(voltageSensors) == 1:
            voltage = measure_voltage(voltageSensors[0])
            ts_fields.update(voltage)

        start_single()
        # measure every sensor with type 2 [HX711]
        for (i, sensor) in enumerate(weightSensors):
            weight = measure_weight(sensor)
            weight = compensate_temperature(sensor, weight, ts_fields)
            ts_fields.update(weight)
        stop_single()

        return json.dumps(ts_fields)

    except Exception as e:
        print("Measurement: " + str(e))

    # Error occured
    return {}

try:
    print(measurement())
except KeyboardInterrupt:
    pass
