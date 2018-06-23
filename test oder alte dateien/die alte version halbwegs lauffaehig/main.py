import os
import threading
import time
import RPi.GPIO as GPIO #allgemeines Einbinden der GPIO-Funktion

from read_settings import get_settings
from read_and_upload_all import close_script, start_read_and_upload_all, stop_read_and_upload_all

settings = get_settings() # read settings for number of GPIO pin
i = 0 # flag to know if measurement is active or not

def start_ap():
    global i
    i = 1 # measurement shall start next time
    print("AccessPoint wird aktiviert")
    os.system("sudo ifconfig wlan0 up") 
    time.sleep(0.4) 


def stop_ap():
    global i
    i = 0 # measurement shall stop next time
    print("AccessPoint wird deaktiviert")
    os.system("sudo ifconfig wlan0 down")
    time.sleep(0.4) 


def main():
    global i

    # setup gpio
    gpio = settings["button_pin"]
    GPIO.setwarnings(False) # Ignore warning for now
    GPIO.setmode(GPIO.BCM) # Zaehlweise der GPIO-PINS auf der Platine, analog zu allen Beispielen
    GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 17 to be an input pin and set initial value to be pulled low (off)

    # by default is AccessPoint down
    stop_ap()
    # start as seperate background thread
    # because Taster pressing was not recognised
    measurement_stop = threading.Event() # set flag to stop measurement
    measurement = threading.Thread(target=start_read_and_upload_all, args=(measurement_stop,))
    measurement.start() # start measurement

    while True:
        #print("Taster")
        input_state = GPIO.input(gpio)
        if input_state == GPIO.HIGH:
            print("Taster wurde gedrueckt")
            if i == 0:
                print("Taster: Stoppe Messungen")
                stop_read_and_upload_all()
                # stop the measurement by event's flag
                measurement_stop.set()
                start_ap() # finally start AP
            else:
                print("Taster: Starte Messungen")
                if not measurement.is_alive():
                    print("Alles Okay, Thread ist tot.")
                else:
                    print("Fehler: Thread ist noch aktiv.")
                measurement_stop.clear() # reset flag
                measurement_stop = threading.Event() # set flag to stop measurement
                measurement = threading.Thread(target=start_read_and_upload_all, args=(measurement_stop,))
                measurement.start() # start measurement
                stop_ap() # finally stop AP
        time.sleep(0.0001) # short sleep is good
    print("Dieser Text wird nie erreicht.")

if __name__ == '__main__':
    try:
        main()

    except (KeyboardInterrupt, SystemExit):
        close_script()