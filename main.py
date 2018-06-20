import os
import threading
from time import sleep

import RPi.GPIO as GPIO  # allgemeines Einbinden der GPIO-Funktion

from read_and_upload_all import stop_script, start_read_and_upload_all, pause_read_and_upload_all, \
    release_read_and_upload_all
from read_settings import get_settings

settings = get_settings()

gpio = settings["button_pin"]
GPIO.setmode(GPIO.BCM)  # Zaehlweise der GPIO-PINS auf der Platine, analog zu allen Beispielen
GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Taster ist an GPIO-Pin 17 angeschlossen

lock = threading.Lock()  # we are using locks so we don't have conflicts while accessing the shared variables
event = threading.Event()  # we are using an event so we can close the thread as soon as KeyboardInterrupt is raised

i = 0
# by default is AccessPoint down
os.system("sudo ifconfig wlan0 down")


def start_ap():
    global i
    i = 1  # measurement shall start next time
    os.system("sudo ifconfig wlan0 up")
    sleep(0.4)


def stop_ap():
    global i
    i = 0  # measurement shall stop next time
    os.system("sudo ifconfig wlan0 down")
    sleep(0.4)


def main():
    # here we start the thread
    # we use a thread in order to gather/process the data separately from the printing process
    data_collector = threading.Thread(target=start_read_and_upload_all())
    data_collector.start()

    while not event.is_set():
        if GPIO.input(gpio) == False:
            lock.acquire()

            if i == 0:
                print("Stop measurements and start WiFi access mode")
                pause_read_and_upload_all()
                start_ap()
            else:
                print("Start measurements and stop WiFi access mode")
                release_read_and_upload_all()
                stop_ap()

            lock.release()

        # wait a second before the next check
        sleep(1)

    # wait until the thread is finished
    data_collector.join()


if __name__ == '__main__':
    try:
        main()

    except (KeyboardInterrupt, SystemExit):
        stop_script()
