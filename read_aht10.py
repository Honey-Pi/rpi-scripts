# -*- coding: utf-8 -*-
#!/usr/bin/python3
#  Based on: https://github.com/gejanssen/aht10-python

import smbus
import time
import logging
from sensors.sensor_utilities import get_smbus

logger = logging.getLogger('HoneyPi.read_aht10')

DEVICE = 0x38 # Default device I2C address

def read_aht10(addr=DEVICE):
    bus = smbus.SMBus(get_smbus())
    # init & read
    config = [0x08, 0x00]
    MeasureCmd = [0x33, 0x00]
    bus.write_i2c_block_data(DEVICE, 0xE1, config)
    time.sleep(0.5)

    byt = bus.read_byte(addr)
    bus.write_i2c_block_data(addr, 0xAC, MeasureCmd)
    time.sleep(0.5)
    data = bus.read_i2c_block_data(addr,0x00)

    # Data
    temp = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]
    ctemp = ((temp*200) / 1048576) - 50
    tmp = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4
    ctmp = int(tmp * 100 / 1048576)
    return (ctemp, ctmp)

def measure_aht10(ts_sensor):
    try:
        fields = {}
        temperature,humidity = read_aht10(DEVICE)
        # ThingSpeak fields
        # Create returned dict if ts_field is defined
        if 'ts_field_temperature' in ts_sensor and isinstance(temperature, (int, float)):
            if 'offset' in ts_sensor and ts_sensor["offset"] is not None:
                temperature = temperature-ts_sensor["offset"]
            fields[ts_sensor["ts_field_temperature"]] = round(temperature, 2)
        if 'ts_field_humidity' in ts_sensor and isinstance(humidity, (int, float)):
            fields[ts_sensor["ts_field_humidity"]] = round(humidity, 2)
        return fields

    except Exception as e:
        logger.error('Error while reading AHT10 Sensor. Is it connected?')
    return None


if __name__ == '__main__':
   try:

     temperature,humidity = read_aht10(DEVICE)

     print("Temperature:", temperature, "C")
     print("Humidity:", humidity, "%")

   except (KeyboardInterrupt, SystemExit):
       pass

   except Exception as e:
       logger.exception("Unhandled Exception in AHT10 Measurement")
