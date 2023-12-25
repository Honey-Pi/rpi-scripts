#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.


# This file is deprecated and not used because the Adafruit_DHT does not work with Raspberry Pi OS. (see: https://stackoverflow.com/a/66007330/6696623)

# Because of comapbility issues (as mentioned here: https://github.com/adafruit/Adafruit_CircuitPython_DHT/issues/73 ) this file is still used if you are running HoneyPi on a Raspberry Zero.

import os
import logging
logger = logging.getLogger('HoneyPi.read_dht_zero')

try:
    import Adafruit_DHT
except ImportError as ex:
    logger.error("read_dht_zero.py ImportError while importing Adafruit_DHT " + str(ex))

os.environ['PYTHON_EGG_CACHE'] = '/usr/local/pylons/python-eggs'

def measure_dht_zero(ts_sensor):
    fields = {}
    timer = 1
    max_timer = 8
    errorMessage = ""
    dht_type = 22
    pin = 0
    temperature = None
    humidity = None

    if 'dht_type' in ts_sensor and ts_sensor["dht_type"] is not None:
        dht_type = int(ts_sensor["dht_type"])
    else:
        logger.warning("DHT type not defined, using DHT22 by default.")
        dht_type = 22

    if 'pin' in ts_sensor and ts_sensor["pin"] is not None:
        pin = int(ts_sensor["pin"])
    else:
        logger.error("DHT PIN not defined!")
        return fields

    while timer <= max_timer:
        try:
            # setup sensor
            if dht_type == 2302:
                sensorDHT = Adafruit_DHT.AM2302
            elif dht_type == 11:
                sensorDHT = Adafruit_DHT.DHT11
            else:
                sensorDHT = Adafruit_DHT.DHT22

            logger.debug('Measuring DHT temperature...')
            humidity, temperature = Adafruit_DHT.read_retry(sensorDHT, pin)
            logger.debug('Finished measuring, closing sensor...')
            break # break while if no Exception occured
        except RuntimeError as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going
            errorMessage = "Failed reading DHT ("+str(timer)+"/"+str(max_timer)+"): " + error.args[0]
            logger.debug(errorMessage)
            time.sleep(1)
            timer = timer + 1
            pass # try again
        except NameError as ex:
            logger.error("NameError reading DHT " + str(ex))
            return fields
        except ImportError as ex:
            logger.error("ImportError while measuring Adafruit_DHT " + str(ex))
            return fields

    if timer > max_timer: # end reached
        logger.error("Failed reading DHT ("+str(timer-1)+" times) on GPIO " + str(pin))
        return fields

    # Create returned dict if ts-field is defined
    if 'ts_field_temperature' in ts_sensor and temperature is not None:
        if 'offset' in ts_sensor and ts_sensor["offset"] is not None:
            temperature = temperature-float(ts_sensor["offset"])
        fields[ts_sensor["ts_field_temperature"]] = round(temperature, 1)
    if 'ts_field_humidity' in ts_sensor and humidity is not None:
        fields[ts_sensor["ts_field_humidity"]] = round(humidity, 1)

    return fields

# For testing you can call this script directly (python3 read_dht_zero.py)
if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)

    try:
        fields = measure_dht_zero ({"dht_type" : 2302, "pin" : 5, 'ts_field_temperature': "temperature", 'ts_field_humidity': "humidity"})
        if fields != {}:
            print("Temp: {:.1f} F / {:.1f} °C    Humidity: {}% ".format(fields['temperature']* (9 / 5) + 32, fields['temperature'], fields['humidity']))

    except (KeyboardInterrupt, SystemExit):
       pass

    except RuntimeError as error:
        logger.error("RuntimeError in DHT measurement: " + error.args[0])

    except Exception as e:
       logger.exception("Unhandled Exception in DHT measurement")
