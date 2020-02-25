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
import json

from read_pcf8591 import measure_voltage, get_raw_voltage
from read_bme680 import initBME680FromMain
from read_ds18b20 import read_unfiltered_temperatur_values, filtered_temperature, checkIfSensorExistsInArray
from read_hx711 import init_hx711
from read_settings import get_settings, get_sensors
from utilities import reboot, error_log, shutdown, start_single, stop_single, wait_for_internet_connection, clean_fields, update_wittypi_schedule, getStateFromStorage, setStateToStorage
from write_csv import write_csv
from measurement import measure_all_sensors

def send_ts_data(ts_channels, ts_fields, offline, connectionErrors, debug):
    # update ThingSpeak / transfer values
    connectionErrorHappened = transfer_channels_to_ts(ts_channels, ts_fields, connectionErrors, debug)

    if connectionErrorHappened:
        # Write to CSV-File if ConnectionError occured
        if offline == 2:
            s = write_csv(ts_fields, ts_channels)
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

def transfer_channels_to_ts(ts_channels, ts_fields, connectionErrors, debug):
    connectionErrorWithinAnyChannel = []
    for (channelIndex, channel) in enumerate(ts_channels, 0):
        channel_id = channel["ts_channel_id"]
        write_key = channel["ts_write_key"]
        if channel_id and write_key:
            if debug :
                print('Channel ' + str(channelIndex) + ' with ID ' + str(channel_id))
            ts_instance = thingspeak.Channel(id=channel_id, write_key=write_key)
            ts_fields_cleaned = clean_fields(ts_fields, channelIndex, debug)
            connectionError = transfer_channel_to_ts(ts_instance, ts_fields_cleaned, connectionErrors, debug)
            connectionErrorWithinAnyChannel.append(connectionError)
        else:
            error_log("Info: No ThingSpeak upload for this channel (" + str(channelIndex) + ") because because channel_id or write_key is None.")

    return any(c == True for c in connectionErrorWithinAnyChannel)

def transfer_channel_to_ts(ts_instance, ts_fields_cleaned, connectionErrors, debug):
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

def measure(offline, debug, ts_channels, filtered_temperature, ds18b20Sensors, bme680Sensors, bme680IsInitialized, dhtSensors, tcSensors, bme280Sensors, voltageSensors, weightSensors, hxInits, connectionErrors, measurementIsRunning):
    measurementIsRunning.value = 1 # set flag
    ts_fields = {}
    try:
        ts_fields = measure_all_sensors(debug, filtered_temperature, ds18b20Sensors, bme680Sensors, bme680IsInitialized, dhtSensors, tcSensors, bme280Sensors, voltageSensors, weightSensors, hxInits)

        if len(ts_fields) > 0:
            if offline == 1 or offline == 3:
                try:
                    s = write_csv(ts_fields, ts_channels)
                    if s and debug:
                        error_log("Info: Data succesfully saved to CSV-File.")
                except Exception as ex:
                    error_log(ex, "Exception")

            # if transfer to thingspeak is set
            if (offline == 0 or offline == 1 or offline == 2) and ts_channels:
                # update ThingSpeak / transfer values
                send_ts_data(ts_channels, ts_fields, offline, connectionErrors, debug)

        elif debug:
            error_log("Info: No measurement data to send.")

        measurementIsRunning.value = 0 # clear flag

    except Exception as ex:
        error_log(ex, "Exception during measurement")
        measurementIsRunning.value = 0 # clear flag

def start_measurement(measurement_stop):
    try:
        start_time = time.time()

        # load settings
        settings = get_settings()
        ts_channels = settings["ts_channels"] # ThingSpeak data (ts_channel_id, ts_write_key)
        debug = settings["debug"] # flag to enable debug mode (HDMI output enabled and no rebooting)
        wittyPi = settings["wittyPi"]
        intervalVoltageCheck = 60
        isLowVoltage = getStateFromStorage('isLowVoltage', False)
        interval = wittyPi["normal"]["interval"]
        shutdownAfterTransfer = wittyPi["normal"]["shutdownAfterTransfer"]
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
        voltageSensors = get_sensors(settings, 6)

        # -- Run Pre Configuration --
        # if bme680 is configured
        if bme680Sensors and len(bme680Sensors) == 1:
            bme680IsInitialized = initBME680FromMain(bme680Sensors)
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
        time_measured_Voltage = 0
        if voltageSensors and len(voltageSensors) == 1:
            voltage = get_raw_voltage(0) #initial measurement as first measurement is always wrong
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
            if wittyPi["voltagecheck_enabled"]:
                isTimeToCheckVoltage = (time_now-time_measured_Voltage >= intervalVoltageCheck)
                if isTimeToCheckVoltage:
                    if voltageSensors and len(voltageSensors) == 1:
                        voltage = get_raw_voltage(0)
                        now = time.strftime("%H:%M", time.localtime(time_now))
                        print("Voltage Check at " + str(now) + ": " + str(voltage) + " Volt")
                        if voltage <= wittyPi["low"]["voltage"]:
                            print("Running on low voltage")
                            if not isLowVoltage:
                                if wittyPi["low"]["enabled"]:
                                    update_wittypi_schedule(wittyPi["low"]["schedule"])
                                else:
                                    update_wittypi_schedule("")
                                interval = wittyPi["low"]["interval"]
                                shutdownAfterTransfer = wittyPi["low"]["shutdownAfterTransfer"]
                                isLowVoltage = setStateToStorage('isLowVoltage', True)
                        elif voltage < wittyPi["normal"]["voltage"]:
                            print("No longer low voltage but recovery voltage not reached")
                        elif voltage >= wittyPi["voltage_normal"]:
                            print("Running on normal voltage")
                            if isLowVoltage:
                                if wittyPi["normal"]["enabled"]:
                                    update_wittypi_schedule(wittyPi["normal"]["schedule"])
                                else:
                                    update_wittypi_schedule("")
                                    interval = wittyPi["normal"]["interval"]
                                    shutdownAfterTransfer = wittyPi["normal"]["shutdownAfterTransfer"]
                                isLowVoltage = setStateToStorage('isLowVoltage', False)
                        else:
                            error_log("Choosen WittyPi Voltage settings irregular Voltage Normal should be higher than Undervoltage")
                    else:
                        error_log("WittyPi Voltage checks enabled but no VoltageSensors configured")
                    time_measured_Voltage = time.time()
                else:
                    print("No Voltage Check due")

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
                    p = Process(target=measure, args=(offline, debug, ts_channels, filtered_temperature, ds18b20Sensors, bme680Sensors, bme680IsInitialized, dhtSensors, tcSensors, bme280Sensors, voltageSensors, weightSensors, hxInits, connectionErrors, measurementIsRunning))
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
