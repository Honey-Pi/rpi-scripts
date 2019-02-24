#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

from HX711 import HX711

def takeClosest(myList, myNumber):
    # from list of integers, get number closest to a given value
    closest = myList[0]
    for i in range(1, len(myList)):
        if abs(myList[i] - myNumber) < closest:
            closest = myList[i]
    return closest

def average(myList):
    # Finding the average of a list
    total = sum(myList)
    total = float(total)
    return total / len(myList)

def measure_weight(weight_sensor):
    # weight sensor pins
    pin_dt = 5
    pin_sck = 6
    channel = 'A'
    try:
        pin_dt = int(weight_sensor["pin_dt"])
        pin_sck = int(weight_sensor["pin_sck"])
        channel = weight_sensor["channel"]   
    except Exception as e:
        print("HX711 missing param: " + str(e))
    
    if 'reference_unit' in weight_sensor:
        reference_unit = weight_sensor["reference_unit"]
    else:
        reference_unit = 1
    if 'offset' in weight_sensor:
        offset = weight_sensor["offset"]
    else:
        offset = 0

    weight = 0

    # setup weight sensor
    try:
        hx = HX711(dout_pin=pin_dt, pd_sck_pin=pin_sck, gain_channel_A=128, select_channel=channel)

        hx.set_scale_ratio(scale_ratio=reference_unit)
        hx.set_offset(offset=offset)

        # improve weight measurement by doing 3 weight measures
        weightMeasures=[]
        for i in range(5):
            weightMeasures.append(hx.get_weight_mean(3))

        # take "best" measure
        average_weight = int(average(weightMeasures))
        weight = takeClosest(weightMeasures, average_weight)
        print("AVG Weight: " + str(average_weight))

        #weight = hx.get_weight_mean(5) # average from 5 times
        if weight is not 0:
            weight = weight/1000  # gramms to kg
        weight = float("{0:.3f}".format(weight)) # float only 3 decimals

        # invert weight if flag is set
        if 'invert' in weight_sensor and weight_sensor['invert'] == True:
            weight = weight*-1;

    except Exception as e:
        print("Reading HX711 failed: " + str(e))

    if 'ts_field' in weight_sensor:
        return ({weight_sensor["ts_field"]: weight})
    else:
        return {}
