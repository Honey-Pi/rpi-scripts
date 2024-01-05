#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

from sensors.HX711 import HX711 # import the class HX711
# Source: https://github.com/gandalf15/HX711
import RPi.GPIO as GPIO # import GPIO
import time
import logging

logger = logging.getLogger('HoneyPi.read_hx711')

# setup GPIO
GPIO.setmode(GPIO.BCM) # set GPIO pin mode to BCM numbering

def takeClosest(myList, myNumber):
    # from list of integers, get number closest to a given value
    try:
        closest = myList[0]
        for i in range(1, len(myList)):
            if abs(myList[i] - myNumber) < closest:
                closest = myList[i]
        return closest
    except Exception as e:
        logger.exception('Error in takeClosest.')

def average(myList):
    # Finding the average of a list
    try:
        total = sum(myList)
        return total / len(myList)
    except Exception as e:
        logger.exception('Error in average.')


def findmax(myList):
    # from list of integers, get number closest to a given value
    try:
        maximum = myList[0]
        for i in range(1, len(myList)):
            if (myList[i] > maximum):
                maximum = myList[i]
        return maximum
    except Exception as e:
        logger.exception('Error in findmax.')

def findmin(myList):
    # from list of integers, get number closest to a given value
    try:
        minimum = myList[0]
        for i in range(1, len(myList)):
            if (myList[i] < minimum):
                minimum = myList[i]
        return minimum
    except Exception as e:
        logger.exception('Error in findmin.')


