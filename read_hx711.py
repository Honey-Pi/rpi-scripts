#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

from HX711 import HX711

def measure_weight(weight_sensor):
    # weight sensor pins
    try:
        pin_dt = weight_sensor["pin_dt"]
        pin_sck = weight_sensor["pin_sck"]
        channel = weight_sensor["channel"]
        ts_field = weight_sensor["ts_field"]
    except Exception as e:
        print("HX711 missing params: " + str(e))
    
    if weight_sensor["reference_unit"]:
        reference_unit = weight_sensor["reference_unit"]
    else:
        reference_unit = 1
    if weight_sensor["offset"]:
        offset = weight_sensor["offset"]
    else:
        offset = 0

    weight = 0

    # setup weight sensor
    try:
        hx = HX711(dout_pin=pin_dt, pd_sck_pin=pin_sck, gain_channel_A=128, select_channel=channel)

        hx.set_scale_ratio(scale_ratio=reference_unit)
        hx.set_offset(offset=offset)

        weight = hx.get_weight_mean(5) # average from 5 times
        weight = weight/1000  # gramms to kg
        weight = float("{0:.3f}".format(weight)) # float only 3 decimals
    except Exception as e:
        print("Reading HX711 failed: " + str(e))

    return ({ts_field: weight})