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
#GPIO.setup(GPIO_PIN, GPIO.OUT) # Set pin 20 to led output

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
                if isinstance(temp_now, (int, float)) and isinstance(weight, (int, float)):
                    print("Weight cell temperature compensation is enabled.")
                    print("=> TempCalibration: " + str(compensation_temp) + "C TempNow: " + str(temp_now) + "C WeightBefore: " + str(weight) + "g")
                    # do compensation
                    if compensation_temp and compensation_value:
                        delta = round(temp_now-compensation_temp, 4)
                        weight = weight - (compensation_value*delta)
                    print("=> TempDelta: " + str(delta) + "C WeightAfter: " + str(weight) + "g")
                else:
                    print("Temperature Compensation: No temperature in given field.")

    except Exception as e:
        print("Exeption while temperature compensation: " + str(e))

    return set_ts_field(weight_sensor, weight)

def set_ts_field(weight_sensor, weight):
    if weight and type(weight) in (float, int):
        weight = weight/1000  # gramms to kg
        weight = float("{0:.3f}".format(weight)) # float only 3 decimals

        if 'ts_field' in weight_sensor:
            return ({weight_sensor["ts_field"]: weight})
    return {}

def init_hx711(weight_sensor, debug=False):
    # HX711 GPIO
    pin_dt = 5
    pin_sck = 6
    channel = 'A'
    errorEncountered = False
    try:
        pin_dt = int(weight_sensor["pin_dt"])
        pin_sck = int(weight_sensor["pin_sck"])
        channel = weight_sensor["channel"]
    except Exception as e:
        print("HX711 missing param: " + str(e))

    loops = 0
    while not errorEncountered and loops < 3:
        loops += 1
        try:
            # setup weight sensor
            hx = HX711(dout_pin=pin_dt, pd_sck_pin=pin_sck, gain_channel_A=128, select_channel=channel)
            if debug:
                hx.set_debug_mode(flag=debug)
            errorEncountered = hx.reset() # Before we start, reset the hx711 (not necessary)

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
        if hx is None:
            hx = init_hx711(weight_sensor)
            time.sleep(0.01) # sleep 10ms

        if hx is not None:
            hx.power_up()
            hx.set_scale_ratio(scale_ratio=reference_unit)
            hx.set_offset(offset=offset)

            temp = hx.get_raw_data_mean(6) # measure just for fun

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
                    # use outliers_filter and do average over 30 measurements
                    hx_weight = hx.get_weight_mean(30)
                    if isinstance(hx_weight, (int, float)):
                        weightMeasures.append(hx_weight)
                    else: # returned False
                        LOOP_AVG += 1 # increase loops because of failured measurement (returned False)

                # take "best" measure
                average_weight = round(average(weightMeasures), 1)
                weight = round(takeClosest(weightMeasures, average_weight), 1)
                print("Average weight: " + str(average_weight) + "g, Chosen weight: " + str(weight) + "g")

                ALLOWED_DIVERGENCE = round((500/reference_unit), 1)
                # bei reference_unit=25 soll ALLOWED_DIVERGENCE=20
                # bei reference_unit=1 soll ALLOWED_DIVERGENCE=300
                if abs(average_weight-weight) > ALLOWED_DIVERGENCE:
                    # if difference between avg weight and chosen weight is bigger than ALLOWED_DIVERGENCE
                    # triggerPIN() # debug method
                    print("Info: Difference between average weight ("+ str(average_weight)+"g) and chosen weight (" + str(weight) + "g) is more than " + str(ALLOWED_DIVERGENCE) + "g. => Try again ("+str(count)+"/"+str(LOOP_TRYS)+")")
                    time.sleep(0.01) # sleep 10ms

                    if LOOP_TRYS == count: # last loop
                        # 3 loops and still no chosen weight => fallback measurement
                        weight = round(hx.get_weight_mean(30), 1) # average from 30 times
                        print("Chosen weight: " + str(weight) + "g")
                else:
                    # divergence is OK => skip
                    break

            #hx.power_down()

            # invert weight if flag is set
            if 'invert' in weight_sensor and weight_sensor['invert'] == True and isinstance(weight, (int, float)):
                weight = weight*-1;

    except Exception as e:
        print("Reading HX711 failed: " + str(e))

    return weight
