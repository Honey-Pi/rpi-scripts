import sys
import time
from pprint import pprint

import RPi.GPIO as GPIO
import bme680
import thingspeak

from hx711 import HX711
from read_ds18b20 import get_temperature
from read_settings import get_settings

settings = pprint(get_settings())

# ThingSpeak data
channel_id = settings["ts_channel_id"]
write_key = settings["ts_write_key"]
interval = settings["sensors"][2]

# ThingSpeak fields
ts_field_outdoor_temperature = settings["sensors"][0]["ts_field_indoor_temperature"]
ts_field_indoor_temperature = settings["sensors"][1]["ts_field_temperature"]
ts_field_humidity = settings["sensors"][1]["ts_field_humidity"]
ts_field_air_pressure = settings["sensors"][1]["ts_field_air_pressure"]
ts_field_air_quality = settings["sensors"][1]["ts_field_air_quality"]
ts_field_weight = settings["sensors"][2]["ts_field_weight"]

# weight sensor pins
pin_dt = settings["sensors"][2]["pin_dt"]
pin_sck = settings["sensors"][2]["pin_sck"]

# setup weight sensor
hx = HX711(pin_dt, pin_sck)
hx.set_reading_format("LSB", "MSB")

# HOW TO CALCULATE THE REFFERENCE UNIT
# To set the reference unit to 1. Put 1kg on your sensor or anything you have and know exactly how much it weights.
# In this case, 92 is 1 gram because, with 1 as a reference unit I got numbers near 0 without any weight
# and I got numbers around 184000 when I added 2kg. So, according to the rule of thirds:
# If 2000 grams is 184000 then 1000 grams is 184000 / 2000 = 92.
# hx.set_reference_unit(113)
hx.set_reference_unit(92)

hx.reset()
hx.tare()

# setup BME680 sensor
bme680 = bme680.BME680()

# These oversampling settings can be tweaked to change the balance between accuracy and noise in the data.
bme680.set_humidity_oversample(bme680.OS_2X)
bme680.set_pressure_oversample(bme680.OS_4X)
bme680.set_temperature_oversample(bme680.OS_8X)
bme680.set_filter(bme680.FILTER_SIZE_3)
bme680.set_gas_status(bme680.ENABLE_GAS_MEAS)
bme680.set_gas_heater_temperature(320)
bme680.set_gas_heater_duration(150)
bme680.select_gas_heater_profile(0)

# Set the humidity baseline to 40%, an optimal indoor humidity.
hum_baseline = 40.0

# This sets the balance between humidity and gas reading in the
# calculation of air_quality_score (25:75, humidity:gas)
humidity_weighting = 0.25


def clean_and_exit():
    print("Cleaning...")
    GPIO.cleanup()
    print("Bye!")
    sys.exit()


def burn_in_bme680():
    try:
        # Collect gas resistance burn-in values, then use the average
        # of the last 50 values to set the upper limit for calculating
        # gas_baseline.

        # start_time and curr_time ensure that the burn_in_time (in seconds) is kept track of.

        start_time = time.time()
        curr_time = time.time()
        burn_in_time = 300

        burn_in_data = []

        while curr_time - start_time < burn_in_time:
            curr_time = time.time()
            if bme680.get_sensor_data() and bme680.data.heat_stable:
                gas = bme680.data.gas_resistance
                burn_in_data.append(gas)
                time.sleep(1)

        return sum(burn_in_data[-50:]) / 50.0
    except KeyboardInterrupt:
        pass


def measure_and_upload():
    try:
        if bme680.get_sensor_data() and bme680.data.heat_stable:
            outdoor_temperature = bme680.data.temperature
            humidity = bme680.data.humidity
            air_pressure = bme680.data.data_pressure

            gas = bme680.data.gas_resistance
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

            channel.update({ts_field_indoor_temperature: get_temperature(),
                            ts_field_outdoor_temperature: outdoor_temperature,
                            ts_field_humidity: humidity,
                            ts_field_air_pressure: air_pressure,
                            ts_field_air_quality: air_quality,
                            ts_field_weight: hx.get_weight(5)})

            hx.power_down()
            hx.power_up()

    except (KeyboardInterrupt, SystemExit):
        clean_and_exit()


if __name__ == "__main__":
    gas_baseline = burn_in_bme680()
    channel = thingspeak.Channel(id=channel_id, write_key=write_key)
    while True:
        measure_and_upload()
        # free ThingSpeak account has an upload limit of 15 seconds
        time.sleep(interval)
