import RPi.GPIO as GPIO #allgemeines Einbinden der GPIO-Funktion 
import time
 
GPIO.setmode(GPIO.BCM) #Zählweise der GPIO-PINS auf der Platine, analog zu allen Beispielen
 
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP) #Taster ist an GPIO-Pin 17 angeschlossen 
 
i=0



while True:
    input_state = GPIO.input(17)
    if input_state == False & i==0:
        os.system("sudo ifconfig wlan0 up")
        i=1
 	
        time.sleep(0.2) 

    elif input_state == False & i==1:
        os.system("sudo ifconfig wlan0 down")
        i=0
 	
        time.sleep(0.2)