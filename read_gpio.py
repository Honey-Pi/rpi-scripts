#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import RPi.GPIO as GPIO # import GPIO
import time

def setup_gpio(GPIO_PIN):
    GPIO.setmode(GPIO.BCM) # set GPIO pin mode to BCM numbering
    GPIO.setwarnings(False)
    GPIO.setup(GPIO_PIN, GPIO.OUT)
    GPIO.setwarnings(True)
    GPIO.output(GPIO_PIN, GPIO.HIGH)

def reset_gpio(GPIO_PIN):
    GPIO.setmode(GPIO.BCM) # set GPIO pin mode to BCM numbering
    GPIO.output(GPIO_PIN, PIO.LOW)
    time.sleep(0.1) # wait 100ms
    GPIO.output(GPIO_PIN, PIO.HIGH)

def reset_ds18b20_3V(GPIO_PIN):
    GPIO.setmode(GPIO.BCM) # set GPIO pin mode to BCM numbering
    GPIO.output(GPIO_PIN, GPIO.LOW)
    time.sleep(3)
    GPIO.output(GPIO_PIN, GPIO.HIGH)
    time.sleep(5)
