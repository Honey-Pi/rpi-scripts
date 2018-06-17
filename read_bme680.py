#!/usr/bin/env python

import time
from pprint import pprint

import bme680

from read_settings import get_settings, get_sensors

# setup BME680 sensor
sensor = bme680.BME680()

# These oversampling settings can be tweaked to change the balance between accuracy and noise in the data.
sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)
sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
sensor.set_gas_heater_temperature(320)
sensor.set_gas_heater_duration(150)
sensor.select_gas_heater_profile(0)

# Set the humidity baseline to 40%, an optimal indoor humidity.
hum_baseline = 40.0

# This sets the balance between humidity and gas reading in the
# calculation of air_quality_score (25:75, humidity:gas)
humidity_weighting = 0.25


def burn_in_bme680():
    try:
        # Collect gas resistance burn-in values, then use the average
        # of the last 50 values to set the upper limit for calculating
        # gas_baseline.

        # start_time and curr_time ensure that the burn_in_time (in seconds) is kept track of.

        start_time = time.time()
        curr_time = time.time()
        burn_in_time = 10

        burn_in_data = []

        while curr_time - start_time < burn_in_time:
            curr_time = time.time()
            if sensor.get_sensor_data() and sensor.data.heat_stable:
                gas = sensor.data.gas_resistance
                burn_in_data.append(gas)
                # log time for burning process
                print "BME680 wird noch " + str(int(round(burn_in_time-(curr_time - start_time)))) + "sec eingebrannt."
                time.sleep(1)

        return sum(burn_in_data[-50:]) / 50.0
    except KeyboardInterrupt:
        return None


def measure_bme680(gas_baseline, ts_sensor):
    if sensor.get_sensor_data() and sensor.data.heat_stable:
        temperature = sensor.data.temperature
        humidity = sensor.data.humidity
        air_pressure = sensor.data.pressure

        gas = sensor.data.gas_resistance
        gas_offset = gas_baseline - gas
        humidity_offset = humidity - hum_baseline

        # Calculate hum_score as the distance from the hum_baseline.
        if humidity_offset > 0:
            hum_score = (100 - hum_baseline - humidity_offset) / (100 - hum_baseline) * (humidity_weighting * 100)

        else:
            hum_score = (hum_baseline + humidity_offset) / hum_baseline * (humidity_weighting * 100)

        # Calculate gas_score as the distance from the gas_baseline.
        if gas_offset > 0:
            gas_score = (gas / gas_baseline) * (100 - (humidity_weighting * 100))

        else:
            gas_score = 100 - (humidity_weighting * 100)

        # Calculate air_quality_score.
        air_quality = hum_score + gas_score

        # ThingSpeak fields
        ts_field_temperature = ts_sensor["ts_field_temperature"]
        ts_field_humidity = ts_sensor["ts_field_humidity"]
        ts_field_air_pressure = ts_sensor["ts_field_air_pressure"]
        ts_field_air_quality = ts_sensor["ts_field_air_quality"]

        return ({ts_field_temperature: temperature,
                 ts_field_humidity: humidity,
                 ts_field_air_pressure: air_pressure,
                 ts_field_air_quality: air_quality})
