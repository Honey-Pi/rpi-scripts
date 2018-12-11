#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import math
import threading
import time
from pprint import pprint
from time import sleep

import RPi.GPIO as GPIO
import thingspeak # https://github.com/mchwalisz/thingspeak/
import requests 

from read_bme680 import measure_bme680, burn_in_bme680, bme680IsConnected
from read_ds18b20 import measure_temperature, read_unfiltered_temperatur_values, filter_temperatur_values, filtered_temperature, checkIfSensorExistsInArray
from read_hx711 import measure_weight
from read_dht import measure_dht
from read_settings import get_settings, get_sensors
from utilities import reboot, error_log

class MyRebootException(Exception):
    """Too many ConnectionErrors => Rebooting"""
    pass

def start_measurement(measurement_stop):
    try:
        print("The measurements have started.")
        start_time = time.time()
        
        # load settings
        settings = get_settings()
        # ThingSpeak data
        channel_id = settings["ts_channel_id"]
        write_key = settings["ts_write_key"]
        interval = settings["interval"]

        if interval and not isinstance(interval, int) or interval == 0 or not channel_id or not write_key:
            print("ThingSpeak settings are not complete or interval is 0")
            measurement_stop.set()

        # read configured sensors from settings.json
        ds18b20Sensors = get_sensors(settings, 0)
        bme680Sensors = get_sensors(settings, 1)
        weightSensors = get_sensors(settings, 2)
        dhtSensors = get_sensors(settings, 3)

        # if bme680 is configured
        if bme680Sensors and len(bme680Sensors) == 1 and bme680IsConnected:
            # bme680 sensor must be burned in before use
            gas_baseline = burn_in_bme680()

            # if burning was canceled => exit
            if gas_baseline is None:
                print("gas_baseline can't be None")
                measurement_stop.set()

        # ThingSpeak channel
        channel = thingspeak.Channel(id=channel_id, write_key=write_key)

        # counting connection Errors
        connectionErros = 0

        # start at -6 because we want to get 6 values before we can filter some out
        counter = -6
        while not measurement_stop.is_set():

            # read values from sensors every second
            for (sensorIndex, sensor) in enumerate(ds18b20Sensors):
                checkIfSensorExistsInArray(sensorIndex)
                read_unfiltered_temperatur_values(sensorIndex, sensor)
            
            # for testing:
            #try:
            #    weight = measure_weight(weightSensors[0])
            #    print("weight: " + str(list(weight.values())[0]))
            #except IOError:
            #    print "IOError occurred"    
            #except TypeError:
            #    print "TypeError occurred"
            #except IndexError:
            #    print "IndexError occurred"

            # wait seconds of interval before next check
            # free ThingSpeak account has an upload limit of 15 seconds
            if counter%interval == 0:
                print("Time over for a new measurement.")

                # filter the values out
                for (sensorIndex, sensor) in enumerate(ds18b20Sensors):
                    filter_temperatur_values(sensorIndex)

                # dict with all fields and values which will be tranfered to ThingSpeak later
                ts_fields = {}

                # measure every sensor with type 0
                for (sensorIndex, sensor) in enumerate(ds18b20Sensors):
                    # if we have at leat one filtered value we can upload
                    if len(filtered_temperature[sensorIndex]) > 0: 
                        ds18b20_temperature = filtered_temperature[sensorIndex].pop() # get last value from array
                        ts_field_ds18b20 = sensor["ts_field"]
                        if ts_field_ds18b20:
                            ts_fields.update({ts_field_ds18b20: ds18b20_temperature})

                # measure BME680 (can only be once) [type 1]
                if bme680Sensors and len(bme680Sensors) == 1 and bme680IsConnected:
                    bme680_values = measure_bme680(gas_baseline, bme680Sensors[0])
                    ts_fields.update(bme680_values)

                # measure every sensor with type 2 [HX711]
                for (i, sensor) in enumerate(weightSensors):
                    weight = measure_weight(sensor)
                    ts_fields.update(weight)

                # measure every sensor with type 3 [DHT11/DHT22]
                for (i, sensor) in enumerate(dhtSensors):
                    tempAndHum = measure_dht(sensor)
                    ts_fields.update(tempAndHum)

                # print measurement values for debug reasons
                for key, value in ts_fields.iteritems():
                    print key + ": " + str(value)
                
                try:
                    # update ThingSpeak / transfer values
                    if len(ts_fields) > 0:
                        channel.update(ts_fields)
                        # reset connectionErros because transfer succeded
                        connectionErros = 0
                except requests.exceptions.HTTPError as errh:
                    error_log(errh, "Http Error")
                except requests.exceptions.ConnectionError as errc:
                    error_log(errc, "Error Connecting")
                    connectionErros += 1
                    # multiple connectionErrors in a row => Exception
                    if connectionErros > 4:
                        raise MyRebootException
                except requests.exceptions.Timeout as errt:
                    error_log(errt, "Timeout Error")
                except requests.exceptions.RequestException as err:
                    error_log(err, "Something Else")
            
            counter += 1
            sleep(0.96)

        end_time = time.time()
        time_taken = end_time - start_time # time_taken is in seconds
        time_taken_s = float("{0:.2f}".format(time_taken)) # remove microseconds
        print("Measurement-Script runtime was " + str(time_taken_s) + " seconds.")
        
    except MyRebootException as re:
        error_log(re, "Too many ConnectionErrors => Rebooting")
        time.sleep(1)
        reboot()
    except Exception as e:
        error_log(e, "Unhandled Exception while Measurement")
        time.sleep(60)
        reboot()