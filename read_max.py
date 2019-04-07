#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

from MAX6675 import MAX6675
from MAX31855 import MAX31855
import RPi.GPIO as GPIO

def measure_tc(tc_sensor):
    # get sensor pins
    pin_cs = 26
    pin_clock = 18
    pin_miso = 19
    max_type = 6675
    try:
        pin_cs = int(tc_sensor["pin_cs"])
        pin_clock = int(tc_sensor["pin_clock"])
        pin_miso = int(tc_sensor["pin"])
        max_type = int(tc_sensor["max_type"])
    except Exception as e:
        print("MAX6675/MAX31855 missing param: " + str(e))

    tc_temperature = 0

    # setup tc-Sensor
    try:
        tc = None
        if max_type == 6675:
            tc = MAX6675(cs_pin = pin_cs, clock_pin = pin_clock, data_pin = pin_miso, units = "c", board = GPIO.BCM)
        elif max_type == 31855:
            tc = MAX31855(cs_pin = pin_cs, clock_pin = pin_clock, data_pin = pin_miso, units = "c", board = GPIO.BCM)

    except Exception as e:
        print("Init MAX6675/MAX31855 failed " + str(e))

    if tc is not None:
        try:
            # get data
            tc_temperature = tc.get()

            if 'offset' in tc_sensor:
                offset = float(tc_sensor["offset"])
                tc_temperature = tc_temperature-offset
            tc_temperature = float('%6.2f' % tc_temperature)

        except Exception as e:
            print("Reading MAX6675/MAX31855 failed: " + str(e))

        if 'ts_field' in tc_sensor:
            return ({tc_sensor["ts_field"]: tc_temperature})
    return {}