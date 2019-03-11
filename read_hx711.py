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
    return total / len(myList)

def get_temp(weight_sensor, ts_fields):
    try:
        if 'ts_field_temperature' in weight_sensor:
            field_name = weight_sensor["ts_field_temperature"]
            return float(ts_fields[field_name])

    except Exception as e:
        print("Exeption while getting temperature field: " + str(e))
    
    return None

def compensate_temperature(weight_sensor, weight, ts_fields):
    try:
        if 'compensation' in weight_sensor:
            compensation = weight_sensor["compensation"]
            if compensation:
                if 'compensation_value' in weight_sensor:
                    compensation_value = float(weight_sensor["compensation_value"])
                else:
                    compensation_value = None
                if 'compensation_temp' in weight_sensor:
                    compensation_temp = float(weight_sensor["compensation_temp"])
                else:
                    compensation_temp = None
                
                temp_now = get_temp(weight_sensor, ts_fields)
                if (temp_now or temp_now == 0) and (weight or weight == 0):
                    print("Weight cell temperature compensation is enabled (TempNow:" + str(temp_now) + " WeightBefore:" + str(weight) + ")")
                    # do compensation
                    if compensation_temp and compensation_value:
                        delta = compensation_temp-temp_now
                        if compensation_temp > temp_now:
                            weight = weight - compensation_value*delta
                        elif compensation_temp < temp_now:
                            weight = weight + compensation_value*delta
                else:
                    print("Temperature Compensation: No temperature in given field.")


    except Exception as e:
        print("Exeption while temperature compensation: " + str(e))

    return set_ts_field(weight_sensor, weight)

def set_ts_field(weight_sensor, weight):
    if weight and type(weight) in (float, int):
        weight = weight/1000  # gramms to kg
        weight = float("{0:.3f}".format(weight)) # float only 3 decimals

    if 'ts_field' in weight_sensor and (weight or weight == 0):
        return ({weight_sensor["ts_field"]: weight})
    else:
        return {}

def init_hx711(weight_sensor, debug=False):
    # HX711 GPIO
    pin_dt = 5
    pin_sck = 6
    channel = 'A'
    try:
        pin_dt = int(weight_sensor["pin_dt"])
        pin_sck = int(weight_sensor["pin_sck"])
        channel = weight_sensor["channel"]   
    except Exception as e:
        print("HX711 missing param: " + str(e))

    try:
        # setup weight sensor
        hx = HX711(dout_pin=pin_dt, pd_sck_pin=pin_sck, gain_channel_A=128, select_channel=channel)
        hx.set_debug_mode(flag=debug)
        hx.reset() # Before we start, reset the hx711 (not necessary)

        return hx
    except Exception as e:
        print("Initializing HX711 failed: " + str(e))

    return None


def measure_weight(weight_sensor, hx=None):
    
    if 'reference_unit' in weight_sensor:
        reference_unit = float(weight_sensor["reference_unit"])
    else:
        reference_unit = 1
    if 'offset' in weight_sensor:
        offset = int(weight_sensor["offset"])
    else:
        offset = 0

    weight = None
    try:
        # init hx711
        if not hx:
            hx = init_hx711(weight_sensor)   

        hx.power_up()
        hx.set_scale_ratio(scale_ratio=reference_unit)
        hx.set_offset(offset=offset)

        count = 0
        LOOP_TRYS = 3
        while count < LOOP_TRYS:
            count += 1
            # improve weight measurement by doing LOOP_TIMES weight measurements
            weightMeasures=[]
            count_avg = 0
            LOOP_AVG = 3
            while count_avg < LOOP_AVG and count_avg < 6: # Break after max. 6 loops
                count_avg += 1
                # use outliers_filter and do average over 3 measurements
                hx_weight = hx.get_weight_mean(3)
                if hx_weight or hx_weight == 0:
                    weightMeasures.append(hx_weight) 
                else: # returned False
                    LOOP_AVG += 1 # increase loops because of failured measurement (returned False)

            # take "best" measure
            average_weight = format(average(weightMeasures), '.1f')
            weight = format(takeClosest(weightMeasures, average_weight), '.1f')
            print("Average weight: " + str(average_weight) + "g, Chosen weight: " + str(weight) + "g")

            ALLOWED_DIVERGENCE = format((500/reference_unit), '.1f')
            # bei reference_unit=25 soll ALLOWED_DIVERGENCE=20
            # bei reference_unit=1 soll ALLOWED_DIVERGENCE=300
            if abs(average_weight-weight) > ALLOWED_DIVERGENCE:
                # if difference between avg weight and chosen weight is bigger than ALLOWED_DIVERGENCE
                triggerPIN() # debug method
                print("Info: Difference between average weight ("+ str(average_weight)+"g) and chosen weight (" + str(weight) + "g) is more than " + str(ALLOWED_DIVERGENCE) + "g. => Try again")
            else:
                # divergence is OK => skip
                break

        #weight = hx.get_weight_mean(30) # average from 30 times
        hx.power_down()

        # invert weight if flag is set
        if 'invert' in weight_sensor and weight_sensor['invert'] == True and (weight or weight == 0):
            weight = weight*-1;

    except Exception as e:
        print("Reading HX711 failed: " + str(e))

    return weight
