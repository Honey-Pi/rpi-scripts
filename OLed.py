#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

from smbus import SMBus
import time
import logging
from logging.handlers import RotatingFileHandler
from Oled.lib_oled96 import ssd1306
from PIL import Image
from sensors.sensor_utilities import get_smbus

from read_settings import get_settings
from utilities import logfile, stop_tv, stop_led, toggle_blink_led, start_led, stop_hdd_led, start_hdd_led, reboot, client_to_ap_mode, ap_to_client_mode, blink_led, miliseconds, shutdown, delete_settings, getStateFromStorage, setStateToStorage, update_wittypi_schedule, connect_internet_modem, get_default_gateway_linux, get_interface_upstatus_linux, get_pi_model, get_rpiscripts_version, runpostupgradescript, check_undervoltage, get_ip_address, check_internet_connection, get_cpu_temp, get_ntp_status, sync_time_ntp, get_interfacelist
#from Oled.diag_onOLED import diag_onOLED

logger = logging.getLogger('HoneyPi.main')
import sys 


def oled_init():
    global i2cbus, oled, draw
    i2cbus = SMBus(get_smbus())  # 0 = Raspberry Pi 1, 1 = Raspberry Pi > 1
    oled = ssd1306(i2cbus)
    draw = oled.canvas
    oled.onoff(1)


def oled_off():
    ## OLED aus
    oled.cls()
    draw.text((0, 2), "", fill=1)
    draw.text((0, 12), "", fill=1)
    draw.text((0, 24), "", fill=1)
    draw.text((0, 34), "", fill=1)
    draw.text((0, 44), "", fill=1)
    draw.text((0, 54), "", fill=1)
    oled.display()
    oled.onoff(0) 

def oled_Logo():
    ## HoneyPi Logo an OLED senden
    try:
        oled.display()
        oled.cls()
        draw.rectangle((0, 0, 128, 64), outline=1, fill=1)
        draw.bitmap((0, 0), Image.open('Oled/HoneyPi_logo.png'), fill=0)
        oled.display()
        time.sleep(1)
    except Exception as ex:
        logger.error("Exception in function oled_Logo:" + str(ex))
        #pass

def oled_start_honeypi():
    try:
        oled_Logo()
        #oled.cls() # Nach dem Logo wird es drüber geschieben 
        # Versionsnummern auslesen und an OLED senden
        version_file = "/var/www/html/version.txt"
        fp = open(version_file)
        for i, line in enumerate(fp):
            if i >= 1 :
                print(line.split()[-1])
                draw.text((0, 13*i-10), str(line.split()[-1]), fill=1)
                oled.display()
        #print("Anzahl Datensaetze: ", i)
        fp.close()
    except Exception as ex:
        logger.error("Exception in function oled_start_honeypi:" + str(ex))

def oled_diag_data():
    try:
        lcdLine1= ""
        lcdLine2= ""
        lcdLine3= ""
        lcdLine4= ""
        lcdLine5= ""
        lcdLine6= ""
        undervoltage = check_undervoltage()
        #error_log("undervoltagecheck")
        print(undervoltage)
        
    
        if "No undervoltage alarm" in undervoltage:
            #error_log("Info: No undervoltage alarm")
            print("Unterspannung 0x0 " + undervoltage)
            lcdLine1= "Undervoltage:" 
            lcdLine2= "          No alarm"
    
        elif "0x50000" in undervoltage:
            #error_log("Warning: Undervoltage alarm had happened since system start ", undervoltage)
            print("Undervoltage " + undervoltage)
            lcdLine1= "Undervoltage check: Alarm"
            lcdLine2=  "    Alarm!"
    
        elif "0x50005" in undervoltage:
            #error_log("Warning: Undervoltage alarm is currently raised ", undervoltage)
            print("Undervoltage 0x50005 " + undervoltage)
            lcdLine1= "Undervoltage check: Alarm " 
            lcdLine2=  "    Alarm!"
        lcdLine5= "Clock sync:" + str(get_ntp_status())
        lcdLine6 = "CPU T: %.2f" % get_cpu_temp()
    
    
        ## IP auslesen
        oled.cls()
        draw.text((0, 2), lcdLine1, fill=1)
        draw.text((0, 12), lcdLine2, fill=1)
        draw.text((0, 24), lcdLine3, fill=1)
        draw.text((0, 34), lcdLine4, fill=1)
        draw.text((0, 44), lcdLine5, fill=1)
        draw.text((0, 54), lcdLine6, fill=1)
        oled.display()
    except Exception as e:
        logger.error("Exception in function oled_diag_data:" + str(e))
        #pass

def oled_interface_data():
    try:
    
        ifaces = get_interfacelist()
        for i in range (0,len(ifaces)):
            lcdLine1 = "Interface " + str(ifaces[i])
            lcdLine2 = "IP:" + str(get_ip_address(ifaces[i]))
            lcdLine3 = "" #Subnetmask
            lcdLine4 = "" #Broadscast
            lcdLine5 = "" #Gateway
            lcdLine6 = ""
            ## an OLED senden
            oled.cls()
            draw.text((0, 2), lcdLine1, fill=1)
            draw.text((0, 12), lcdLine2, fill=1)
            draw.text((0, 24), lcdLine3, fill=1)
            draw.text((0, 34), lcdLine4, fill=1)
            draw.text((0, 44), lcdLine5, fill=1)
            draw.text((0, 54), lcdLine6, fill=1)
            oled.display()
            time.sleep(2)
    except Exception as e:
        logger.error("Exception in function oled_interface_data:" + str(e))
        #pass


def main():
    try:
        oled_init()
        oled_start_honeypi()
        time.sleep(4)
        oled_diag_data()
        time.sleep(4)
        oled_interface_data()
        #time.sleep()
        oled_off()
    except Exception as ex:
        logger.critical("Unhandled Exception in main: " + repr(ex))

if __name__ == '__main__':
    try:
        main()

    except (KeyboardInterrupt, SystemExit):
        close_script()

    except Exception as ex:
        logger.error("Unhandled Exception in __main__ " + repr(ex))
