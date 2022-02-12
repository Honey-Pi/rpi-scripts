#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.
# Changelog 05.12.2020: New sensors ATH10, SHT31 and HDC1080(1008)

import superglobal
import math
import threading
import time
from datetime import datetime, timedelta

import logging

from pprint import pprint
from multiprocessing import Process, Queue, Value

import RPi.GPIO as GPIO
import requests
import json

from read_pcf8591 import get_raw_voltage
from read_bme680 import initBME680FromMain, burn_in_bme680, burn_in_time
from read_ds18b20 import read_unfiltered_temperatur_values, filtered_temperature, checkIfSensorExistsInArray
from read_hx711 import init_hx711
from read_gps import init_gps

from read_settings import get_settings, get_sensors
from utilities import reboot, shutdown, start_single, stop_single, clean_fields, update_wittypi_schedule, getStateFromStorage, setStateToStorage, blink_led, check_undervoltage, thingspeak_datetime
from write_csv import write_csv
from measurement import measure_all_sensors
from thingspeak import transfer_all_channels_to_ts

logger = logging.getLogger('HoneyPi.read_and_upload_all')
superglobal = superglobal.SuperGlobal()

def manage_transfer_to_ts(ts_channels, ts_fields, server_url, offline, debug, ts_datetime):
    try:
        # update ThingSpeak / transfer values
        connectionErrorHappened = transfer_all_channels_to_ts(ts_channels, ts_fields, server_url, debug, ts_datetime)

        if connectionErrorHappened:
            # Write to CSV-File if ConnectionError occured
            if offline == 2:
                s = write_csv(ts_fields, ts_channels, ts_datetime)
                if s and debug:
                    logger.info("Data succesfully saved to CSV-File.")

        return connectionErrorHappened
    except Exception as ex:
        logger.exception("Exception during manage_transfer_to_ts")

def measure(q, offline, debug, ts_channels, ts_server_url, filtered_temperature, ds18b20Sensors, bme680Sensors, bme680Inits, dhtSensors, aht10Sensors, sht31Sensors, sht25Sensors, hdc1008Sensors, bh1750Sensors, tcSensors, bme280Sensors, pcf8591Sensors, ee895Sensors, gpsSensors, weightSensors, hxInits, connectionErrors, measurementIsRunning):
    measurementIsRunning.value = 1 # set flag
    ts_fields = {}
    try:
        ts_fields, bme680Inits = measure_all_sensors(debug, filtered_temperature, ds18b20Sensors, bme680Sensors, bme680Inits, dhtSensors, aht10Sensors, sht31Sensors, sht25Sensors, hdc1008Sensors, bh1750Sensors, tcSensors, bme280Sensors, pcf8591Sensors, ee895Sensors, gpsSensors, weightSensors, hxInits)
        if len(ts_fields) > 0:
            ts_datetime=thingspeak_datetime()
            if offline == 1 or offline == 3:
                try:
                    s = write_csv(ts_fields, ts_channels, ts_datetime)
                    if s and debug:
                        logger.info("Data succesfully saved to CSV-File.")
                except Exception as ex:
                    logger.exception("Exception in measure / write_csv")

            # if transfer to thingspeak is set
            if (offline == 0 or offline == 1 or offline == 2) and ts_channels:
                # update ThingSpeak / transfer values
                connectionErrorHappened = manage_transfer_to_ts(ts_channels, ts_fields, ts_server_url, offline, debug, ts_datetime)

                if connectionErrorHappened:
                    MAX_RETRIES_IN_A_ROW = 3
                    # Do Rebooting if to many connectionErrors in a row
                    connectionErrors.value +=1
                    logger.error("Failed internet connection. Count: " + str(connectionErrors.value) + "/" + str(MAX_RETRIES_IN_A_ROW))
                    if connectionErrors.value >= MAX_RETRIES_IN_A_ROW:
                        if not debug:
                            logger.critical("Too many Connection Errors in a row => Rebooting Raspberry")
                            time.sleep(4)
                            if superglobal.isMaintenanceActive is None:
                                superglobal.isMaintenanceActive = False
                                logger.warning("Set initial state of isMaintenanceActive in read and uplodd: '" + str(superglobal.isMaintenanceActive) + "'")
                            logger.debug("Value of 'isMaintenanceActive' is: " + str(superglobal.isMaintenanceActive))
                            while superglobal.isMaintenanceActive:
                                logger.info("Too many Connection Errors in a row but rebooting delayed due to maintenance mode is active!")
                                logger.debug("Value of 'isMaintenanceActive' is: " + str(superglobal.isMaintenanceActive))
                                time.sleep(10)
                            reboot(settings)
                        else:
                            logger.critical("Too many Connection Errors in a row but did not reboot because console debug mode is enabled.")
                else:
                    if connectionErrors.value > 0:
                        if debug:
                            logger.warning("Connection Errors (" + str(connectionErrors.value) + ") Counting resetet because transfer succeded.")
                        # reset connectionErrors because transfer succeded
                        connectionErrors.value = 0

        elif debug:
            logger.info("No measurement data to send.")

    except Exception as ex:
        logger.exception("Exception during measure (outer).")
    measurementIsRunning.value = 0 # clear flag


