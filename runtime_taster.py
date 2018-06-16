import time

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # GPIO pin where button is connected

while True:
    input_state = GPIO.input(17)
    if input_state == False:
        print('Pressed Button')
        time.sleep(0.2)
