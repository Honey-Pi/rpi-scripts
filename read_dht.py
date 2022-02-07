#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

# This script requires:
#   sudo pip3 install adafruit-circuitpython-dht
#   sudo apt-get install libgpiod2

import logging
logger = logging.getLogger('HoneyPi.read_dht')
import time

try:
    import adafruit_dht

except ImportError as ex:
    logger.error("ImportError while importing Adafruit_DHT " + str(ex))
try:
    #import board
    import digitalio
except ImportError as ex:
    logger.error("ImportError while importing digitalio " + str(ex))

def measure_dht(ts_sensor):
    fields = {}
    timer = 1
    errorMessage = ""
    dht_type= 0
    pin = 0
    temperature = None
    humidity = None
    if 'dht_type' in ts_sensor and dht_type is not None:
        dht_type = int(ts_sensor["dht_type"])
    else:
        logger.warning("DHT type not defined, using DHT22")
        dht_type = 22
    if 'pin' in ts_sensor and pin is not None:
        pin = int(ts_sensor["pin"])
    else:
        logger.error("DHT PIN not defined!")
        return fields
    try:
        SENSOR_PIN = digitalio.Pin(pin)
    except NameError as ex:
            logger.error("NameError reading DHT " + str(ex))
            return fields
    except Exception as ex:
            errorMessage = "Setting up DHT PIN failed for GPIO: " + str(pin)
            logger.error(errorMessage)
            return fields
    while timer <= 8:
        try:

            # setup sensor
            logger.debug("Init DHT Sensor..")
            if dht_type == 2302:
                dht = adafruit_dht.DHT22(SENSOR_PIN, use_pulseio=True)
            elif dht_type == 11:
                dht = adafruit_dht.DHT11(SENSOR_PIN, use_pulseio=True)
            else:
                dht = adafruit_dht.DHT22(SENSOR_PIN, use_pulseio=True)
        except RuntimeError as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going
            errorMessage = "Failed reading DHT: " + error.args[0]
            logger.debug(errorMessage)
            time.sleep(1)
            timer = timer + 1
        except NameError as ex:
            logger.error("NameError reading DHT " + str(ex))
            return fields
        else:
            try:
                logger.debug('Measuring temperature (try: '+ str(timer)+')')
                temperature = dht.temperature
                logger.debug('Measuring humidity (try: '+ str(timer)+')')
                humidity = dht.humidity
                logger.debug('Finished measuring, closing sensor...')
                dht.exit()
                logger.debug('Finished closing sensor...')
                break # break while if no Exception occured
            except RuntimeError as error:
                # Errors happen fairly often, DHT's are hard to read, just keep going
                errorMessage = "Failed reading DHT: " + error.args[0]
                logger.debug(errorMessage)
                time.sleep(1)
                timer = timer + 1
                dht.exit()

    if timer > 8: # end reached
        logger.error("Failed reading DHT (tried "+str(timer)+"x times) on GPIO " + str(pin) + ". " + errorMessage)
        return fields
    # Create returned dict if ts-field is defined
    if 'ts_field_temperature' in ts_sensor and temperature is not None:
        if 'offset' in ts_sensor and ts_sensor["offset"] is not None:
            temperature = temperature-float(ts_sensor["offset"])
        fields[ts_sensor["ts_field_temperature"]] = round(temperature, 1)
    if 'ts_field_humidity' in ts_sensor and humidity is not None:
        fields[ts_sensor["ts_field_humidity"]] = round(humidity, 1)
    return fields

# For testing you can call this script directly (python3 read_dht.py)
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    try:


        fields = measure_dht ({"dht_type" : 2302, "pin" : 5, 'ts_field_temperature': "temperature", 'ts_field_humidity': "humidity"})
        if fields != {}:
            print("Temp: {:.1f} F / {:.1f} °C    Humidity: {}% ".format(fields['temperature']* (9 / 5) + 32, fields['temperature'], fields['humidity']))

    except (KeyboardInterrupt, SystemExit):
       pass

    except RuntimeError as error:
        logger.error("RuntimeError in DHT measurement: " + error.args[0])

    except Exception as e:
       logger.exception("Unhandled Exception in DHT measurement")