def check_wittypi_voltage(time_measured_Voltage, wittyPi, pcf8591Sensors, isLowVoltage, interval, shutdownAfterTransfer, pcf8591Sensorforvoltagecheck=0):
    try:
        if wittyPi["voltagecheck_enabled"] and wittyPi["enabled"]:
            intervalVoltageCheck = 60
            time_now = time.time()
            isTimeToCheckVoltage = (time_now-time_measured_Voltage >= intervalVoltageCheck)
            if isTimeToCheckVoltage:
                if pcf8591Sensors and len(pcf8591Sensors) > 0:
                    logger.debug(str(pcf8591Sensors[pcf8591Sensorforvoltagecheck]))
                    voltage = get_raw_voltage(pcf8591Sensors[pcf8591Sensorforvoltagecheck])
                    if voltage is not None:
                        now = time.strftime("%H:%M", time.localtime(time_now))
                        logger.debug("Voltage Check at " + str(now) + ": " + str(voltage) + " Volt")
                        if voltage <= wittyPi["low"]["voltage"]:
                            if (isLowVoltage == False) or (isLowVoltage is None):
                                logger.debug("Running on low voltage, was above low voltage last measurement!")
                                if wittyPi["low"]["enabled"]:
                                    logger.info("Enable wittyPi low voltage settings!")
                                    update_wittypi_schedule(wittyPi["low"]["schedule"])
                                else:
                                    logger.warning("Low voltage but wittyPi disabled!")
                                    update_wittypi_schedule("")
                                interval = wittyPi["low"]["interval"]
                                shutdownAfterTransfer = wittyPi["low"]["shutdownAfterTransfer"]
                                isLowVoltage = setStateToStorage('isLowVoltage', True)
                                logger.info("New Interval: '" + str(interval) + "', Shutdown after transfer is '" + str(shutdownAfterTransfer)  +"'")
                            else:
                                logger.debug("Running on low voltage, was on low voltage last measurement!")
                        elif voltage < wittyPi["normal"]["voltage"]:
                            if (isLowVoltage == False) or (isLowVoltage is None):
                                logger.debug("Not yet low voltage but below recovery voltage")
                            else:
                                logger.debug("No longer low voltage but recovery / normal voltage not reached")
                        elif voltage >= wittyPi["normal"]["voltage"]:
                            if (isLowVoltage == True) or (isLowVoltage is None):
                                logger.debug("Running on normal voltage, was below recovery / normal voltage last measurement!")
                                if wittyPi["normal"]["enabled"]:
                                    logger.info("Enable wittyPi normal voltage settings!")
                                    update_wittypi_schedule(wittyPi["normal"]["schedule"])
                                else:
                                    logger.info("Normal voltage but wittyPi disabled!")
                                    update_wittypi_schedule("")
                                    interval = wittyPi["normal"]["interval"]
                                    shutdownAfterTransfer = wittyPi["normal"]["shutdownAfterTransfer"]
                                isLowVoltage = setStateToStorage('isLowVoltage', False)
                                logger.info("New Interval: '" + str(interval) + "', Shutdown after transfer is '" + str(shutdownAfterTransfer)  +"'")
                            else:
                                logger.debug("Running on normal voltage, was on normal voltage last measurement!")
                        else:
                            logger.error("Choosen WittyPi Voltage settings irregular Voltage Normal should be higher than Undervoltage")
                    else:
                        logger.error("Voltagesensor did not return a value!")
                else:
                    logger.error("WittyPi Voltage checks enabled but no pcf8591Sensors configured")
                    time_measured_Voltage = time.time()
            else:
                logger.debug("No Voltage Check due")

        return (time_measured_Voltage, interval, shutdownAfterTransfer, isLowVoltage)
    except Exception as ex:
        logger.exception("Exception during check_wittypi_voltage")
        measurementIsRunning.value = 0 # clear flag

