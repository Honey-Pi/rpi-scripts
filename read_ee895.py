#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import smbus
import time
from sensors.sensor_utilities import get_smbus
import logging
logger = logging.getLogger('HoneyPi.read_ee895')

# Main Source: http://www.diyblueprints.net/measuring-voltage-with-raspberry-pi/#Measure_Voltage_Python

#Debugging with i2cget all values return in big-endian)
# pi@testRPi3:~$ i2cget –y 1 0x5e 0 w --> co2 ppm
# pi@testRPi3:~$ i2cget –y 1 0x5e 2 w --> temperature °C.
# pi@testRPi3:~$ i2cget –y 1 0x5e 6 w --> pressure mbar

# I2C-address of EE-895 is

#pressure
# i2cget –y 1 0x5e 6 w

def _switchBit(high):
    return ((high>>8)&0xff) + ((high&0xff)<<8)

def _measure_all():
    address = 0x5e    #I2C-address of EE-895

    try:
        # Create I2C instance and open the bus
        EE895 = smbus.SMBus(get_smbus())

        _c = EE895.read_word_data(address,0x0) # co2
        _t = EE895.read_word_data(address,0x2) # temp
        _p = EE895.read_word_data(address,0x6) # pressure

        co = _switchBit(_c)
        temp= _switchBit(_t) / 100
        pressure= _switchBit(_p) / 10

        return co,temp,pressure

    except Exception as e:
        logger.exception("Error while reading EE895 Sensor. Is it connected")

    return None, None, None


def measure_raw():
    co,temp,pressure=_measure_all()

    print("co: %d ppm" % co)
    print("temp: %+.2f °C" % temp)
    print("temp: %d mbar" % pressure)

def measure_ee895(ts_sensor):

    fields = {}
    try:
        #read all values from sensor
        co2,temp,pressure=_measure_all()

        # ThingSpeak fields
        # Create returned dict if ts-field is defined
        if 'ts_field' in ts_sensor and isinstance(co2, (int, float)):
            fields[ts_sensor["ts_field"]] = round(co2, 2)
        if 'ts_field_temperature' in ts_sensor and isinstance(temp, (int, float)):
            fields[ts_sensor["ts_field_temperature"]] = round(temp, 1)
        if 'ts_field_air_pressure' in ts_sensor and isinstance(pressure, (int, float)):
            fields[ts_sensor["ts_field_air_pressure"]] = round(pressure, 1)
    except OSError:
        logger.warning("No EE895 Sensor connected.")
    except Exception as ex:
        logger.exception("Error while measuring EE895 Sensor.")

    return fields


if __name__ == '__main__':
    try:

        # just for testing the values
        print(measure_raw())

    except (KeyboardInterrupt, SystemExit):
        pass

    except Exception as e:
        logger.exception("Unhandled Exception in EE895 Measurement")
