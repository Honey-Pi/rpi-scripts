#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import math
import threading
import time
from pprint import pprint
from time import sleep
import json

import RPi.GPIO as GPIO

from read_bme680 import measure_bme680, burn_in_bme680, initBME680FromMain
from read_ds18b20 import measure_temperature
from read_hx711 import measure_weight
from read_dht import measure_dht
from read_max6675 import measure_tc
from read_settings import get_settings, get_sensors
from utilities import reboot, error_log

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

        # if bme680 is configured
        if bme680Sensors and len(bme680Sensors) == 1:
            gas_baseline = None
            if initBME680FromMain():
                # bme680 sensor must be burned in before use
                gas_baseline = burn_in_bme680(10)

                # if burning was canceled => exit
                if gas_baseline is None:
                    print("gas_baseline can't be None")

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

        # measure BME680 (can only be once) [type 1]
        if bme680Sensors and len(bme680Sensors) == 1 and gas_baseline:
            bme680_values = measure_bme680(gas_baseline, bme680Sensors[0])
            ts_fields.update(bme680_values)

        # disable warnings for HX711
        GPIO.setwarnings(False)
        
        # measure every sensor with type 2 [HX711]
        for (i, sensor) in enumerate(weightSensors):
            weight = measure_weight(sensor)
            ts_fields.update(weight)

        # measure every sensor with type 3 [DHT11/DHT22]
        for (i, sensor) in enumerate(dhtSensors):
            tempAndHum = measure_dht(sensor)
            ts_fields.update(tempAndHum)

        # measure every sensor with type 4 [MAX6675]
        for (i, sensor) in enumerate(tcSensors):
            tc_temp = measure_tc(sensor)
            ts_fields.update(tc_temp)

        return json.dumps(ts_fields)
           
    except Exception as e:
        print("Measurement: " + str(e))


print measurement()
