#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import math
import threading
import time
from pprint import pprint
from multiprocessing import Process, Queue, Value

import RPi.GPIO as GPIO
import thingspeak # Source: https://github.com/mchwalisz/thingspeak/
import requests

from read_bme680 import measure_bme680, initBME680FromMain
from read_bme280 import measure_bme280
from read_ds18b20 import measure_temperature, read_unfiltered_temperatur_values, filter_temperatur_values, filtered_temperature, checkIfSensorExistsInArray
from read_hx711 import measure_weight, compensate_temperature, init_hx711
from read_dht import measure_dht
from read_max import measure_tc
from read_settings import get_settings, get_sensors
from utilities import reboot, error_log, shutdown, start_single, stop_single, wait_for_internet_connection
from write_csv import write_csv


def send_ts_data(ts_channels, ts_fields, offline, debug):
    # update ThingSpeak / transfer values
    connectionErrorHappened = transfer_channels_to_ts(ts_channels, ts_fields, debug)

    if connectionErrorHappened:
        # Write to CSV-File if ConnectionError occured
        if offline == 2:
            s = write_csv(ts_fields)
            if s and debug:
                error_log("Info: Data succesfully saved to CSV-File.")
        # Do Rebooting if to many connectionErrors in a row
        connectionErrors.value +=1
        error_log("Error: Failed internet connection. Count: " + str(connectionErrors.value))
        if connectionErrors.value >= 5:
            if not debug:
                error_log("Info: Too many ConnectionErrors in a row => Rebooting")
                time.sleep(4)
                reboot()
            else:
                error_log("Info: Did not reboot because debug mode is enabled.")

def clean_fields(ts_fields, countChannels):
    ts_fields_cleaned = {}
    for field in ts_fields:
        fieldNumber = int(field.replace('field',''))
        if fieldNumber > 8:
            fieldNumber = fieldNumber/countChannels
        fieldNew['field' + fieldNumber] = ts_fields[key]
        ts_fields_cleaned.update(fieldNew)
    return ts_fields_cleaned

def transfer_channels_to_ts(ts_channels, ts_fields, debug):
    connectionErrorWithinAnyChannel = []
    for (channelIndex, channel) in enumerate(ts_channels):
        channel_id = ts_channels[channelIndex]["channel_id"]
        write_key = ts_channels[channelIndex]["write_key"]
        if channel_id and write_key:
            ts_instance = thingspeak.Channel(id=channel_id, write_key=write_key)
            ts_fields_cleaned = clean_fields(ts_fields, count(ts_channels))
            connectionError = transfer_channel_to_ts(ts_instance, ts_fields_cleaned, debug)
            connectionErrorWithinAnyChannel += connectionError
        else:
            error_log("Info: No ThingSpeak upload for this channel ("+channelIndex+") because because channel_id or write_key is None.")

    return any(c == True for c in connectionErrorWithinAnyChannel)

def transfer_channel_to_ts(ts_instance, ts_fields_cleaned, debug):
    # do-while to retry failed transfer
    retries = 0
    connectionError = True
    while connectionError:
        try:
            if ts_fields_cleaned:
                ts_instance.update(ts_fields_cleaned)
                if debug:
                    error_log("Info: Data succesfully transfered to ThingSpeak.")
            else:
                error_log("Info: No ThingSpeak data transfer because no fields defined.")

            if connectionErrors.value > 0:
                if debug:
                    error_log("Info: Connection Errors (" + str(connectionErrors.value) + ") Counting resetet.")
                # reset connectionErrors because transfer succeded
                connectionErrors.value = 0
            # break do-while because transfer succeded
            connectionError = False
            break
        except requests.exceptions.HTTPError as errh:
            error_log(errh, "Http Error")
        except requests.exceptions.ConnectionError as errc:
            pass
        except requests.exceptions.Timeout as errt:
            error_log(errt, "Timeout Error")
        except requests.exceptions.RequestException as err:
            error_log(err, "Something Else")
        except Exception as ex:
            error_log(ex, "Exception while sending Data")
        finally:
            if connectionError:
                print("Warning: Waiting for internet connection to try transfer again...")
                wait_for_internet_connection(15) # wait before next try
                retries+=1
                # Maximum 3 retries
                if retries >= 3:
                    break # break do-while
    return connectionError

