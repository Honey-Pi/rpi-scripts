# Distributed with a free-will license.
# Use it any way you want, profit or free, provided it fits in the licenses of its associated works.
# This code is designed to work with the SHT25_I2CS I2C Mini Module available from ControlEverything.com.
# https://www.controleverything.com/content/Humidity?sku=SHT25_I2CS#tabs-0-product_tabset-2

import smbus
import time
import logging
from sensors.sensor_utilities import get_smbus

logger = logging.getLogger('HoneyPi.read_sht25')

# SHT25 address, 0x40(68)
DEVICE=0x40

def read_sht25(addr=DEVICE):
    # Get I2C bus
    bus = smbus.SMBus(1)

    # Send temperature measurement command
    #		0xF3(243)	NO HOLD master
    bus.write_byte(addr, 0xF3)

    time.sleep(0.5)

    # Read data back, 2 bytes
    # Temp MSB, Temp LSB
    data0 = bus.read_byte(addr)
    data1 = bus.read_byte(addr)

    # Convert the data
    temp = data0 * 256 + data1
    cTemp= -46.85 + ((temp * 175.72) / 65536.0)
    fTemp = cTemp * 1.8 + 32

    # Send humidity measurement command
    #		0xF5(245)	NO HOLD master
    bus.write_byte(addr, 0xF5)

    time.sleep(0.5)

    # Read data back, 2 bytes
    # Humidity MSB, Humidity LSB
    data0 = bus.read_byte(addr)
    data1 = bus.read_byte(addr)

    # Convert the data
    humidity = data0 * 256 + data1
    humidity = -6 + ((humidity * 125.0) / 65536.0)

    return (cTemp, humidity)


def measure_sht25(ts_sensor):
    try:
        fields = {}
        if 'i2c_addr' in ts_sensor and ts_sensor["i2c_addr"] is not None:
            DEVICE = int(ts_sensor["i2c_addr"], 16) # convert string to hexadecimal integer
        temperature,humidity = read_sht25(DEVICE)
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
        logger.error('Error while reading SHT25 Sensor. Is it connected?')
    return None

if __name__ == '__main__':
   try:

     cTemp,humidity = read_sht25(DEVICE)

     # Output data to screen
     print ("Relative Humidity is : %.2f %%" %humidity)
     print ("Temperature in Celsius is : %.2f C" %cTemp)

   except (KeyboardInterrupt, SystemExit):
       pass

   except Exception as e:
       logger.exception("Unhandled Exception in SHT25 Measurement")
