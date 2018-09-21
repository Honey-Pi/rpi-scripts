#!/usr/bin/env python
# This file is part of HoneyPi which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import math
import threading
from pprint import pprint
from time import sleep
from urllib2 import HTTPError
from requests.exceptions import ConnectionError

import RPi.GPIO as GPIO
import thingspeak

from read_bme680 import measure_bme680, burn_in_bme680
from read_ds18b20 import measure_temperature, read_unfiltered_temperatur_values, filter_temperatur_values, filtered_temperature, checkIfSensorExistsInArray
from read_hx711 import measure_weight
from read_settings import get_settings, get_sensors

def start_measurement(measurement_stop):
    print("Messungen beginnen")
    
    # load settings
    settings = get_settings()
    # ThingSpeak data
    channel_id = settings["ts_channel_id"]
    write_key = settings["ts_write_key"]
    interval = settings["interval"]

    if interval and not isinstance(interval, int) or not channel_id or not write_key:
        print "settings.json is not correct"
        measurement_stop.set()

    # read configured sensors from settings.json
    ds18b20Sensors = get_sensors(settings, 0)
    bme680Sensors = get_sensors(settings, 1)
    weightSensors = get_sensors(settings, 2)

    # if bme680 is configured
    if bme680Sensors and len(bme680Sensors) == 1:
        # bme680 sensor must be burned in before use
        gas_baseline = burn_in_bme680()

        # if burning was canceled => exit
        if gas_baseline is None:
            print "gas_baseline can't be None"
            measurement_stop.set()

    # ThingSpeak channel
    channel = thingspeak.Channel(id=channel_id, write_key=write_key)

    # start at -10 because we want to get 10 values before we can filter some out
    counter = -10
    while not measurement_stop.is_set():

        # read values from sensors every second
        for (sensorIndex, sensor) in enumerate(ds18b20Sensors):
            checkIfSensorExistsInArray(sensorIndex)
            read_unfiltered_temperatur_values(sensorIndex, sensor)
        
        # for testing:
        try:
            #weight = measure_weight(weightSensors[0])
            #print(weight)
        except IOError:
            print "IOError occurred"    
        except TypeError:
            print "TypeError occurred"

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
            if bme680Sensors and len(bme680Sensors) == 1:
                bme680_values = measure_bme680(gas_baseline, bme680Sensors[0])
                ts_fields.update(bme680_values)

            # measure every sensor with type 2
            for (i, sensor) in enumerate(weightSensors):
                weight = measure_weight(sensor)
                ts_fields.update(weight)

            # print measurement values for debug reasons
            for key, value in ts_fields.iteritems():
                print key + ": " + str(value)
            
            try:
                # update ThingSpeak / transfer values
                if len(ts_fields) > 0:
                    channel.update(ts_fields)
            except ConnectionError:
                print "ConnectionError occurred: Could not upload measurements to ThingSpeak"  
            except HTTPError:
                print "HTTPError occurred: Could not upload measurements to ThingSpeak"  
        
        counter += 1
        sleep(0.98)

    print("Measurement-Script runtime was " + str(counter) + " seconds.")