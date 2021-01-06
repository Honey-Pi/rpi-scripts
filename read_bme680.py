#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import time
import bme680
import smbus
from sensors.sensor_utilities import get_smbus, computeAbsoluteHumidity 

# global vars
sensor = None
bme680IsConnected = 0
gas_baseline = 0

def isSMBusConnected():
    try:
        bus = smbus.SMBus(get_smbus())
        return 1
    except Exception as ex:
        pass #print("No BME680 connected: " + str(ex))
    return 0

def initBME680(ts_sensor):
    global sensor
    try:
        # setup BME680 sensor
        try:
            i2c_addr = ts_sensor["i2c_addr"]
        except:
            i2c_addr = "0x76"
            # setup BME680 sensor
        if i2c_addr == "0x76":
            sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
        elif i2c_addr == "0x77":
            sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

        try:
            offset = float(ts_sensor["offset"])
            print('BME680: The Temperature Offset is ' + str(offset) + ' °C')
        except:
            offset = 0
            #print('BME680: The Temperature Offset is default: ' + str(offset) + '°C')

        # These oversampling settings can be tweaked to change the balance between accuracy and noise in the data.
        sensor.set_humidity_oversample(bme680.OS_2X)
        sensor.set_pressure_oversample(bme680.OS_4X)
        sensor.set_temperature_oversample(bme680.OS_8X)
        sensor.set_filter(bme680.FILTER_SIZE_3)
        sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
        sensor.set_temp_offset(offset)
        sensor.set_gas_heater_temperature(320)
        sensor.set_gas_heater_duration(150)
        sensor.select_gas_heater_profile(0)

        return 1
    except IOError as ex:
        if str(ex) == "[Errno 121] Remote I/O error":
            print("Initializing BME680 failed: Most likely wrong Sensor Chip-ID or sensor not connected.")
        else:
            print("Initializing BME680 failed: " + str(ex))
    return 0

def initBME680FromMain(ts_sensor):
    if isSMBusConnected():
        return initBME680(ts_sensor)
    else:
        print("No I2C sensor connected to SMBus. Please check sensor or remove BME680 from settings.")
        return 0

def burn_in_bme680(sensor, burn_in_time):
    try:
        # Collect gas resistance burn-in values, then use the average
        # of the last 50 values to set the upper limit for calculating
        # gas_baseline.

        # start_time and curr_time ensure that the burn_in_time (in seconds) is kept track of.
        start_time = time.time()
        curr_time = time.time()

        burn_in_data = []
        while curr_time - start_time < burn_in_time:
            curr_time = time.time()
            if sensor.get_sensor_data() and sensor.data.heat_stable:
                gas = sensor.data.gas_resistance
                burn_in_data.append(gas)
                # log time for burning process
                #print("Burning BME680 in for " + str(int(round(burn_in_time - (curr_time - start_time)))) + "s.")
                #print('Gas: {0:.2f}Ohms'.format(gas))
                time.sleep(1)
            else:
                time.sleep(0.4) # wait 400ms for heat_stable
        gas_baseline = sum(burn_in_data[-burn_in_time:]) / burn_in_time
        #print('Gas Baseline: {0:.2f} Ohms'.format(gas_baseline))
        return gas_baseline
    except NameError:
        print("Sensor BME680 is not connected.")
    except KeyboardInterrupt:
        print("Burning BME680 interruped by Keyboard.")
    return None

def calc_air_quality(sensor, gas_baseline):
    # Set the humidity baseline to 40%, an optimal indoor humidity.
    hum_baseline = 40.0
    # This sets the balance between humidity and gas reading in the
    # calculation of air_quality_score (25:75, humidity:gas)
    hum_weighting = 0.25
    
    temp = sensor.data.temperature

    gas = sensor.data.gas_resistance
    gas_offset = gas_baseline - gas

    hum = sensor.data.humidity
    hum_offset = hum - hum_baseline

    # Calculate hum_score as the distance from the hum_baseline.
    if hum_offset > 0:
        hum_score = (100 - hum_baseline - hum_offset)
        hum_score /= (100 - hum_baseline)
        hum_score *= (hum_weighting * 100)

    else:
        hum_score = (hum_baseline + hum_offset)
        hum_score /= hum_baseline
        hum_score *= (hum_weighting * 100)

    # Calculate gas_score as the distance from the gas_baseline.
    if gas_offset > 0:
        gas_score = (gas / gas_baseline)
        gas_score *= (100 - (hum_weighting * 100))

    else:
        gas_score = 100 - (hum_weighting * 100)

    # Calculate air_quality_score.
    air_quality_score = hum_score + gas_score
    absoluteHumidity = computeAbsoluteHumidity(hum, temp)

    print('BME680 Gas: {0:.2f} Ohms, humidity: {1:.2f} %RH, air quality: {2:.2f}, absolute humidity: {3:.2f} g/m³'.format(gas,hum,air_quality_score,absoluteHumidity))
    return air_quality_score


def measure_bme680(ts_sensor, burn_in_time=30):
    global sensor, gas_baseline
    start_time = time.time()
    curr_time = time.time()
    max_time = 30 # max seconds to wait for heat_stable
    while curr_time - start_time < max_time:
        curr_time = time.time()
        if sensor.get_sensor_data() and sensor.data.heat_stable:
            temperature = sensor.data.temperature
            humidity = sensor.data.humidity
            air_pressure = sensor.data.pressure

            # ThingSpeak fields
            # Create returned dict if ts-field is defined
            fields = {}
            if 'ts_field_temperature' in ts_sensor:
                fields[ts_sensor["ts_field_temperature"]] = temperature
            if 'ts_field_humidity' in ts_sensor:
                fields[ts_sensor["ts_field_humidity"]] = humidity
            if 'ts_field_air_pressure' in ts_sensor:
                fields[ts_sensor["ts_field_air_pressure"]] = air_pressure
            if 'ts_field_air_quality' in ts_sensor:
                if not gas_baseline:
                    gas_baseline = burn_in_bme680(sensor, burn_in_time)
                # Calculate air_quality_score.
                if gas_baseline:
                    air_quality_score = calc_air_quality(sensor, gas_baseline)
                    # round to 0 digits
                    fields[ts_sensor["ts_field_air_quality"]] = int(round(air_quality_score, 0))

            return fields
        # Waiting for heat_stable
        time.sleep(0.4)

    # error
    return {}
