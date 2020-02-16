#!/usr/bin/env python3
import smbus
import time
import re

# Source: https://github.com/adafruit/Adafruit_Python_GPIO/blob/master/Adafruit_GPIO/Platform.py

# Rev 1 Pi uses bus 0
# Rev 2 Pi, Pi 2 & Pi 3 uses bus 1
def get_smbus():
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