def measure(offline, debug, ts_channels, filtered_temperature, ds18b20Sensors, bme680Sensors, bme680IsInitialized, dhtSensors, tcSensors, bme280Sensors, weightSensors, hxInits, connectionErrors, measurementIsRunning):
    measurementIsRunning.value = 1 # set flag

    # filter the values out
    for (sensorIndex, sensor) in enumerate(ds18b20Sensors):
        filter_temperatur_values(sensorIndex)

    # dict with all fields and values which will be tranfered to ThingSpeak later
    ts_fields = {}

    # measure every sensor with type 0
    for (sensorIndex, sensor) in enumerate(ds18b20Sensors):
        # if we have at leat one filtered value we can upload
        if len(filtered_temperature[sensorIndex]) > 0 and 'ts_field' in sensor:
            ds18b20_temperature = filtered_temperature[sensorIndex].pop() # get last value from array
            ts_field_ds18b20 = sensor["ts_field"]
            if ts_field_ds18b20:
                ts_fields.update({ts_field_ds18b20: ds18b20_temperature})

    # measure BME680 (can only be one) [type 1]
    if bme680Sensors and len(bme680Sensors) == 1 and bme680IsInitialized:
        bme680_values = measure_bme680(bme680Sensors[0], 30)
        ts_fields.update(bme680_values)

    # measure every sensor with type 3 [DHT11/DHT22]
    for (i, sensor) in enumerate(dhtSensors):
        tempAndHum = measure_dht(sensor)
        ts_fields.update(tempAndHum)

    # measure every sensor with type 4 [MAX6675]
    for (i, sensor) in enumerate(tcSensors):
        tc_temp = measure_tc(sensor)
        ts_fields.update(tc_temp)

    # measure BME280 (can only be one) [type 5]
    if bme280Sensors and len(bme280Sensors) == 1:
        bme280_values = measure_bme280(bme280Sensors[0])
        ts_fields.update(bme280_values)

    start_single()
    # measure every sensor with type 2 [HX711]
    for (i, sensor) in enumerate(weightSensors):
        weight = measure_weight(sensor, hxInits[i])
        weight = compensate_temperature(sensor, weight, ts_fields)
        ts_fields.update(weight)
    stop_single()

    # print all measurement values stored in ts_fields
    for key, value in ts_fields.items():
        print(key + ": " + str(value))

    if len(ts_fields) > 0:
        if offline == 1 or offline == 3:
            try:
                s = write_csv(ts_fields)
                if s and debug:
                    error_log("Info: Data succesfully saved to CSV-File.")
            except Exception as ex:
                error_log(ex, "Exception")

        # if transfer to thingspeak is set
        if (offline == 0 or offline == 1 or offline == 2) and ts_channels:
            # update ThingSpeak / transfer values
            send_ts_data(ts_channels, ts_fields, offline, debug)

    elif debug:
        error_log("Info: No measurement data to send.")

    measurementIsRunning.value = 0 # clear flag


def start_measurement(measurement_stop):
    try:
        start_time = time.time()

        # load settings
        settings = get_settings()
        ts_channels = settings["ts_channels"] # ThingSpeak data (ts_channel_id, ts_write_key)
        interval = settings["interval"]
        debug = settings["debug"] # flag to enable debug mode (HDMI output enabled and no rebooting)
        shutdownAfterTransfer = settings["shutdownAfterTransfer"]
        offline = settings["offline"] # flag to enable offline csv storage

        if debug:
            print("Debug-Mode is enabled.")
            error_log("Info: The measurements have started.")

        # with process shared variables
        connectionErrors = Value('i',0)
        measurementIsRunning = Value('i',0)

        if interval and not isinstance(interval, int) or interval == 0:
            interval = 0
            error_log("Info: Stop measurement because interval is null.")
            measurement_stop.set()

        # read configured sensors from settings.json
        ds18b20Sensors = get_sensors(settings, 0)
        bme680Sensors = get_sensors(settings, 1)
        weightSensors = get_sensors(settings, 2)
        dhtSensors = get_sensors(settings, 3)
        tcSensors = get_sensors(settings, 4)
        bme280Sensors = get_sensors(settings, 5)


        # -- Run Pre Configuration --
        # if bme680 is configured
        if bme680Sensors and len(bme680Sensors) == 1:
            bme680IsInitialized = initBME680FromMain()
        else:
            bme680IsInitialized = 0

        # if hx711 is set
        hxInits = []
        for (i, sensor) in enumerate(weightSensors):
            _hx = init_hx711(sensor, debug)
            hxInits.append(_hx)

        # start at -6 because we want to get 6 values before we can filter some out
        counter = -6
        time_measured = 0
        while not measurement_stop.is_set():
            counter += 1

            # read values from sensors every second
            for (sensorIndex, sensor) in enumerate(ds18b20Sensors):
                checkIfSensorExistsInArray(sensorIndex)
                if 'device_id' in sensor:
                    read_unfiltered_temperatur_values(sensorIndex, sensor['device_id'])

            # wait seconds of interval before next check
            # free ThingSpeak account has an upload limit of 15 seconds
            time_now = time.time()
            isTimeToMeasure = (time_now-time_measured >= interval) and counter > 0 # old: counter%interval == 0
            if isTimeToMeasure or interval == 1:
                now = time.strftime("%H:%M", time.localtime(time_now))
                lastMeasurement = time.strftime("%H:%M", time.localtime(time_measured))
                if time_measured == 0:
                    print("First time measurement. Now: " + str(now))
                else:
                    print("Last measurement was at " + str(lastMeasurement))
                    print("Time over for a new measurement. Time is now: " + str(now))
                time_measured = time.time()

                if measurementIsRunning.value == 0:
                    q = Queue()
                    p = Process(target=measure, args=(offline, debug, ts_channels, filtered_temperature, ds18b20Sensors, bme680Sensors, bme680IsInitialized, dhtSensors, tcSensors, bme280Sensors, weightSensors, hxInits, connectionErrors, measurementIsRunning))
                    p.start()
                    p.join()
                else:
                    error_log("Warning: Forerun measurement is not finished yet. Consider increasing interval.")

                # stop measurements after uploading once
                if interval == 1:
                    print("Only one measurement was set => stop measurements.")
                    measurement_stop.set()

                    if shutdownAfterTransfer:
                        print("Shutting down was set => Waiting 10seconds and then shutdown.")
                        time.sleep(10)
                        shutdown()

            time.sleep(6) # wait 6 seconds before next measurement check

        end_time = time.time()
        time_taken = end_time - start_time # time_taken is in seconds
        time_taken_s = float("{0:.2f}".format(time_taken)) # remove microseconds
        print("Measurement-Script runtime was " + str(time_taken_s) + " seconds.")

    except Exception as e:
        error_log(e, "Unhandled Exception while Measurement")
        if not debug:
            time.sleep(10)
            reboot()
