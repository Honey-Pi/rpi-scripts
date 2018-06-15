#!/usr/bin/env python3


from gpiozero import Button
from signal import pause
import os


def start_ap():
 	os.system("sudo ifconfig wlan0 up")
 	#
 	i=1
 	
def shutdown_ap():
 	os.system("sudo ifconfig wlan0 down")
 	i=0

button = Button(17)
	#Wert ist der GPIO Pin
i=0


while(true)
	if i=0
		button.when_pressed = start_ap
		pause()
	else
		button.when_pressed = shutdown_ap
		pause()