import math
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
unfiltered_values = [] # here we keep all the unfilteres values

# function for reading the value from sensor
def read_values():
    temperature = None
    try:
        temperature = get_temperature(get_sensors(0)[0])
        print("temperature: " + str(temperature))
        # for testing:
        #weight = measure_weight(get_sensors(2)[0])
        #print(weight)
    except IOError:
        print "IOError occurred"    
    except TypeError:
        print "TypeError occurred"

    if math.isnan(temperature) == False:
        unfiltered_values.append(temperature)

# function which eliminates the noise by using a statistical model
# we determine the standard normal deviation and we exclude anything that goes beyond a threshold
# think of a probability distribution plot - we remove the extremes
# the greater the std_factor, the more "forgiving" is the algorithm with the extreme values
def filter_values(unfiltered_values, std_factor=2):
    mean = numpy.mean(unfiltered_values)
    standard_deviation = numpy.std(unfiltered_values)

    if standard_deviation == 0:
        return unfiltered_values

    final_values = [element for element in unfiltered_values if element > mean - std_factor * standard_deviation]
    final_values = [element for element in final_values if element < mean + std_factor * standard_deviation]

    return final_values

# function for appending the filter
def append_filter():
    # read the last 9 values
    # and filter them
    filtered_temperature.append(numpy.mean(filter_values([x for x in unfiltered_values[-9:]])))

def start_measurement(measurement_stop):
    print("Messungen beginnen")
    
    # reload settings because could be changed
    settings = get_settings()

    # bme680 sensor must be burned in before use
    gas_baseline = burn_in_bme680()
    
    # if burning was canceled=> exit
    if gas_baseline is None:
        print "gas_baseline can't be None"
        measurement_stop.set()

    # ThingSpeak channel
    channel = thingspeak.Channel(id=channel_id, write_key=write_key)

    # start at -10 because we want to get 10 values before we can filter some out
    counter = -10
    while not measurement_stop.is_set():
        # read values from sensors every second
        read_values()

        # wait seconds of interval before next check
        # free ThingSpeak account has an upload limit of 15 seconds
        if counter%interval == 0:
            print("Time over for a new measurement.")

            # filter the values out
            append_filter()

            # if we have at leat one filtered value we can upload
            if len(filtered_temperature) > 0: 

                # dict with all fields and values with will be tranfered later to ThingSpeak
                ts_fields = {}

                # measure sensor with type 0
                ds18b20_temperature = filtered_temperature.pop() # get last value from array
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
        
        counter += 1
        sleep(1)

    print("Measurement-Script runtime was " + str(counter) + " seconds.")