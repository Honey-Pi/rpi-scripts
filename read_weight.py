# read weight value
# funktioniert derzeit nicht mit python3
import sys
import time

import RPi.GPIO as GPIO

from hx711 import HX711


def clean_and_exit():
    print("Cleaning...")
    GPIO.cleanup()
    print("Bye!")
    sys.exit()


hx = HX711(5, 6)
hx.set_reading_format("LSB", "MSB")

# HOW TO CALCULATE THE REFFERENCE UNIT
# To set the reference unit to 1. Put 1kg on your sensor or anything you have and know exactly how much it weights.
# In this case, 92 is 1 gram because, with 1 as a reference unit I got numbers near 0 without any weight
# and I got numbers around 184000 when I added 2kg. So, according to the rule of thirds:
# If 2000 grams is 184000 then 1000 grams is 184000 / 2000 = 92.
# hx.set_reference_unit(113)
hx.set_reference_unit(92)

hx.reset()
hx.tare()

while True:
    try:
        val = hx.get_weight(5)
        print(val)

        hx.power_down()
        hx.power_up()
        time.sleep(0.5)
    except (KeyboardInterrupt, SystemExit):
        clean_and_exit()
