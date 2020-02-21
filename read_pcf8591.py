#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import smbus
import time
from sensors.sensor_utilities import get_smbus

# Main Source: http://www.diyblueprints.net/measuring-voltage-with-raspberry-pi/#Measure_Voltage_Python

def measure_voltage(ts_sensor):
    fields = {}

    # I2C-address of YL-40 PCF8591
    address = 0x48

    try:
        # Create I2C instance and open the bus
        PCF8591 = smbus.SMBus(get_smbus())

        # Configure PCF8591
        PCF8591.write_byte(address, 0x03) # set channel to AIN3 | = i2cset -y 1 0x48 0x03

        Voltage_8bit = PCF8591.read_byte(address) # = i2cget -y 1 0x48
        voltage = Voltage_8bit*0.064453125 # convert 8 bit number to voltage 16.5/256 | 16.5V max voltage for 0xff (=3.3V analog output signal)

        if 'ts_field' in ts_sensor and isinstance(voltage, (int, float)):
            fields[ts_sensor["ts_field"]] = round(voltage, 4)

        return fields

    except Exception as e:
        print('Error while reading PCF8591 (Voltage): ' + str(e))

    return None

def get_raw_voltage(pin):
    # I2C-address of YL-40 PCF8591
    address = 0x48

    try:
        # Create I2C instance and open the bus
        PCF8591 = smbus.SMBus(get_smbus())

        # Configure PCF8591
        PCF8591.write_byte(address, 0x40+pin)

        Voltage_8bit = PCF8591.read_byte(address) # = i2cget -y 1 0x48
        voltage = Voltage_8bit*0.064453125 # convert 8 bit number to voltage 16.5/256 | 16.5V max voltage for 0xff (=3.3V analog output signal)

        if isinstance(voltage, (int, float)):
            voltage=round(voltage, 4)

        return voltage

    except Exception as e:
        print("Exeption while getting temperature field: " + str(e))

    return None   