def easy_weight(weight_sensor):
    pin_dt = 5
    pin_sck = 6
    channel = 'A'
    reference_unit = 1
    offset = 0

    try:
        pin_dt = int(weight_sensor["pin_dt"])
        pin_sck = int(weight_sensor["pin_sck"])
        channel = weight_sensor["channel"]
        reference_unit = float(weight_sensor["reference_unit"])
        offset = int(weight_sensor["offset"])
    except Exception as e:
        logger.error('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' missing param: ' + str(e))

    try:
        GPIO.setmode(GPIO.BCM)  # set GPIO pin mode to BCM numbering
        # Create an object hx which represents your real hx711 chip
        hx = HX711(dout_pin=pin_dt, pd_sck_pin=pin_sck, select_channel=channel)
        hx.set_scale_ratio(scale_ratio=reference_unit)
        hx.set_offset(offset=offset)
        # use outliers_filter and do average over 30 measurements
        weight = hx.get_weight_mean(30)
        if weight != False:
            return round(weight, 1)

    except Exception as e:
        logger.error('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' Fallback failed: ' + str(e))

    finally:
        pass

    return None

def get_temp(weight_sensor, ts_fields):
    try:
        if 'ts_field_temperature' in weight_sensor:
            field_name = weight_sensor["ts_field_temperature"]
            return float(ts_fields[field_name])

    except Exception as ex:
        logger.error("Exeption while getting temperature field: " + repr(ex))

    return None

def compensate_temperature(weight_sensor, weight, ts_fields):
    pin_dt = 5
    pin_sck = 6
    channel = 'A'
    reference_unit = 1
    offset = 0

    try:
        pin_dt = int(weight_sensor["pin_dt"])
        pin_sck = int(weight_sensor["pin_sck"])
        channel = weight_sensor["channel"]
        reference_unit = float(weight_sensor["reference_unit"])
        offset = int(weight_sensor["offset"])
    except Exception as e:
        logger.error('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' compensate_temperature missing param: ' + str(e))
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
                    logger.debug('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' Weight cell temperature compensation is enabled. TempCalibration: ' + str(compensation_temp) + 'C TempNow: ' + str(temp_now) + 'C WeightBefore: ' + str(weight) + 'g')
                    # do compensation
                    if compensation_temp and compensation_value:
                        delta = round(temp_now-compensation_temp, 4)
                        weight = weight - (compensation_value*delta)
                    logger.debug('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' => TempDelta: ' + str(delta) + 'C WeightAfter: ' + str(weight) + 'g')
                else:
                    logger.warning('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' Temperature Compensation: No temperature in given field.')

    except Exception as ex:
        logger.exception("Exeption in compensate_temperature")

    return weight

def set_ts_field(weight_sensor, weight):
    try:
        if weight and type(weight) in (float, int):
            weight = weight/1000  # gramms to kg
            weight = float("{0:.3f}".format(weight)) # float only 3 decimals

            if 'ts_field' in weight_sensor:
                return ({weight_sensor["ts_field"]: weight})
        return {}
    except Exception as ex:
        logger.exception('Unhandled Exception in set_ts_field.')

def init_hx711(weight_sensor):
    # HX711 GPIO
    pin_dt = 5
    pin_sck = 6
    channel = 'A'
    errorEncountered = False
    try:
        try:
            debug = weight_sensor["debug"]
        except:
            debug = False

        try:
            pin_dt = int(weight_sensor["pin_dt"])
            pin_sck = int(weight_sensor["pin_sck"])
            channel = weight_sensor["channel"]
        except Exception as e:
            logger.error("init_hx711 missing param: " + str(e))

        logger.debug('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' Init started')
        loops = 0
        while not errorEncountered and loops < 3:
            loops += 1
            try:
                GPIO.setmode(GPIO.BCM) # set GPIO pin mode to BCM numbering
                # Create an object hx which represents your real hx711 chip
                hx = HX711(dout_pin=pin_dt, pd_sck_pin=pin_sck, select_channel=channel)
                hx.set_debug_mode(flag=debug)
                errorEncountered = hx.reset() # Before we start, reset the hx711 (not necessary)
                if not errorEncountered:
                    logger.debug('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' Init finished')
                    return hx
            except Exception as e:
                if str(e) == "no median for empty data" or str(e) == "mean requires at least one data point":
                    logger.debug('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' Could not read data from HX711 => Try again: ' + str(loops) + '/3')
                else:
                    logger.warning('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' Initializing HX711 failed: ' + str(e))
            time.sleep(1)

        logger.error('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' initializing failed, Please check cabling and configuration! Returning empty HX711.')
        return None
    except Exception as e:
        logger.exception("Unhandled Exception in init_hx711")


def measure_weight(weight_sensor, hx=None):
    try:
        weight_sensor
    except Exception as e:
        logger.error("measure_hx711 is missing param weight_sensor: " + str(e))

    if 'reference_unit' in weight_sensor:
        reference_unit = float(weight_sensor["reference_unit"])
    else:
        reference_unit = 1
    if 'offset' in weight_sensor:
        offset = int(weight_sensor["offset"])
    else:
        offset = 0

    pin_dt = 0
    pin_sck = 0
    channel = ''

    try:
        pin_dt = int(weight_sensor["pin_dt"])
        pin_sck = int(weight_sensor["pin_sck"])
        channel = weight_sensor["channel"]
    except Exception as e:
        logger.error("HX711 missing param: " + str(e))
        pass

    temp_reading = None
    weight = None
    try:
        logger.debug('measure HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' started')
        GPIO.setmode(GPIO.BCM) # set GPIO pin mode to BCM numbering

        # init hx711
        if not hx:
            logger.debug('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' no initialized HX711 received, initializing now.')
            hx = init_hx711(weight_sensor)

        if hx:
            temp_reading = hx.get_raw_data_mean(6) # measure just for fun

        if not isinstance(temp_reading, (int, float)): # always check if you get correct value or only False
            logger.debug('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' bad data measured, initializing HX711 again.')
            if hx:
                hx.reset()
            hx = init_hx711(weight_sensor)

        hx.power_up()
        hx.set_scale_ratio(scale_ratio=reference_unit)
        hx.set_offset(offset=offset)

        count = 0
        LOOP_TRYS = 6
        while count < LOOP_TRYS:

            count += 1
            # improve weight measurement by doing LOOP_TIMES weight measurements
            weightMeasures=[]
            count_avg = 0
            LOOP_AVG = 3
            while count_avg < LOOP_AVG and count_avg < 6: # Break after max. 6 loops
                count_avg += 1
                num_measurements = 41
                reading = hx.get_weight_mean(num_measurements) # use outliers_filter and do average over 41 measurements
                if isinstance(reading, (int, float)): # always check if you get correct value or only False
                    weightMeasures.append(reading)
                    num_data_filtered_out = hx.get_num_data_filtered_out()
                    percentage_filtered_out = round((num_data_filtered_out / num_measurements * 100),2)
                    if percentage_filtered_out >= 40:
                        logger.warning('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' ' + str(percentage_filtered_out) + '%, in total ' + str(num_data_filtered_out) + ' of ' + str(num_measurements) + ' elements removed by filter within hx711. You might need to check your power supply or cabling setup.')
                    else:
                        logger.debug('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' ' + str(percentage_filtered_out) + '%, in total ' + str(num_data_filtered_out) + ' of ' + str(num_measurements) + ' elements removed by filter within hx711')
                else: # returned False
                    LOOP_AVG += 1 # increase loops because of failured measurement (returned False)
                    logger.error('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' Failured measurement, you might need to check your hx711 setup')

            # take "best" measure
            average_weight = round(average(weightMeasures), 1)
            maxweight = round(findmax(weightMeasures), 1)
            minweight = round(findmin(weightMeasures), 1)
            weight = round(takeClosest(weightMeasures, average_weight), 1)
            logger.debug('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' Max weight: ' + str(maxweight) + 'g, Min weight: ' + str(minweight) + 'g, Average weight: ' + str(average_weight) + 'g, Chosen weight: ' + str(weight) + 'g')

            ALLOWED_DIVERGENCE = round((500/reference_unit), 1)
            # bei reference_unit=25 soll ALLOWED_DIVERGENCE=20
            # bei reference_unit=1 soll ALLOWED_DIVERGENCE=300
            if abs(average_weight-weight) > ALLOWED_DIVERGENCE:
                # if difference between avg weight and chosen weight is bigger than ALLOWED_DIVERGENCE
                logger.warning('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' Difference between average weight ('+ str(average_weight)+'g) and chosen weight (' + str(weight) + 'g) is more than ' + str(ALLOWED_DIVERGENCE) + 'g. => Try again ('+str(count)+'/'+str(LOOP_TRYS)+')')

                if LOOP_TRYS == count: # last loop
                    # 3 loops and still no chosen weight => fallback measurement
                    weight = easy_weight(weight_sensor)
                    logger.warning('HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' Difference between average weight ('+ str(average_weight)+'g) and chosen weight (' + str(weight) + 'g) is more than ' + str(ALLOWED_DIVERGENCE) + 'g. after ' +str(count) + ' loops, Fallback weight: ' + str(weight) + 'g')
            else:
                # divergence is OK => skip
                break

        # invert weight if flag is set
        if 'invert' in weight_sensor and weight_sensor['invert'] == True and isinstance(weight, (int, float)):
                weight = weight*-1;
        logger.debug('measure HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' finished')

    except Exception as e:
        if str(e) == "no median for empty data" or str(e) == "mean requires at least one data point":
            logger.error('Could not read data from HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel  + ' Please check cabling and configuration!')
        elif str(e) == "'NoneType' object has no attribute 'power_up'":
            logger.error('Could not access HX711 on DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ' Please check cabling and configuration!')
        else:
            logger.error('Reading HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ': failed: ' + str(e))
    finally:
        pass

    return weight


def measure_hx711(weight_sensor, ts_fields, hx=None):
    fields = {}
    pin_dt = 0
    pin_sck = 0
    channel = ''

    try:
        pin_dt = int(weight_sensor["pin_dt"])
        pin_sck = int(weight_sensor["pin_sck"])
        channel = weight_sensor["channel"]
    except Exception as e:
        logger.error("HX711 missing param: " + str(e))

    try:
        weight = measure_weight(weight_sensor, hx=None)

        if 'ts_field_uncompensated' in weight_sensor and type(weight) in (float, int):
            fields[weight_sensor["ts_field_uncompensated"]] = float("{0:.3f}".format(weight/1000)) # float only 3 decimals
        weight = compensate_temperature(weight_sensor, weight, ts_fields)

        if 'filter_negative' in weight_sensor and weight_sensor['filter_negative'] and weight < -1: # filter negative measurements
            weight = None

        if 'ts_field' in weight_sensor and type(weight) in (float, int):
            fields[weight_sensor["ts_field"]] = float("{0:.3f}".format(weight/1000)) # float only 3 decimals

        if 'ts_field_offset2' in weight_sensor and 'offset2' in weight_sensor:
                    fields[weight_sensor["ts_field_offset2"]] = float("{0:.3f}".format(weight_sensor["offset2"]/1000))
    except Exception as e:
        logger.error('Measure HX711 DT: ' + str(pin_dt) + ' SCK: ' + str(pin_sck) + ' Channel: ' + channel + ': failed: ' + str(e))

    return fields
