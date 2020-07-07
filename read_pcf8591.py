#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import smbus
import time
from sensors.sensor_utilities import get_smbus
from utilities import error_log

# Main Source: http://www.diyblueprints.net/measuring-voltage-with-raspberry-pi/#Measure_Voltage_Python

def measure_voltage(ts_sensor):
    fields = {}

    # I2C-address of YL-40 PCF8591
    address = 0x48

    try:
        # Create I2C instance and open the bus
        PCF8591 = smbus.SMBus(get_smbus())

        # read pin from ts_sensor settings
        if 'pin' in ts_sensor and ts_sensor['pin'] is not None:
            pin = int(ts_sensor['pin'])
        else:
            pin = 2

        # AIN0 => Pin 0
        # AIN1 => Pin 1
        # AIN2 => Pin 2 (default)
        # AIN3 => Pin 3

        #factor = 0.09765625 # 25V/256 (=5V analog output signal)
        factor = 16.5/256 # 16.5V/256 | 16.5V max voltage for 0xff (=3.3V analog output signal)
        if 'I2CVoltage' in ts_sensor and ts_sensor['I2CVoltage'] is not None:
            # convert 8 bit number to voltage
            factor = float(ts_sensor['I2CVoltage']) / 256

        PCF8591.write_byte(address, 0x40+pin) # set channel to AIN0, AIN1, AIN2 or AIN3

        # measure once just for fun
        _v = PCF8591.read_byte(address)

        Voltage_8bit = PCF8591.read_byte(address) # = i2cget -y 1 0x48
        voltage = Voltage_8bit*factor # convert 8 bit number to voltage

        if 'ts_field' in ts_sensor and isinstance(voltage, (int, float)):
            fields[ts_sensor["ts_field"]] = round(voltage, 4)

        return fields

    except Exception as e:
        error_log(e, 'Error while reading PCF8591 (Voltage). Is the Sensor connected?')

    return None

def get_raw_voltage(ts_sensor):
    # I2C-address of YL-40 PCF8591
    address = 0x48

    try:
        # Create I2C instance and open the bus
        PCF8591 = smbus.SMBus(get_smbus())

        # read pin from ts_sensor settings
        if 'pin' in ts_sensor:
            pin = int(ts_sensor['pin'])
        else:
            pin = 2

        # AIN0 => Pin 0
        # AIN1 => Pin 1
        # AIN2 => Pin 2 (default)
        # AIN3 => Pin 3

        #factor = 0.09765625 # 25V/256 (=5V analog output signal)
        factor = 16.5/256 # 16.5V/256 | 16.5V max voltage for 0xff (=3.3V analog output signal)
        if 'I2CVoltage' in ts_sensor and ts_sensor['I2CVoltage'] is not None:
            # convert 8 bit number to voltage
            factor = float(ts_sensor['I2CVoltage']) / 256

        PCF8591.write_byte(address, 0x40+pin) # set channel to AIN0, AIN1, AIN2 or AIN3

        Voltage_8bit = PCF8591.read_byte(address) # = i2cget -y 1 0x48
        voltage = Voltage_8bit*factor # convert 8 bit number to voltage

        if isinstance(voltage, (int, float)):
            voltage=round(voltage, 4)

        return voltage

    except Exception as e:
        print("Exception in get_raw_voltage: " + str(e))

    return None
