#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

# read temperature from DS18b20 sensor
import math
import os
import numpy as np
from pprint import pprint
import logging
from read_gpio import setup_gpio, reset_ds18b20_3V

logger = logging.getLogger('HoneyPi.read_ds18b12')

unfiltered_values = [] # here we keep all the unfilteres values
filtered_temperature = [] # here we keep the temperature values after removing outliers

def measure_temperature(sensor):
    try:
        try:
            if 'device_id' not in sensor:
                sensor["device_id"] = "undefined"
        except Exception as ex:
            logger.exception('Unhandled Exception in measure_temperature / device_id '+ repr(ex))

        try:
            if 'pin' in sensor:
                gpio_3V = int(sensor["pin"])
                if gpio_3V > 0:

                    logger.debug("GPIO" + str(gpio_3V) + " is defined as 3.3V power source for Ds18b20 '" + sensor["device_id"] + "'")
                    setup_gpio(gpio_3V)

                    if not os.path.isdir("/sys/bus/w1/devices/" + sensor["device_id"]):
                        logger.warning("Resetting 3.3V GPIO" + str(gpio_3V) + " because Ds18b20 with device-id '" + sensor["device_id"] + "' was missing.")
                        reset_ds18b20_3V(gpio_3V)
        except Exception as ex:
            logger.exception('Unhandled Exception in measure_temperature / pin' + repr(ex))
            
        try:
            if sensor["device_id"] != "undefined":
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
            logger.warning('Cannot find Device-ID from Ds18b20 Sensor ' + sensor["device_id"])
            return None
        except IndexError:
            logger.warning('Ds18b20 Sensor with Device-ID: ' + sensor["device_id"] + ' found, but no temperatures listed')
            return None
        except Exception as ex:
            logger.exception('Error: Unhandled Exception in measure_temperature read 1-wire slave file' + repr(ex))
    except Exception as ex:
        logger.exception('Error: Unhandled Exception in measure_temperature' + repr(ex))

    return None

# function for reading the value from sensor
def read_unfiltered_temperatur_values(sensorIndex, sensor):
    temperature = None
    try:
        temperature = measure_temperature(sensor)

        if temperature is not None and math.isnan(temperature) == False:
            logger.debug("temperature for device '" + str(sensor["device_id"]) + "': " + str(temperature))
            unfiltered_values[sensorIndex].append(temperature)

    except IOError as ex1:
        logger.exception("IOError occurred in read_unfiltered_temperatur_values" + repr(ex1))
    except TypeError as ex2:
        logger.exception("TypeError occurred in read_unfiltered_temperatur_values" + repr(ex2))
    except Exception as ex:
        logger.exception("Unhandled Exception in read_unfiltered_temperatur_values" + repr(ex))
# function which eliminates the noise by using a statistical model
# we determine the standard normal deviation and we exclude anything that goes beyond a threshold
# think of a probability distribution plot - we remove the extremes
# the greater the std_factor, the more "forgiving" is the algorithm with the extreme values

def filter_values(unfiltered_values, std_factor=2):
    try:
        mean = np.mean(unfiltered_values)
        standard_deviation = np.std(unfiltered_values)

        if standard_deviation == 0:
            return unfiltered_values

        final_values = [element for element in unfiltered_values if element > mean - std_factor * standard_deviation]
        final_values = [element for element in final_values if element < mean + std_factor * standard_deviation]

        return final_values
    except Exception as ex:
        logger.exception("Unhandled Exception in filter_values" + repr(ex))
        
# function for appending the filter
def filter_temperatur_values(sensorIndex):
    try:
        if sensorIndex in unfiltered_values and len(unfiltered_values[sensorIndex]) > 5:
            # read the last 5 values and filter them
            filtered_temperature[sensorIndex].append(np.mean(filter_values([x for x in unfiltered_values[sensorIndex][-5:]])))
    except Exception as ex:
        logger.exception("Unhandled Exception in filter_temperatur_values"+ repr(ex))
        
def checkIfSensorExistsInArray(sensorIndex):
    try:
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
    except Exception as ex:
        logger.exception("Unhandled Exception in checkIfSensorExistsInArray"+ repr(ex))
