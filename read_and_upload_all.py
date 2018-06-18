import math
import sys
import threading
from pprint import pprint
from time import sleep
from urllib2 import HTTPError

import RPi.GPIO as GPIO
import numpy
import thingspeak

from read_bme680 import measure_bme680, burn_in_bme680
from read_ds18b20 import get_temperature
from read_hx711 import measure_weight
from read_settings import get_settings, get_sensors


settings = get_settings()

# ThingSpeak data
channel_id = settings["ts_channel_id"]
write_key = settings["ts_write_key"]
interval = settings["interval"]

filtered_temperature = []  # here we keep the temperature values after removing outliers
filtered_humidity = []  # here we keep the filtered humidity values after removing the outliers

lock = threading.Lock()  # we are using locks so we don't have conflicts while accessing the shared variables
event = threading.Event()  # we are using an event so we can close the thread as soon as KeyboardInterrupt is raised


# function for processing the data
def read_values():
    records = 10 # after this many records we make a record
    values = []

    while not event.is_set():
        counter = 0
        while counter < records and not event.is_set():
            temperature = None
            try:
                temperature = get_temperature(get_sensors(0)[0])
                print "temperature: " + str(temperature)
            except IOError:
                print "IOError occurred"    
            except TypeError:
                print "TypeError occurred"

            if math.isnan(temperature) == False:
                values.append(temperature)
                counter += 1
                
            sleep(3)

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
    print("Stop Thread!")

def close_script():
    event.set()
    print("Exit Script!")
    sys.exit()

def start_read_and_upload_all():
    # bme680 sensor must be burned in before use
    gas_baseline = burn_in_bme680()
    
    # if burning was canceled=> exit
    if gas_baseline is None:
        print "gas_baseline can't be None"
        stop_read_and_upload_all()

    # here we start the thread
    # we use a thread in order to gather/process the data separately from the printing process
    data_collector = threading.Thread(target=read_values)
    data_collector.start()

    # ThingSpeak channel
    channel = thingspeak.Channel(id=channel_id, write_key=write_key)

    while not event.is_set():
        if len(filtered_temperature) > 0:  # or we could have used filtered_humidity instead
            lock.acquire()

            # dict with all fields and values with will be tranfered later to ThingSpeak
            ts_fields = {}

            # here you can do whatever you want with the variables: print them, file them out, anything
            
            # measure sensor with type 0
            ds18b20_temperature = filtered_temperature.pop()
            ts_field_ds18b20 = get_sensors(0)[0]["ts_field"]
            ts_fields.update({ts_field_ds18b20: ds18b20_temperature})

            # measure BME680 (can only be once)
            bme680_values = measure_bme680(gas_baseline, get_sensors(1)[0])
            ts_fields.update(bme680_values)

            # measure every sensor with type 2
            for (i, sensor) in enumerate(get_sensors(2)):
                weight = measure_weight(sensor)
                ts_fields.update(weight)

            # print measurement values for debug reasons
            for key, value in ts_fields.iteritems():
                print key + ": " + str(value)
            
            try:
                # update ThingSpeak / transfer values
                channel.update(ts_fields)
            except HTTPError:
                print "HTTPError occurred"  

            lock.release()

        # wait seconds of interval before next check
        # free ThingSpeak account has an upload limit of 15 seconds
        sleep(interval)

    # wait until the thread is finished
    data_collector.join()
