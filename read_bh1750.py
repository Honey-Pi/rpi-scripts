# -*- coding: utf-8 -*-
#!/usr/bin/python3
#  Based on an article at https://www.raspberry-pi-geek.de/
#  Modified for HoneyPi

import smbus
import time
from utilities import error_log

device     = 0x23 # 0x5C 
power_down = 0x00
power_on   = 0x01
reset      = 0x07
bus = smbus.SMBus(1)

def convertToNumber(data):
    result=(data[1] + (256 * data[0])) / 1.2
    return (result)

def measure_bh1750(ts_sensor):
    try:

        fields = {}
        #	0x10	 0b00010000 //CHM: Continuously H-Resolution Mode
        #	0x11	 0b00010001 //CHM_2: Continuously H-Resolution Mode2
        #	0x13	 0b00010011 //CLM: Continuously L-Resolution Mode
        #***0x20	 0b00100000 //OTH: One Time H-Resolution Mode ***
        #	0x21	 0b00100001 //OTH_2: One Time H-Resolution Mode2
        #	0x23	 0b00100011 //OTL: One Time L-Resolution Mode
        #   For the beginning, the one time high resolution mode (OTH) was chosen.  
        data = bus.read_i2c_block_data(device, 0x20)  # Start initial measurement 
        time.sleep(0.200) # Measurement take ~120 ms / 200 ms was chosen as a safe value. 
        data = bus.read_i2c_block_data(device, 0x20) # Collecting the value
        # The address must be accessed a 2nd time so that the values are up-to-date. 
 
        # ThingSpeak fields
        # Create returned dict if ts_field is defined
        if 'ts_field' in ts_sensor and isinstance(convertToNumber(data), (int, float)):
            if 'offset' in ts_sensor and ts_sensor["offset"] is not None:
                data = convertToNumber(data)-ts_sensor["offset"]
            fields[ts_sensor["ts_field"]] = round(data, 1)
        return fields  
        
    except Exception as e:
        error_log(e, 'Error: Error while reading BH1750 Sensor. Is it connected?')
    return None
     
if __name__ == '__main__':
   try:
        lightLevel=convertToNumber(bus.read_i2c_block_data(device, 0x20))
        print (format(lightLevel,'.2f') + " lux")
        time.sleep(0.200)
        lightLevel=convertToNumber(bus.read_i2c_block_data(device, 0x20))
        print (format(lightLevel,'.2f') + " lux")

   except (KeyboardInterrupt, SystemExit):
       pass

   except Exception as e:
       error_log(e, "Unhandled Exception in BH1750 Measurement")
