#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

from HX711 import HX711
import RPi.GPIO as GPIO 
import time

# global var
ledState = False
GPIO_PIN = 20 # debug pin

# setup GPIO
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BCM) # Zaehlweise der GPIO-PINS auf der Platine
GPIO.setup(GPIO_PIN, GPIO.OUT) # Set pin 20 to led output

def triggerPIN():
    global ledState, GPIO_PIN
    # Method for Alex
    ledState = not ledState
    GPIO.output(GPIO_PIN, ledState)

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

def get_temp(weight_sensor, ts_fields):
    try:
        if 'ts_field_temperature' in weight_sensor:
            ts_field_temperature = weight_sensor["ts_field_temperature"]
            return getattr(ts_fields, ts_field_temperature) 

    except Exception as e:
        print("Exeption while getting temperature field: " + str(e))
    
    return None

def compensate_weight(weight_sensor, weight, ts_fields):
    try:
        if 'compensation' in weight_sensor:
            compensation = weight_sensor["compensation"]
            if compensation:
                if 'compensation_value' in weight_sensor:
                    compensation_value = weight_sensor["compensation_value"]
                else:
                    compensation_value = None
                if 'compensation_temp' in weight_sensor:
                    compensation_temp = weight_sensor["compensation_temp"]
                else:
                    compensation_temp = None
                ts_field_temperature = get_temp(weight_sensor, ts_fields)

                # do compensation
                if compensation_temp and compensation_value and (ts_field_temperature or ts_field_temperature == 0):
                    delta = compensation_temp-ts_field_temperature
                    if compensation_temp > ts_field_temperature:
                        weight = weight - compensation_value*delta
                    elif compensation_temp < ts_field_temperature:
                        weight = weight + compensation_value*delta


    except Exception as e:
        print("Exeption while temperature compensation: " + str(e))
    
    return weight

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

        count = 0
        while True and count < 3:
            count += 1
            # improve weight measurement by doing 3 weight measures
            weightMeasures=[]
            for i in range(3):
                #use outliers_filter and do average over 5 measurements
                weightMeasures.append(hx.get_data_mean(5))

            # take "best" measure
            average_weight = int(average(weightMeasures))
            weight = takeClosest(weightMeasures, average_weight)
            print("Average weight: " + str(average_weight))

            ALLOWED_DIVERGENCE = 20 # old: abs(weight)*0.1
            # if divergence is too big
            if abs(average_weight-weight) > ALLOWED_DIVERGENCE:
                # if difference between avg weight and chosen weight is bigger than ALLOWED_DIVERGENCE
                triggerPIN() # debug method
                print("Info: Difference between average weight and chosen weight is more than ALLOWED_DIVERGENCE.")
            else:
                # divergence is OK => skip
                break

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
