import math
import sys
import threading
from pprint import pprint
from time import sleep

import RPi.GPIO as GPIO
import numpy
import thingspeak

from read_bme680_and_hx711 import measure_other_sensors, burn_in_bme680
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

filtered_temperature = []  # here we keep the temperature values after removing outliers
filtered_humidity = []  # here we keep the filtered humidity values after removing the outliers

lock = threading.Lock()  # we are using locks so we don't have conflicts while accessing the shared variables
event = threading.Event()  # we are using an event so we can close the thread as soon as KeyboardInterrupt is raised


# function for processing the data
def read_values():
    seconds = 10  # after this many second we make a record
    values = []

    while not event.is_set():
        counter = 0
        while counter < seconds and not event.is_set():
            temperature = None
            try:
                temperature = get_temperature()

            except IOError:
                print("IOError occurred")

            if math.isnan(temperature) == False:
                values.append(temperature)
                counter += 1

            sleep(1)

        lock.acquire()
        filtered_temperature.append(numpy.mean(filter_values([x for x in values])))
        lock.release()

        values = []


# function which eliminates the noise by using a statistical model
# we determine the standard normal deviation and we exclude anything that goes beyond a threshold
# think of a probability distribution plot - we remove the extremes
# the greater the std_factor, the more "forgiving" is the algorithm with the extreme values
def filter_values(values, std_factor=2):
    mean = numpy.mean(values)
    standard_deviation = numpy.std(values)

    if standard_deviation == 0:
        return values

    final_values = [element for element in values if element > mean - std_factor * standard_deviation]
    final_values = [element for element in final_values if element < mean + std_factor * standard_deviation]

    return final_values


def stop_read_and_upload_all():
    event.set()
    print("Cleaning...")
    GPIO.cleanup()
    print("Bye!")
    sys.exit()


def start_read_and_upload_all():
    # bme680 sensor must be burned in before use
    gas_baseline = burn_in_bme680()

    # here we start the thread
    # we use a thread in order to gather/process the data separately from the printing process
    data_collector = threading.Thread(target=read_values)
    data_collector.start()

    # ThingSpeak channel
    channel = thingspeak.Channel(id=channel_id, write_key=write_key)

    while not event.is_set():
        if len(filtered_temperature) > 0:  # or we could have used filtered_humidity instead
            lock.acquire()

            # here you can do whatever you want with the variables: print them, file them out, anything
            temperature = filtered_temperature.pop()
            other_sensor_values = measure_other_sensors(gas_baseline)

            channel.update({ts_field_indoor_temperature: temperature,
                            ts_field_outdoor_temperature: other_sensor_values.get("outdoor_temperature"),
                            ts_field_humidity: other_sensor_values.get("humidity"),
                            ts_field_air_pressure: other_sensor_values.get("air_pressure"),
                            ts_field_air_quality: other_sensor_values.get("air_quality"),
                            ts_field_weight: other_sensor_values.get("weight")})

            lock.release()

        # wait seconds of interval before next check
        # free ThingSpeak account has an upload limit of 15 seconds
        sleep(interval)

    # wait until the thread is finished
    data_collector.join()
