import os
import threading
import time
import RPi.GPIO as GPIO #allgemeines Einbinden der GPIO-Funktion

from read_settings import get_settings
from read_and_upload_all import close_script, start_read_and_upload_all, stop_read_and_upload_all

settings = get_settings()

gpio = settings["button_pin"]
GPIO.setmode(GPIO.BCM) # Zaehlweise der GPIO-PINS auf der Platine, analog zu allen Beispielen
GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Taster ist an GPIO-Pin 17 angeschlossen 

i = 0
# by default is AccessPoint down
os.system("sudo ifconfig wlan0 down")
# start as seperate background thread
# because Taster pressing was not recognised
t = threading.Thread(target=start_read_and_upload_all)
t.start()

def start_ap():
    global i
    i = 1 # measurement shall start next time
    os.system("sudo ifconfig wlan0 up") 
    time.sleep(0.4) 


def stop_ap():
    global i
    i = 0 # measurement shall stop next time
    os.system("sudo ifconfig wlan0 down")
    time.sleep(0.4) 


def main():
    global i
    while True:
        input_state = GPIO.input(gpio)
        if input_state == False:
            if i == 0:
                print "Pausiere Messungen im AccessPoint-Modus"
                stop_read_and_upload_all()
                start_ap()
            else:
                print "Starte Messungen"
                # start as seperate thread
                # because Taster pressing was not recognised
                t = threading.Thread(target=start_read_and_upload_all)
                t.start()
                stop_ap()
        time.sleep(0.0001) 

if __name__ == '__main__':
    try:
        main()

    except (KeyboardInterrupt, SystemExit):
        close_script()
