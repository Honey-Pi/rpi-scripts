#!/usr/bin/env python3
import smbus
import time
import re
import math
import logging

logger = logging.getLogger('HoneyPi.sensor_utilities')

# Source: https://github.com/adafruit/Adafruit_Python_GPIO/blob/master/Adafruit_GPIO/Platform.py

# Rev 1 Pi uses bus 0
# Rev 2 Pi, Pi 2 & Pi 3 uses bus 1
def get_smbus():
    try:
        """ Detect the version of the Raspberry Pi.  Returns the SMBus number.
            Rev 2 Pi, Pi 2 & Pi 3 uses bus 1
            Rev 1 Pi uses bus 0
        """
        # Check /proc/cpuinfo for the Hardware field value.
        # 2708 is pi 1
        # 2709 is pi 2
        # 2835 is pi 3 on 4.9.x kernel
        # Anything else is not a pi.
        with open('/proc/cpuinfo', 'r') as infile:
            cpuinfo = infile.read()
        # Match a line like 'Hardware   : BCM2709'
        match = re.search('^Hardware\s+:\s+(\w+)$', cpuinfo,
                          flags=re.MULTILINE | re.IGNORECASE)
        if not match:
            # Couldn't find the hardware, assume it isn't a pi.
            return 1
        if match.group(1) == 'BCM2708':
            # Pi 1
            return 0
        else:
            # Something else
            return 1
    except Exception as ex:
        logger.exception("Unhandled Exception in get_smbus")

def isSMBusConnected():
    try:
        bus = smbus.SMBus(get_smbus())
        return 1
    except Exception as ex:
        logger.exception("Unhandled Exception in isSMBusConnected")
        pass
    return 0

def computeAbsoluteHumidity(humidity, temperature):
    """https://carnotcycle.wordpress.com/2012/08/04/how-to-convert-relative-humidity-to-absolute-humidity/"""
    try:
        absTemperature = temperature + 273.15;
        absHumidity = 6.112;
        absHumidity *= math.exp((17.67 * temperature) / (243.5 + temperature));
        absHumidity *= humidity;
        absHumidity *= 2.1674;
        absHumidity /= absTemperature;
        return round(absHumidity, 2)

    except Exception as ex:
        logger.exception("Unhandled Exception in computeAbsoluteHumidity")
    return None
