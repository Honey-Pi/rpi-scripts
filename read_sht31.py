# Distributed with a free-will license.
# Use it any way you want, profit or free, provided it fits in the licenses of its associated works.
# SHT31
# This code is designed to work with the SHT31_I2CS I2C Mini Module available from ControlEverything.com.
# https://www.controleverything.com/content/Humidity?sku=SHT31_I2CS#tabs-0-product_tabset-2

import smbus
import time
import logging
from sensors.sensor_utilities import get_smbus

logger = logging.getLogger('HoneyPi.read_sht31')

# SHT31 address, 0x44(68)
DEVICE=0x44

def read_sht31(addr=DEVICE):
    # Get I2C bus
    bus = smbus.SMBus(get_smbus())

    # Send measurement command, 0x2C(44)
    #		0x06(06)	High repeatability measurement
    bus.write_i2c_block_data(addr, 0x2C, [0x06])

    time.sleep(0.5)

    # Read data back from 0x00(00), 6 bytes
    # Temp MSB, Temp LSB, Temp CRC, Humididty MSB, Humidity LSB, Humidity CRC
    data = bus.read_i2c_block_data(addr, 0x00, 6)

    # Convert the data
    temp = data[0] * 256 + data[1]
    cTemp = -45 + (175 * temp / 65535.0)
    fTemp = -49 + (315 * temp / 65535.0)
    humidity = 100 * (data[3] * 256 + data[4]) / 65535.0

    return (cTemp, humidity)

def measure_sht31(ts_sensor):
    try:
        fields = {}
        if 'i2c_addr' in ts_sensor and ts_sensor["i2c_addr"] is not None:
            DEVICE = int(ts_sensor["i2c_addr"], 16) # convert string to hexadecimal integer
        temperature,humidity = read_sht31(DEVICE)
        # ThingSpeak fields
        # Create returned dict if ts_field is defined
        if 'ts_field_temperature' in ts_sensor and isinstance(temperature, (int, float)):
            if 'offset' in ts_sensor and ts_sensor["offset"] is not None:
                temperature = temperature-ts_sensor["offset"]
            fields[ts_sensor["ts_field_temperature"]] = round(temperature, 1)
        if 'ts_field_humidity' in ts_sensor and isinstance(humidity, (int, float)):
            fields[ts_sensor["ts_field_humidity"]] = round(humidity, 1)
        return fields

    except Exception as e:
        logger.error('Error while reading SHT3x Sensor. Is it connected?')
    return None

if __name__ == '__main__':
   try:

     cTemp,humidity = read_sht31(DEVICE)

     print("Temperature:", cTemp, "C")
     print("Humidity:", humidity, "%RH")

   except (KeyboardInterrupt, SystemExit):
       pass

   except Exception as e:
       logger.exception("Unhandled Exception in SHT31 Measurement")
