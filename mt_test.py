#!/usr/bin/python
# -*- coding: utf-8 -*-

import multiprocessing
from multiprocessing import Value
import threading
import queue
import time
import math
import json
from ds18b20 import DS18B20
from read_settings import get_settings, get_sensors

import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger('HoneyPi.mt_test')

import time

measurement_stop = threading.Event()
a=Value('f', 8)
#toto=8



# function which eliminates the noise by using a statistical model
# we determine the standard normal deviation and we exclude anything that goes beyond a threshold
# think of a probability distribution plot - we remove the extremes
# the greater the std_factor, the more "forgiving" is the algorithm with the extreme values

global unfiltered_values 
global filtered_temperature
unfiltered_values = [] # here we keep all the unfilteres values
filtered_temperature = [] # here we keep all the filteres values


def filter_values(unfiltered_values, std_factor=2):
    try:
        mean = np.mean(unfiltered_values)
        standard_deviation = np.std(unfiltered_values)

        if standard_deviation == 0:
            return unfiltered_values

        final_values = [element for element in unfiltered_values if element > mean - std_factor * standard_deviation]
        final_values = [element for element in final_values if element < mean + std_factor * standard_deviation]

        return final_values
    except Exception as ex:
        logger.exception("Unhandled Exception in filter_values")

# function for appending the filter
def filter_temperatur_values():
    try:
        if len(unfiltered_values) > 5:
            # read the last 5 values and filter them
            filtered_temperature.append(np.mean(filter_values([x for x in unfiltered_values[-5:]])))
    except Exception as ex:
        logger.exception("Unhandled Exception in filter_temperatur_values")

def worker_w_queue(queue, sensor, results):
    try:
        global unfiltered_values , filtered_temperature
        #name = multiprocessing.current_process().name
        name =  threading.currentThread().getName()
        #sensor = DS18B20(sensor["device_id"])
        #sensors = []
        print("Worker for sensor: " + str(sensor))
        DS18B20_sensor = DS18B20(sensor['device_id'].replace("28-",""))

        while not measurement_stop.is_set():
            temperature = DS18B20_sensor.get_temperature()
            if temperature is not None and math.isnan(temperature) == False:
                print("Sensor %s has temperature %.2f" % (sensor['device_id'], temperature))
                unfiltered_values.append(temperature)
                if len(filtered_temperature) > 50:
                    filtered_temperature = filtered_temperature[sensorIndex][len(filtered_temperature[sensorIndex])-10:] # remove all but the last 10 elements
                if len(unfiltered_values) > 50:
                    unfiltered_values = unfiltered_values[len(unfiltered_values)-10:] # remove all but the last 10 elements
            if not queue.empty():
                work = queue.get()
                #a.acquire()
                #a.value=i
                #a.release()
                if (work == sensor['device_id']):
                #queue.put((sensor))
                    print ('Worker' + name + 'found request for ' + str(work) + 'my sensor, working on result')
                    ds18b20_temperature = None
                    if filtered_temperature is not None and len(filtered_temperature) > 0:
                    # if we have at leat one filtered value we can upload
                        ds18b20_temperature = filtered_temperature.pop()
                    if ds18b20_temperature is not None:
                        if 'offset' in sensor and sensor["offset"] is not None:
                            ds18b20_temperature = ds18b20_temperature-float(sensor["offset"])
                        ds18b20_temperature = float("{0:.2f}".format(ds18b20_temperature)) # round to two decimals
                    elif temperature is not None:
                        # Case for filtered_temperature was not filled, use direct measured temperture in this case
                        ds18b20_temperature = temperature
                    if ds18b20_temperature is not None:
                        result={}
                        result['type']=sensor['type']
                        result['device_id']=sensor['device_id']
                        result['temperature']=ds18b20_temperature
                        print ('Worker' + name + 'sending result ' + str(result))
                        results.put(result)
                        queue.task_done()
                else:
                    print ('Worker' + name + 'found request for ' + str(work) + ' not my sensor')
    except Exception as e:
        print(e)

def my_service(ds18b20queues, results, sensors):
    try:
        #name = multiprocessing.current_process().name
        name = threading.currentThread().getName() 
        # print (name,"Starting")
        # time.sleep(3)
        # print (name, "Exiting")
        while not measurement_stop.is_set():
            
                #az.acquire()
                #print ("my_service=",az.value)
                for (queueindex, ds18b20queue) in enumerate(ds18b20queues):
                    ds18b20queue.put(sensors[queueindex]["device_id"])
                    print('Put work Job for ' + sensors[queueindex]["device_id"])
                for ds18b20queue in ds18b20queues:
                    ds18b20queue.join()
                time.sleep(1)
                while not results.empty():
                    print("result received:" + str(results.get()))
                    results.task_done()
                #az.release()
                
                time.sleep(10)
    except Exception as e:
        print('Exception in my_service' + repr(e))




if __name__ == '__main__':

    settings = get_settings()
    ds18b20Sensors = get_sensors(settings, 0)

    results = queue.Queue()
    #queue.put(sensor)
    measurement_stop.clear()
    #Process(target=worker).start()
    ds18b20queues = []
    ds18b20threads = []
    for sensor in ds18b20Sensors:
        print('Creating worker ' + str(sensor))
        time.sleep(2)
        ds18b20queue = queue.Queue()
        ds18b20worker = threading.Thread(name=sensor["device_id"], target=worker_w_queue,args=(ds18b20queue, sensor, results))
        ds18b20queues.append(ds18b20queue)
        ds18b20worker.start()
        ds18b20threads.append(ds18b20worker)
        print('Created worker '+ sensor["device_id"])
    service = threading.Thread(name='my_service', target=my_service,args=(ds18b20queues, results, ds18b20Sensors))
    service.start()
    time.sleep(60)
    measurement_stop.set()
    for ds18b20worker in ds18b20threads:
        ds18b20worker.join()