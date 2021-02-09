#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import smbus
import time
from sensors.sensor_utilities import get_smbus
import logging

logger = logging.getLogger('HoneyPi.utilities')


# Main Source: http://www.diyblueprints.net/measuring-voltage-with-raspberry-pi/#Measure_Voltage_Python

def measure_pcf8591(ts_sensor):
    fields = {}
    try:
        if 'pin' in ts_sensor:
            pin = int(ts_sensor['pin'])
        else:
            pin = 2
            logger.debug("No pin defined, using default")

        #factor = 0.09765625 # 25V/256 (=5V analog output signal)
        factor = 16.5/256 # 16.5V/256 | 16.5V max voltage for 0xff (=3.3V analog output signal)
        if 'I2CVoltage' in ts_sensor and ts_sensor['I2CVoltage'] is not None:
            # convert 8 bit number to voltage
            factor = float(ts_sensor['I2CVoltage']) / 256

        data_8bit = measure(pin)
        data = data_8bit*factor # convert 8 bit number to voltage
        logger.debug("PCF8591 PIN: AIN" + str(pin) + " data with factor applied: " + str(data_8bit))

        if 'ts_field' in ts_sensor and isinstance(data, (int, float)):
            fields[ts_sensor["ts_field"]] = round(data, 4)

        return fields

    except Exception as ex:
        logger.exception("Unhaldled exception in measure_pcf8591: ")

    return None

def get_raw_voltage(ts_sensor):
    try:
        if 'pin' in ts_sensor:
            pin = int(ts_sensor['pin'])
        else:
            pin = 2
            logger.debug("get_raw_voltage - No pin defined, using default")

        #factor = 0.09765625 # 25V/256 (=5V analog output signal)
        factor = 16.5/256 # 16.5V/256 | 16.5V max voltage for 0xff (=3.3V analog output signal)
        if 'I2CVoltage' in ts_sensor and ts_sensor['I2CVoltage'] is not None:
            # convert 8 bit number to voltage
            factor = float(ts_sensor['I2CVoltage']) / 256

        Voltage_8bit = measure(pin)
        voltage = Voltage_8bit*factor # convert 8 bit number to voltage

        if isinstance(voltage, (int, float)):
            voltage=round(voltage, 4)
        logger.debug("PCF8591 PIN: AIN" + str(pin) + " voltage: " + str(voltage))

        return voltage

    except Exception as ex:
        logger.exception("Unhaldled exception in get_raw_voltage / PCF8591 (Voltage)")

    return None

def measure(pin):
    # I2C-addr of YL-40 PCF8591
    i2c_addr = 0x48

    try:
        # Create I2C instance and open the bus
        PCF8591 = smbus.SMBus(get_smbus())

        # read pin from ts_sensor settings
        # AIN0 => Pin 0
        # AIN1 => Pin 1
        # AIN2 => Pin 2 (default)
        # AIN3 => Pin 3

        PCF8591.write_byte(i2c_addr, 0x40+pin) # set channel to AIN0, AIN1, AIN2 or AIN3

        data_8bit = PCF8591.read_byte(i2c_addr) # = i2cget -y 1 0x48
        logger.debug("PCF8591 PIN: AIN" + str(pin) + " measureed raw data: " + str(data_8bit))
        if isinstance(data_8bit, (int, float)):
            data=data_8bit

        return data

    except Exception as ex:
        logger.exception("Unhaldled exception measure / PCF8591")