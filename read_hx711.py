#!/usr/bin/env python

from HX711 import HX711

def measure_weight(weight_sensor):
    # weight sensor pins
    pin_dt = weight_sensor["pin_dt"]
    pin_sck = weight_sensor["pin_sck"]
    reference_unit = weight_sensor["reference_unit"]

    # setup weight sensor
    hx = HX711(pin_dt, pin_sck)
   
    # I've found out that, for some reason, the order of the bytes is not always the same between versions of python, numpy and the hx711 itself.
    # Still need to figure out why does it change.
    # If you're experiencing super random values, change these values to MSB or LSB until to get more stable values.
    # There is some code below to debug and log the order of the bits and the bytes.
    # The first parameter is the order in which the bytes are used to build the "long" value.
    # The second paramter is the order of the bits inside each byte.
    # According to the HX711 Datasheet, the second parameter is MSB so you shouldn't need to modify it.
    hx.set_reading_format("LSB", "MSB")

    # HOW TO CALCULATE THE REFFERENCE UNIT
    # To set the reference unit to 1. Put 1kg on your sensor or anything you have and know exactly how much it weights.
    # In this case, 92 is 1 gram because, with 1 as a reference unit I got numbers near 0 without any weight
    # and I got numbers around 184000 when I added 2kg. So, according to the rule of thirds:
    # If 2000 grams is 184000 then 1000 grams is 184000 / 2000 = 92.
    # hx.set_reference_unit(113)
    hx.set_reference_unit(reference_unit)

    hx.reset()
    hx.tare()

    weight = hx.get_weight(5)
    # transform weight value
    #weight = max(0, int(weight))
    hx.power_down()
    hx.power_up()

    return ({weight_sensor["ts_field"]: float("%.0f" % (weight))})
