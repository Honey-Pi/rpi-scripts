from MAX6675 import MAX6675
import RPi.GPIO as GPIO

def measure_tc(tc_sensor):
    # MAX6675 sensor pins
    pin_cs = 26
    pin_sck = 18
    pin_do = 19
    try:
        pin_cs = int(tc_sensor["pin_cs"])
        pin_sck = int(tc_sensor["pin_sck"])
        pin_do = int(tc_sensor["pin_do"])
    except Exception as e:
        print("MAX6675 missing param: " + str(e))

    tc_temperature = 0

    # setup tc-Sensor
    try:
        tc = MAX6675(cs_pin = pin_cs, clock_pin = pin_sck, data_pin = pin_do, units = "c", board = GPIO.BCM)
    except Exception as e:
        print("Setup Max6675 failed " + str(e))

    try:
        tc_temperature=tc.get()
    except Exception as e:
        print("Reading HMAX6675 failed: " + str(e))

    if 'ts_field' in tc_sensor:
        return ({tc_sensor["ts_field"]: tc_temperature})
    else:
        return {}