#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import superglobal
import os
from datetime import datetime
from smbus2 import SMBus
import time
import logging
from logging.handlers import RotatingFileHandler
from Oled.lib_oled96 import ssd1306
from PIL import Image
from sensors.sensor_utilities import get_smbus

from read_settings import get_defaults, get_settings
from utilities import scriptsFolder, get_default_gateway_linux, get_interface_upstatus_linux, get_pi_model, get_rpiscripts_version, check_undervoltage, get_ip_address, check_internet_connection, get_cpu_temp, get_ntp_status, sync_time_ntp, get_interfacelist, offlinedata_prepare
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
        draw.bitmap((0, 0), Image.open(scriptsFolder + '/Oled/HoneyPi_logo.png'), fill=0)
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

        if "No undervoltage alarm" in undervoltage:
            lcdLine5= "Undervoltage:"
            lcdLine6= "No alarm"

        elif "0x50000" in undervoltage:
            lcdLine5= "Undervoltage check:"
            lcdLine6= "Alarm since start!"

        elif "0x50005" in undervoltage:
            lcdLine5= "Undervoltage check: Alarm "
            lcdLine6= "Alarm currently!"

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
            lcdLine2 = "is up: " + str(get_interface_upstatus_linux(ifaces[i]))
            lcdLine3 = "IP:" + str(get_ip_address(ifaces[i]))
            lcdLine4 = "" #Subnetmask
            lcdLine5 = "" #Broadscast
            lcdLine6 = "" #Gateway
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

def oled_maintenance_data(settings):
    try:
        if superglobal.isMaintenanceActive:

            honeypi = settings['internet']['honeypi']
            if honeypi['password'] == get_defaults()['internet']['honeypi']['password']:
                    password = honeypi["password"]
            else:
                if settings['display']['show_nondefault_password']:
                    password = honeypi["password"]
                else:
                    password = '**********'
            lcdLine1 = "Connect to"
            lcdLine2 = "SSID:"
            lcdLine3 = honeypi["ssid"]
            lcdLine4 = "Password:"
            lcdLine5 = password
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

def oled_view_channels(offlinedata):
    try:
        for channeldata in offlinedata:
            oled_view_channel(
                channeldata['channel_id'],
                channeldata['Date'],
                channeldata['Time'],
                channeldata['field1'],
                channeldata['field2'],
                channeldata['field3'],
                channeldata['field4'],
                channeldata['field5'],
                channeldata['field6'],
                channeldata['field7'],
                channeldata['field8'])
    except Exception as ex:
        logger.exception("oled_view_channels")

def oled_view_channel(ChannelId, lcdTime, lcdDate, field1="", field2="", field3="", field4="", field5="", field6="", field7="", field8=""):
    try:
        #oled.onoff(1)
        #oled.cls()
        #draw.rectangle((0, 0, 128, 64), outline=1, fill=1)
        #draw.bitmap((0, 0), Image.open('HoneyPi_logo.png'), fill=0)
        #oled.display()
        #time.sleep(2)

        lcdLine1="Channel: " + str(ChannelId)
        lcdLine2=('Date:'+ lcdDate).ljust(10)  + " " + ('Time:' + lcdTime).ljust(10)
        lcdLine3=field1.rjust(10) + "|" + field2.rjust(10)
        lcdLine4=field3.rjust(10) + "|" + field4.rjust(10)
        lcdLine5=field5.rjust(10) + "|" + field6.rjust(10)
        lcdLine6=field7.rjust(10) + "|" + field8.rjust(10)
        oled.cls()
        #mylcd.lcd_clear()
        draw.text((0, 2), lcdLine1, fill=1)
        draw.text((0, 12), lcdLine2, fill=1)
        draw.text((0, 24), lcdLine3, fill=1)
        draw.text((0, 34), lcdLine4, fill=1)
        draw.text((0, 44), lcdLine5, fill=1)
        draw.text((0, 54), lcdLine6, fill=1)
        oled.display()
        time.sleep(2)
        #oled.onoff(0)   # kill the oled.  RAM contents still there.
        logger.debug("Channel data for " + str(ChannelId) + " successfully sent to the LCD")
        return ChannelId

    except IOError as ex:
        if str(ex) == "[Errno 121] Remote I/O error":
            logger.error("Initializing oled ssd1306 failed, most likely display not connected.")
        else:
            logger.exception("Initializing oled ssd1306 failed")
    except Exception as ex:
        logger.exception("oled_view_channel")
    return False



def main():
    try:
        logging.basicConfig(level=logging.DEBUG)
        settings = get_settings()
        ts_channels = settings["ts_channels"] # ThingSpeak data (ts_channel_id, ts_write_key)

        oled_init()
        oled_start_honeypi()
        time.sleep(4)
        oled_diag_data()
        time.sleep(4)
        oled_interface_data()
        oled_measurement_data()
        time.sleep(4)
        oled_view_channels(offlinedata_prepare(ts_channels))
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
