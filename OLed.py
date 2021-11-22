#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import superglobal
from datetime import datetime
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

logger = logging.getLogger('HoneyPi.OLed')
import sys 

superglobal = superglobal.SuperGlobal()

def oled_init():
    global i2cbus, oled, draw
    try:
        i2cbus = SMBus(get_smbus())  # 0 = Raspberry Pi 1, 1 = Raspberry Pi > 1
        oled = ssd1306(i2cbus)
        draw = oled.canvas
        oled.onoff(1)
    except IOError as ex:
        if str(ex) == "[Errno 121] Remote I/O error":
            logger.error("Initializing oled ssd1306 failed, most likely display not connected.")
        else:
            logger.exception("Initializing oled ssd1306 failed")
    except Exception as ex:
        logger.error("Exception in function oled_init:" + str(ex))
        #pass
    


def oled_off():
    try:
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
    except IOError as ex:
        if str(ex) == "[Errno 121] Remote I/O error":
            logger.error("communication with oled ssd1306 failed, most likely display not connected.")
        else:
            logger.exception("communication with oled ssd1306 failed")
    except Exception as ex:
        logger.error("Exception in function oled_off:" + str(ex))
        #pass

def oled_Logo():
    ## HoneyPi Logo an OLED senden
    try:
        oled.display()
        oled.cls()
        draw.rectangle((0, 0, 128, 64), outline=1, fill=1)
        draw.bitmap((0, 0), Image.open('Oled/HoneyPi_logo.png'), fill=0)
        oled.display()
        time.sleep(1)
    except IOError as ex:
        if str(ex) == "[Errno 121] Remote I/O error":
            logger.error("Initializing oled ssd1306 failed, most likely display not connected.")
        else:
            logger.exception("Initializing oled ssd1306 failed")
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
                #print(line.split()[-1])
                draw.text((0, 13*i-10), str(line.split()[-1]), fill=1)
                oled.display()
        #print("Anzahl Datensaetze: ", i)
        fp.close()
    except IOError as ex:
        if str(ex) == "[Errno 121] Remote I/O error":
            logger.error("Initializing oled ssd1306 failed, most likely display not connected.")
        else:
            logger.exception("Initializing oled ssd1306 failed")
    except Exception as ex:
        logger.error("Exception in function oled_start_honeypi:" + str(ex))

def oled_measurement_data():
    try:
        #print("oled_measurement_data")
        if superglobal.lastmeasurement is not None:
            lastmeasurement = superglobal.lastmeasurement.strftime('%Y-%m-%d %H:%M')
        else:
            lastmeasurement = "Never"
        #print("Last Measurement: " + lastmeasurement)
        if superglobal.nextmeasurement is not None:
            nextmeasurement = superglobal.nextmeasurement.strftime('%Y-%m-%d %H:%M')
            #nextmeasurement = str(datetime.fromtimestamp(int(superglobal.nextmeasurement)).strftime('%Y-%m-%d %H:%M'))
        else:
            nextmeasurement = "see interval"
        #print("Next Measurement: " + nextmeasurement)
        if superglobal.isMaintenanceActive:
            nextmeasurement = "MaintenanceActive"
        lcdLine1= "Measurement info"
        lcdLine2= "Last:"
        lcdLine3= lastmeasurement
        lcdLine4= "Next:"
        lcdLine5= nextmeasurement
        lcdLine6= ""

        oled.cls()
        draw.text((0, 2), lcdLine1, fill=1)
        draw.text((0, 12), lcdLine2, fill=1)
        draw.text((0, 24), lcdLine3, fill=1)
        draw.text((0, 34), lcdLine4, fill=1)
        draw.text((0, 44), lcdLine5, fill=1)
        draw.text((0, 54), lcdLine6, fill=1)
        oled.display()
    except IOError as ex:
        if str(ex) == "[Errno 121] Remote I/O error":
            logger.error("Initializing oled ssd1306 failed, most likely display not connected.")
        else:
            logger.exception("Initializing oled ssd1306 failed")
    except Exception as e:
        logger.error("Exception in function oled_diag_data:" + str(e))
        #pass

def oled_diag_data():
    try:
        lcdLine1= ""
        lcdLine2= ""
        lcdLine3= ""
        lcdLine4= ""
        lcdLine5= ""
        lcdLine6= ""
        
        lcdLine1= "Actual Date & Time"
        lcdLine2 = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        lcdLine3= "Clock sync:" + str(get_ntp_status())
        lcdLine4 = "CPU T: %.2f" % get_cpu_temp()
        
        undervoltage = check_undervoltage()
        #error_log("undervoltagecheck")
        #print(undervoltage)
        
        
        if "No undervoltage alarm" in undervoltage:
            #error_log("Info: No undervoltage alarm")
            #print("Unterspannung 0x0 " + undervoltage)
            lcdLine5= "Undervoltage:" 
            lcdLine6= "No alarm"
        
        elif "0x50000" in undervoltage:
            #error_log("Warning: Undervoltage alarm had happened since system start ", undervoltage)
            #print("Undervoltage " + undervoltage)
            lcdLine5= "Undervoltage check: Alarm"
            lcdLine6=  "Alarm!"
        
        elif "0x50005" in undervoltage:
            #error_log("Warning: Undervoltage alarm is currently raised ", undervoltage)
            #print("Undervoltage 0x50005 " + undervoltage)
            lcdLine5= "Undervoltage check: Alarm " 
            lcdLine6=  "Alarm!"
        
        oled.cls()
        draw.text((0, 2), lcdLine1, fill=1)
        draw.text((0, 12), lcdLine2, fill=1)
        draw.text((0, 24), lcdLine3, fill=1)
        draw.text((0, 34), lcdLine4, fill=1)
        draw.text((0, 44), lcdLine5, fill=1)
        draw.text((0, 54), lcdLine6, fill=1)
        oled.display()
    except IOError as ex:
        if str(ex) == "[Errno 121] Remote I/O error":
            logger.error("Initializing oled ssd1306 failed, most likely display not connected.")
        else:
            logger.exception("Initializing oled ssd1306 failed")
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
    except IOError as ex:
        if str(ex) == "[Errno 121] Remote I/O error":
            logger.error("Initializing oled ssd1306 failed, most likely display not connected.")
        else:
            logger.exception("Initializing oled ssd1306 failed")
    except Exception as e:
        logger.error("Exception in function oled_interface_data:" + str(e))
        #pass

def oled_maintenance_data():
    try:
        if superglobal.isMaintenanceActive:
            settings = get_settings()
            honeypi = settings['internet']['honeypi']
            
            lcdLine1 = "Connect to"
            lcdLine2 = "SSID:"
            lcdLine3 = honeypi["ssid"]
            lcdLine4 = "Password:"
            lcdLine5 = honeypi["password"]
            lcdLine6 = "IP:" + str(get_ip_address("uap0"))
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
    except IOError as ex:
        if str(ex) == "[Errno 121] Remote I/O error":
            logger.error("Initializing oled ssd1306 failed, most likely display not connected.")
        else:
            logger.exception("Initializing oled ssd1306 failed")
    except Exception as e:
        logger.error("Exception in function oled_interface_data:" + str(e))
        #pass

def oled_maintenance_mode(status):
    try:
        oled_maintenance_data()
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
    except IOError as ex:
        if str(ex) == "[Errno 121] Remote I/O error":
            logger.error("Initializing oled ssd1306 failed, most likely display not connected.")
        else:
            logger.exception("Initializing oled ssd1306 failed")
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
        oled_measurement_data(lastmeasurement="", nextmeasurement="")
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
