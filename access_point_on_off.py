import os
from signal import pause

from gpiozero import Button

button = Button(17)  # value is the GPIO pin
i = 0
os.system("sudo ifconfig wlan0 down")


def start_ap():
    os.system("sudo ifconfig wlan0 up")
    i = 1


def shutdown_ap():
    os.system("sudo ifconfig wlan0 down")
    i = 0


while True:
    if i == 0:
        button.when_pressed = start_ap
        pause()
    else:
        button.when_pressed = shutdown_ap
        pause()