def start_measurement(measurement_stop):
    settings = get_settings()
    try:
        global burn_in_time
        start_time = time.time()

        # load settings

        ts_channels = settings["ts_channels"] # ThingSpeak data (ts_channel_id, ts_write_key)
        ts_server_url = settings["ts_server_url"]
        debuglevel = settings["debuglevel"]
        if debuglevel <= 10:
            debug = True # flag to enable debug mode (HDMI output enabled and no rebooting)
        else:
            debug = False # flag to enable debug mode (HDMI output enabled and no rebooting)

        wittyPi = settings["wittyPi"]
        offline = settings["offline"] # flag to enable offline csv storage

        isLowVoltage = getStateFromStorage('isLowVoltage', False)
        if isLowVoltage == True:
            interval = wittyPi["low"]["interval"]
            shutdownAfterTransfer = wittyPi["low"]["shutdownAfterTransfer"]
        else:
            interval = wittyPi["normal"]["interval"]
            shutdownAfterTransfer = wittyPi["normal"]["shutdownAfterTransfer"]

        if debug:
            logger.info("The measurements have started.")

        # with process shared variables
        connectionErrors = Value('i',0)
        measurementIsRunning = Value('i',0)

        if interval and not isinstance(interval, int) or interval == 0:
            interval = 0
            logger.info("Stop measurement because interval is null.")
            measurement_stop.set()

        # read configured sensors from settings.json
        gpsSensors = get_sensors(settings, 99)
        ds18b20Sensors = get_sensors(settings, 0)
        bme680Sensors = get_sensors(settings, 1)
        weightSensors = get_sensors(settings, 2)
        dhtSensors = get_sensors(settings, 3)
        tcSensors = get_sensors(settings, 4)
        bme280Sensors = get_sensors(settings, 5)
        pcf8591Sensors = get_sensors(settings, 6)
        ee895Sensors = get_sensors(settings, 7)
        hdc1008Sensors = get_sensors(settings, 8)
        sht31Sensors = get_sensors(settings, 9)
        aht10Sensors = get_sensors(settings, 10)
        bh1750Sensors = get_sensors(settings, 11)
        sht25Sensors = get_sensors(settings, 12)
        bme680Inits = []

        # -- Run Pre Configuration --
        # if bme680 is configured
        for (sensorIndex, bme680Sensor) in enumerate(bme680Sensors):
            bme680Init = {}
            if 'burn_in_time' in bme680Sensor:
                burn_in_time = bme680Sensor["burn_in_time"]
            sensor = initBME680FromMain(bme680Sensor)
            bme680Init['sensor'] = sensor
            if 'ts_field_air_quality' in bme680Sensor:
                gas_baseline = burn_in_bme680(sensor, burn_in_time)
            else:
                gas_baseline = None
            bme680Init['gas_baseline'] = gas_baseline
            bme680Inits.append(bme680Init)

        # if GPS PA1010D is configured
        if gpsSensors and len(gpsSensors) == 1:
            init_gps(gpsSensors[0])

        # if hx711 is set
        hxInits = []
        for (i, sensor) in enumerate(weightSensors):
            _hx = init_hx711(sensor)
            hxInits.append(_hx)

        # PCF8591
        for (i, pcf8591Sensor) in enumerate(pcf8591Sensors):
            voltage = get_raw_voltage(pcf8591Sensor) # initial measurement as first measurement is always wrong

        # -- End Pre Configuration --

        # start at -6 because we want to get 6 values before we can filter some out
        counter = -6
        time_measured = 0
        time_measured_Voltage = 0

        # Main loop which checks every second
        while not measurement_stop.is_set():
            counter += 1
            time_now = time.time()

            for (sensorIndex, sensor) in enumerate(ds18b20Sensors):
                checkIfSensorExistsInArray(sensorIndex)
                if 'device_id' in sensor:
                    read_unfiltered_temperatur_values(sensorIndex, sensor)

            time_measured_Voltage, interval, shutdownAfterTransfer, isLowVoltage = check_wittypi_voltage(time_measured_Voltage, wittyPi, pcf8591Sensors, isLowVoltage, interval, shutdownAfterTransfer)

            # wait seconds of interval before next check
            # free ThingSpeak account has an upload limit of 15 seconds
            isTimeToMeasure = ((time_now-time_measured >= interval) or (interval == 1)) and counter > 0
            if isTimeToMeasure:
                now = datetime.now()
                if time_measured == 0:
                    logger.info("First time doing a measurement. Time is now: " + str(now.strftime('%Y-%m-%d %H:%M')))
                else:
                    logger.debug("Last measurement was at " + str(superglobal.lastmeasurement.strftime('%Y-%m-%d %H:%M')))
                    logger.info("Time over for a new measurement. Time is now: " + str(now.strftime('%Y-%m-%d %H:%M')))

                # Decide if Thread finished and new measurement can be run
                startNewMeasurement = False
                if measurementIsRunning.value == 0:
                    startNewMeasurement = True
                #if measurementIsRunning.value == 1 and time_measured-interval >= time_now-10*60: #untested
                #    logger.warning("A previous measurement is still not finished! A measurement propaply cancelled somehow. But we keep measuring because the previous, canceled measurement was 10 minutes ago.")
                #    startNewMeasurement = True

                # update variables with new timestamps of this new meassurement
                time_measured = time.time()
                superglobal.lastmeasurement = now
                superglobal.nextmeasurement = now + timedelta(seconds=1) * interval

                # TODO Add description what and why this is checked here. What means 0x7?
                check_undervoltage('0x7')

                if startNewMeasurement:
                    q = Queue()
                    p = Process(target=measure, args=(q, offline, debug, ts_channels, ts_server_url, filtered_temperature, ds18b20Sensors, bme680Sensors, bme680Inits, dhtSensors, aht10Sensors, sht31Sensors, sht25Sensors, hdc1008Sensors, bh1750Sensors, tcSensors, bme280Sensors, pcf8591Sensors, ee895Sensors, gpsSensors, weightSensors, hxInits, connectionErrors, measurementIsRunning))
                    p.start()
                    if interval == 1:
                        timeouttime=timedelta(seconds=300)
                    else:
                        timeouttime=superglobal.nextmeasurement - now
                    logger.debug("Remaining time for thread: " + str(timeouttime.total_seconds()) + " seconds")
                    p.join(timeout=timeouttime.total_seconds())
                    if p.is_alive():
                        logger.warning("Measurement is still not finished. Waiting 5 seconds before killing process.")
                        time.sleep(5)
                        logger.debug("Killing unfinished measurement process.")
                        p.terminate()
                        measurementIsRunning.value = 0

                else:
                    logger.warning("Forerun measurement is not finished yet. Consider increasing interval.")

                # stop measurements after uploading once
                if interval == 1:
                    logger.debug("Only one measurement was set => stop measurements.")
                    measurement_stop.set()

                    if shutdownAfterTransfer:
                        if superglobal.isMaintenanceActive is None:
                            superglobal.isMaintenanceActive = False
                            logger.warning("Set initial state of isMaintenanceActive in read and uplodd: '" + str(superglobal.isMaintenanceActive) + "'")
                        logger.debug("Value of 'isMaintenanceActive' is: " + str(superglobal.isMaintenanceActive))
                        while superglobal.isMaintenanceActive:
                            logger.info("Shutting down was set but Maintenance mode is active, delaying shutdown!")
                            logger.debug("Value of 'isMaintenanceActive' is: " + str(superglobal.isMaintenanceActive))
                            time.sleep(10)
                        logger.info("Shutting down was set => Waiting 10seconds and then shutdown.")
                        tblink = threading.Thread(target=blink_led, args = (settings["led_pin"], 0.25))
                        tblink.start()
                        time.sleep(10)
                        shutdown(settings)

            time.sleep(6) # wait 6 seconds before next measurement check

        end_time = time.time()
        time_taken = end_time - start_time # time_taken is in seconds
        time_taken_s = float("{0:.2f}".format(time_taken)) # remove microseconds
        logger.debug("Measurement-Script runtime was " + str(time_taken_s) + " seconds.")

    except Exception as ex:
        logger.exception("Unhandled Exception in start_measurement")
        if not debug:
            time.sleep(10)
            reboot(settings)
