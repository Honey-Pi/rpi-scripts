#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

# read temperature from DS18b20 sensor
import math
import os
import numpy as np
from pprint import pprint
from utilities import error_log
from read_gpio import setup_gpio, reset_ds18b20_3V

unfiltered_values = [] # here we keep all the unfilteres values
filtered_temperature = [] # here we keep the temperature values after removing outliers

def measure_temperature(sensor):
    try:
        if 'pin' in sensor and isinstance(sensor["pin"], (int)) and sensor["pin"] > 0:
            setup_gpio(sensor["pin"])

            if (os.path.isdir("/sys/bus/w1/devices/" + sensor["device_id"]) == False):
                error_log("Info: Resetting 3.3V GPIO " + str(sensor["pin"]) + " because " + sensor["device_id"] + " was missing.")
                reset_ds18b20_3V(sensor["pin"])

        # read 1-wire slave file
        with open('/sys/bus/w1/devices/' + sensor["device_id"] + '/w1_slave', 'r') as file:
            file_content = file.read()
            file.close()

            # read temperature and convert temperature
            string_value = file_content.split("\n")[1].split(" ")[9]
            temperature = float(string_value[2:]) / 1000
            temperature = float('%6.2f' % temperature)

            return temperature

    except FileNotFoundError:
        error_log("Warning: Cannot find Device-ID from Ds18b20 Sensor " + sensor["device_id"])
    except Exception as ex:
        error_log(ex, "Error: Unhandled Exception in measure_temperature")

    return None

# function for reading the value from sensor
def read_unfiltered_temperatur_values(sensorIndex, sensor):
    temperature = None
    try:
        temperature = measure_temperature(sensor)
        print("temperature for device '" + str(sensor["device_id"]) + "': " + str(temperature))

        if math.isnan(temperature) == False:
            unfiltered_values[sensorIndex].append(temperature)

    except IOError as ex1:
        error_log(ex1, "Error: IOError occurred in read_unfiltered_temperatur_values")
    except TypeError as ex2:
        error_log(ex2, "Error: TypeError occurred in read_unfiltered_temperatur_values")
    except Exception as ex:
        error_log(ex, "Error: Unhandled Exception in read_unfiltered_temperatur_values")
# function which eliminates the noise by using a statistical model
# we determine the standard normal deviation and we exclude anything that goes beyond a threshold
# think of a probability distribution plot - we remove the extremes
# the greater the std_factor, the more "forgiving" is the algorithm with the extreme values

def filter_values(unfiltered_values, std_factor=2):
    mean = np.mean(unfiltered_values)
    standard_deviation = np.std(unfiltered_values)

    if standard_deviation == 0:
        return unfiltered_values

    final_values = [element for element in unfiltered_values if element > mean - std_factor * standard_deviation]
    final_values = [element for element in final_values if element < mean + std_factor * standard_deviation]

    return final_values

# function for appending the filter
def filter_temperatur_values(sensorIndex):
    if sensorIndex in unfiltered_values and len(unfiltered_values[sensorIndex]) > 5:
        # read the last 5 values and filter them
        filtered_temperature[sensorIndex].append(np.mean(filter_values([x for x in unfiltered_values[sensorIndex][-5:]])))

def checkIfSensorExistsInArray(sensorIndex):
    try:
        filtered_temperature[sensorIndex]
    except IndexError:
        # handle this
        filtered_temperature.append([])
        unfiltered_values.append([])

    # prevent buffer overflow
    if len(filtered_temperature[sensorIndex]) > 50:
        filtered_temperature[sensorIndex] = filtered_temperature[sensorIndex][len(filtered_temperature[sensorIndex])-10:] # remove all but the last 10 elements
    if len(unfiltered_values[sensorIndex]) > 50:
        unfiltered_values[sensorIndex] = unfiltered_values[sensorIndex][len(unfiltered_values[sensorIndex])-10:] # remove all but the last 10 elements
