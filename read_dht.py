#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

# This script requires:
#   sudo pip3 install adafruit-circuitpython-dht
#   sudo apt-get install libgpiod2

import logging
import adafruit_dht
import time
import board
import digitalio

logger = logging.getLogger('HoneyPi.read_dht')

def measure_dht(ts_sensor):
    fields = {}
    timer = 0
    errorMessage = ""

    try:
        SENSOR_PIN = digitalio.Pin(int(ts_sensor["pin"]))
        dht_type = int(ts_sensor["dht_type"])

        # setup sensor
        if dht_type == 2302:
            dht = adafruit_dht.DHT22(pin=SENSOR_PIN, use_pulseio=True)
        elif dht_type == 11:
            dht = adafruit_dht.DHT11(pin=SENSOR_PIN, use_pulseio=True)
        else:
            dht = adafruit_dht.DHT22(pin=SENSOR_PIN, use_pulseio=True)

        while timer <= 8:
            try:

                temperature = dht.temperature
                humidity = dht.humidity

                # Create returned dict if ts-field is defined
                if 'ts_field_temperature' in ts_sensor and temperature is not None:
                    if 'offset' in ts_sensor and ts_sensor["offset"] is not None:
                        temperature = temperature-float(ts_sensor["offset"])
                    fields[ts_sensor["ts_field_temperature"]] = round(temperature, 1)
                if 'ts_field_humidity' in ts_sensor and humidity is not None:
                    fields[ts_sensor["ts_field_humidity"]] = round(humidity, 1)

                break # break while if no Exception occured
            except RuntimeError as error:
                # Errors happen fairly often, DHT's are hard to read, just keep going
                errorMessage = error.args[0]
                print(errorMessage)
                time.sleep(1)
                timer = timer + 1

            if timer > 8: # end reached
                logger.error("Failed reading DHT on GPIO " + str(SENSOR_PIN) + ". " + errorMessage)

    except RuntimeError as error:
        errorMessage = error.args[0]
        logger.error("Failed initialising DHT: " + errorMessage)

    except Exception as ex:
        logger.exception("Reading DHT failed. DHT: " + str(dht_type) + ", GPIO: " + str(SENSOR_PIN))

    return fields

# For testing you can call this script directly (python3 read_dht.py)
if __name__ == '__main__':
    try:

        SENSOR_PIN = digitalio.Pin(4) # change GPIO pin
        dht = adafruit_dht.DHT22(pin=SENSOR_PIN, use_pulseio=True)

        timer = 0
        while timer <= 10:
            try:
                temperature = dht.temperature
                temperature_f = temperature * (9 / 5) + 32
                humidity = dht.humidity

                print("Temp: {:.1f} F / {:.1f} °C    Humidity: {}% ".format(temperature_f, temperature, humidity))

                break # break while if it worked
            except RuntimeError as error:
                # Errors happen fairly often, DHT's are hard to read, just keep going
                print(error.args[0])
                time.sleep(2.0)
                timer = timer + 2

            if timer > 10: # end reached
                print("Loop finished. Error.")

    except (KeyboardInterrupt, SystemExit):
       pass

    except RuntimeError as error:
        logger.error("RuntimeError in DHT measurement: " + error.args[0])

    except Exception as e:
       logger.exception("Unhandled Exception in DHT measurement")
