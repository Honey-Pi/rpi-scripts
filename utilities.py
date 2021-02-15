#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import io
import os
import pwd
import grp
import sys
import time
from datetime import datetime
import urllib.request
import json
import logging
import RPi.GPIO as GPIO
from pathlib import Path
import socket, struct, fcntl

import subprocess
import re
logger = logging.getLogger('HoneyPi.utilities')

homeFolder = '/home/pi'
honeypiFolder = homeFolder + '/HoneyPi'
scriptsFolder = honeypiFolder + '/rpi-scripts'
backendFolder = '/var/www/html/backend'
settingsFile = backendFolder + '/settings.json'
wittypi_scheduleFile = backendFolder + "/schedule.wpi"
logfile = scriptsFolder + '/error.log'

def get_ip_address(ifname):
    try:
        ipv4 = os.popen('ip addr show ' + ifname + ' | grep "\<inet\>" | awk \'{ print $2 }\' | awk -F "/" \'{ print $1 }\'').read().strip()
        return(ipv4)
    except Exception as ex:
        logger.exception("Exception in get_ip_address")
        pass
        return None

def get_default_gateway_linux():
    """Read the default gateway directly from /proc."""
    try:
        with open("/proc/net/route") as fh:
            for line in fh:
                fields = line.strip().split()
                if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                    # If not default route or not RTF_GATEWAY, skip it
                    continue

                return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))
    except Exception as ex:
        logger.exception("Exception in get_default_gateway_linux")
        pass
        return None

def get_default_gateway_interface_linux():
    """Read the default gateway directly from /proc."""
    try:
        with open("/proc/net/route") as fh:
            for line in fh:
                fields = line.strip().split()
                if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                    # If not default route or not RTF_GATEWAY, skip it
                    continue

                return str(fields[0])
    except Exception as ex:
        logger.exception("Exception in get_default_gateway_interface_linux")
        return None

def get_interface_upstatus_linux(interfacename):
    """/sys/class/net/'interfacename'/operstate'."""
    try:
        with open('/sys/class/net/'+ str(interfacename) + '/operstate') as fh:
            for line in fh:
                status= line.strip()
                if status == "up":
                    return True
    except FileNotFoundError:
        #logger.warning("FileNotFoundError in get_interface_upstatus_linux for " + str(interfacename))
        pass
    except Exception as ex:
        logger.exception("Exception in get_interface_upstatus_linux")
    return False

def get_lsusb_linux():
    try:
        device_re = re.compile(b"Bus\s+(?P<bus>\d+)\s+Device\s+(?P<device>\d+).+ID\s(?P<id>\w+:\w+)\s(?P<name>.+)$", re.I)
        df = subprocess.check_output("lsusb")
        devices = []
        for i in df.split(b'\n'):
            if i:
                info = device_re.match(i)
                if info:
                    dinfo = info.groupdict()
                    dinfo['id'] = dinfo['id'].decode("utf-8", errors="ignore")
                    dinfo['name'] = dinfo['name'].decode("utf-8", errors="ignore")
                    dinfo['device'] = '/dev/bus/usb/%s/%s' % (dinfo.pop('bus').decode("utf-8", errors="ignore"), dinfo.pop('device').decode("utf-8", errors="ignore"))
                    devices.append(dinfo)
        #print(devices)
        return devices

    except Exception as ex:
        logger.exception("Exception in get_lsusb_linux")
        return False

def stop_tv():
    os.system("sudo /usr/bin/tvservice -o")

def get_version():
    rpiscripts = ""
    webinterface = ""
    lastinstalled = ""
    postupdatefinished = "0"
    try:
        with open('/var/www/html/version.txt', 'r') as fh:
            for line in fh:
                if line.strip().split(": ")[0] == "HoneyPi (last install on Raspi":
                    lastinstalled = line.strip().split(": ")[1].replace(")", "")
                elif line.strip().split()[0] == "rpi-scripts":
                    rpiscripts = line.strip().split()[1]
                elif line.strip().split()[0] == "rpi-webinterface":
                    webinterface = line.strip().split()[1]
                elif line.strip().split()[0] == "postupdatefinished":
                    postupdatefinished = line.strip().split()[1]
    except Exception as ex:
        logger.exception("Exception in get_version")
    return lastinstalled, rpiscripts, webinterface, postupdatefinished

def get_postupdatefinished():
    postupdatefinished = False
    try:
        lastinstalled, rpiscripts, webinterface, postupdatefinished = get_version()
        postupdatefinished = int(postupdatefinished)
        if postupdatefinished == 1:
            postupdatefinished = True
        return postupdatefinished
    except Exception as ex:
        logger.exception("Exception in get_postupdatefinished")

def get_rpiscripts_version():
    try:
        lastinstalled, rpiscripts, webinterface, postupdatefinished = get_version()
        return rpiscripts
    except Exception as ex:
        logger.exception("Exception in get_rpiscripts_version")

def runpostupgradescript():
    try:
        runpostupgradescriptfile = scriptsFolder + '/' + get_rpiscripts_version() + '/post-upgrade.sh'
        if os.path.isfile(runpostupgradescriptfile) and not get_postupdatefinished():
            logger.warning("Unfinished post_upgrade found in '" + runpostupgradescriptfile + "' Starting it again...")
            process = subprocess.Popen(runpostupgradescriptfile, shell=True, stdout=subprocess.PIPE)
            for line in process.stdout:
                logger.info(line.decode("utf-8"))
            process.wait()
        else:
            logger.debug("A finished post_upgrade found in (all good): " + runpostupgradescriptfile)
    except Exception as ex:
        logger.exception("Exception in runpostupgradescript")

def get_pi_model():
    model = ""
    try:
        with open('/proc/device-tree/model', 'r') as fh:
            model = fh.readline()
    except Exception as ex:
        logger.exception("Exception in get_pi_model")
    return model

def is_zero():
    try:
        if 'Zero' in get_pi_model():
            return True
        else:
            return False
    except Exception as ex:
        logger.exception("Exception in get_lsusb_linux")

def get_led_state(gpio=21):
   state = GPIO.input(gpio)
   if state:
       logger.debug("LED " + str(gpio) + " is currently on")
   else:
       logger.debug("LED " + str(gpio) + " is currently off")
   return state

def toggle_led(gpio, state):
   if state:
       stop_led(gpio)
   else:
       start_led(gpio)

def stop_hdd_led():
    # Turn Raspi-LED off
    off = 0
    if is_zero():
        off = 1
    else:
        os.system("sudo bash -c 'echo " + str(off) + " > /sys/class/leds/led0/brightness'") # green LED
        os.system("sudo bash -c 'echo none > /sys/class/leds/led0/trigger'") # green LED

def start_hdd_led():
    # Turn Raspi-LED on
    on = 1
    if is_zero():
        on = 0
    else:
        os.system("sudo bash -c 'echo " + str(on) + " > /sys/class/leds/led0/brightness'") # green LED
        os.system("sudo bash -c 'echo mmc0 > /sys/class/leds/led0/trigger'") # green LED

def stop_led(gpio=21):
    # Turn Raspi-LED off
    off = 0
    if is_zero():
        off = 1
        os.system("sudo bash -c 'echo " + str(off) + " > /sys/class/leds/led0/brightness'") # green LED
    os.system("sudo bash -c 'echo " + str(off) + " > /sys/class/leds/led1/brightness' 2>/dev/null") # red LED
    # Setup GPIO LED
    GPIO.setmode(GPIO.BCM) # Counting the GPIO PINS on the board
    GPIO.output(gpio, GPIO.LOW)

def start_led(gpio=21):
    # Turn Raspi-LED on
    on = 1
    if is_zero():
        on = 0
        os.system("sudo bash -c 'echo " + str(on) + " > /sys/class/leds/led0/brightness'") # green LED
    os.system("sudo bash -c 'echo " + str(on) + " > /sys/class/leds/led1/brightness' 2>/dev/null") # red LED
    # Setup GPIO LED
    GPIO.setmode(GPIO.BCM) # Counting the GPIO PINS on the board
    GPIO.output(gpio, GPIO.HIGH)

def toggle_blink_led(gpio=21, duration=0.25):
    GPIO.setmode(GPIO.BCM) # Counting the GPIO PINS on the board
    state = bool(GPIO.input(gpio))
    GPIO.output(gpio, not state)
    time.sleep(duration)
    GPIO.output(gpio, state)

def blink_led(gpio=21, duration=0.25):
    stop_led(gpio)
    time.sleep(duration)
    start_led(gpio)
    time.sleep(duration)
    stop_led(gpio)
    time.sleep(duration)
    start_led(gpio)
    time.sleep(duration)
    stop_led(gpio)
    time.sleep(duration)
    start_led(gpio)
    time.sleep(duration)
    stop_led(gpio)
    time.sleep(duration)
    start_led(gpio)
    time.sleep(duration)
    stop_led(gpio)

def run_wvdial(modem):
    modemapn = modem['apn']
    modempath = str(modem['ttyUSB'])
    founddevices = get_lsusb_linux()
    #print(founddevices)
    surfsticks = {}

    surfstick_file = Path(scriptsFolder + '/surfstick.json')
    surfstick_abs_path = surfstick_file.resolve()

    try:
        with io.open(surfstick_file, encoding="utf-8") as data_file:
            surfsticks = json.loads(data_file.read())
    except Exception as ex:
        logger.exception("Exception in connect_internet_modem reading surfstick_file.")

    if founddevices:
        devicefound = False
        for device in founddevices:
            deviceid = device['id']
            for surfstick in surfsticks:
                surfstickmodemid = surfstick['id']
                surfstickstorgaeid = surfstick['id-storage']
                if deviceid == surfstickmodemid:
                    if os.path.exists('/dev/'+ modempath):
                        logger.debug('Surfstick with ID ' + deviceid + ' ' + device['name'] + ' found in Modem mode on ' + device['device'])
                        devicefound = True
                        break
                    else:
                        if surfstick['modem'] != modempath:
                            if os.path.exists('/dev/'+ surfstick['modem']):
                                logger.warning('Surfstick with ID ' + deviceid + ' ' + device['name'] + ' found in Modem mode on ' + device['device'] +' with /dev/'+ surfstick['modem'] + ' as interface but /dev/' + modempath + 'is configured in settings. Please update settings!')
                            else:
                                logger.warning('Surfstick with ID ' + deviceid + ' ' + device['name'] + ' found in Modem mode on ' + device['device'] + ' but /dev/' + modempath + ' is missing')
                        else:
                            logger.warning('Surfstick with ID ' + deviceid + ' ' + device['name'] + ' found in Modem mode on ' + device['device'] + ' but /dev/' + surfstick['modem'] + ' is missing')
                elif deviceid ==  surfstickstorgaeid:
                    if modemisenabled:
                        logger.warning('Surfstick with ID ' + deviceid + ' ' + device['name'] + ', ' + surfstick['name'] + ', ' + surfstick['alternatename'] + ' found in Storage / Ethernet mode on ' + device['device'] + ' A modeswitch rule is required to use this stick with wvdial!')
        if not devicefound:
            logger.debug('No known Surfstick found!')
    if os.path.exists('/dev/'+ modempath): #Modem attatched to UART will not be found usíng above routine, but will work with configuration settings
        logger.info('Starting wvdial for Modem on path ' + str(modempath) + ' with APN ' + modemapn)
        os.system("(sudo sh " + scriptsFolder + "/shell-scripts/connection.sh run)&")
    else:
        logger.error("Not starting wvdial as no modem on configured path /dev/" + str(modempath) + " found! Please check configuration or modem")

def connect_internet_modem(settings):
    try:
        modem = settings['internet']['modem']
        modem_mode = modem['enabled']

        if modem_mode == 2:
            # if modem mode is wvdial
            run_wvdial(modem)
            logger.debug("Interface ppp0 is up: " +  str(get_interface_upstatus_linux('ppp0')))
        elif modem_mode == 1:
            # if modem mode is Hi.Link mode
            logger.debug('Surfstick is configured to be used in HiLink mode.')
            logger.info("Default gateway used for Internet connection is: " +  str(get_default_gateway_linux()))
            logger.debug("Interface wwan0 is up: " +  str(get_interface_upstatus_linux('wwan0')))
            logger.debug("Interface wlan0 is up: " +  str(get_interface_upstatus_linux('wlan0')))
            logger.debug("Interface wlan1 is up: " +  str(get_interface_upstatus_linux('wlan1')))
            logger.debug("Interface eth0 is up: " +  str(get_interface_upstatus_linux('eth0')))
            logger.debug("Interface eth1 is up: " +  str(get_interface_upstatus_linux('eth1')))
        elif modem_mode == 0:
            logger.debug('Use of surfstick is configured as disabled.')
            logger.debug("Default gateway used for Internet connection is: " +  str(get_default_gateway_linux()))
            logger.debug("Interface eth0 is up: " +  str(get_interface_upstatus_linux('eth0')))
            logger.debug("Interface wlan0 is up: " +  str(get_interface_upstatus_linux('wlan0')))
        else:
            logger.warning('Undefined state for surfstick mode.')
    except Exception as ex:
        logger.exception("Exception in connect_internet_modem")

def client_to_ap_mode():
    pause_wittypi_schedule()
    os.system("sudo sh " + scriptsFolder + "/shell-scripts/client_to_ap_mode.sh")

def ap_to_client_mode():
    continue_wittypi_schedule()
    os.system("sudo sh " + scriptsFolder + "/shell-scripts/ap_to_client_mode.sh")

def reboot():
    set_wittypi_schedule() # run wittypi runScript.sh to sync latest schedule
    os.system("sudo systemctl stop hostapd.service")
    os.system("sudo systemctl disable hostapd.service")
    os.system("sudo systemctl stop dnsmasq.service")
    os.system("sudo systemctl disable dnsmasq.service")
    logger.info('HoneyPi rebooting...')
    os.system("sudo reboot")

def shutdown():
    set_wittypi_schedule() # run wittypi runScript.sh to sync latest schedule
    os.system("sudo systemctl stop hostapd.service")
    os.system("sudo systemctl disable hostapd.service")
    os.system("sudo systemctl stop dnsmasq.service")
    os.system("sudo systemctl disable dnsmasq.service")
    logger.info('HoneyPi shutting down...')
    os.system("sudo shutdown -h 0")

def decrease_nice():
    pid = os.getpid()
    os.system("sudo renice -n -19 -p " + str(pid) + " >/dev/null")

def normal_nice():
    pid = os.getpid()
    os.system("sudo renice -n 0 -p " + str(pid) + " >/dev/null")

def start_single(file_path=".isActive"):
    file = scriptsFolder + '/' + file_path
    try:
        time_to_wait = 2*60 # 2 Minutes
        # wait as long as the file exists to block further measurements
        # because there is another HX711 process already running
        # but skip if the file is too old (time_to_wait)
        while os.path.exists(file):
            # skip waiting if file is older than 2 minutes
            # this is because the last routine could be canceled irregular
            # and the file could be still existing
            filetime = os.stat(file).st_mtime
            if filetime < time.time()-time_to_wait:
                logger.warning("Skiped waiting because the measurement process we are waiting for was likely not properly finished.")
                os.remove(file) # remove the old file
                break
            time.sleep(1)
            logger.info("Measurement waits for a process to finish. Another measurement job is running at the moment.")
        # create file to stop other HX711 readings
        f = open(file, "x")
    except Exception as ex:
        logger.exception("Exception in start_single")
        pass
    finally:
        decrease_nice()

def stop_single(file_path=".isActive"):
    file = scriptsFolder + '/' + file_path
    try:
        # remove file because reading HX711 finished
        if os.path.exists(file):
            os.remove(file)
        else:
            logger.warning('stop_single: File does not exists.')
    except Exception as ex:
        logger.exception("Exception in stop_single")
    finally:
        normal_nice()

def miliseconds():
    return int(round(time.time() * 1000))

# reduce size if file is to big
def check_file(file, size=5, entries=25, skipFirst=0):
    try:
        # If bigger than 5MB
        if os.path.getsize(file) > size * 1024 * 1024:
            readFile = open(file)
            lines = readFile.readlines()
            readFile.close()
            w = open(file,'w')
            # delete first 25 lines in file
            # When CSV: skip first entry because it is header (skipFirst=1)
            del lines[skipFirst:entries]
            w.writelines(lines)
            w.close()
    except FileNotFoundError:
        pass
    except Exception as ex:
        logger.exception("Exception in check_file")

def error_log(e=None, printText=None):
    try:
        """file = scriptsFolder + '/error.log'
        check_file(file) # reset file if it gets to big

        # generate printed text"""
        if printText and e:
            printText = printText + " | " + repr(e)
        elif e:
            printText = e
        else:
            printText = "No Text defined."
        """
        print(printText)

        dt = datetime.now()
        timestamp = dt.replace(microsecond=0)

        # write to file
        with open(file, "a") as myfile:
            myfile.write (str(timestamp) + " | " + printText + "\n")
        """
        logger.info(printText)
    except Exception:
        pass

def check_undervoltage():
    message = ""
    try:
        undervoltage = str(os.popen("sudo vcgencmd get_throttled").readlines())
        if "0x0" in undervoltage:
            message = "No undervoltage alarm"
            logger.debug(message)

        elif "0x50000" in undervoltage:
            message = "Undervoltage alarm had happened since system start " + undervoltage
            logger.warning(message)

        elif "0x50005" in undervoltage:
            message = "Undervoltage alarm is currently raised " + undervoltage
            logger.warning(message)

    except Exception as ex:
        message = "Exception in function check_undervoltage: " + repr(ex)
        logger.warning(message)
    return message

def wait_for_internet_connection(maxTime=10):
    i = 0
    while i < maxTime:
        i+=1
        try:
            response = str(urllib.request.urlopen('http://www.msftncsi.com/ncsi.txt', timeout=1).read().decode('utf-8'))
            if response == "Microsoft NCSI":
                logger.debug("Success: Connection established after " + str(i) + " seconds.")
                return True
        except:
            pass
        finally:
            time.sleep(1)

    return False

def check_internet_connection():
    try:
        response = str(urllib.request.urlopen('http://www.msftncsi.com/ncsi.txt', timeout=1).read().decode('utf-8'))
        if response == "Microsoft NCSI":
            return True
    except Exception as ex:
        logger.exception("Exception check_internet_connection")
    return False

def delete_settings():
    os.remove(settingsFile)

def clean_fields(ts_fields, countChannels, debug):
    ts_fields_cleaned = {}
    fieldNew = {};
    for field in ts_fields:
        fieldNumber = int(field.replace('field',''))
        fieldNumberNew = fieldNumber - (8 * countChannels)
        if fieldNumberNew <= 8 and fieldNumberNew > 0 :
            ts_fields_cleaned['field' + str(fieldNumberNew)]=ts_fields['field' + str(fieldNumber)]
    logger.debug('Cleaned dictionary:' + json.dumps(ts_fields_cleaned))
    return ts_fields_cleaned

# decorater used to block function printing to the console
def blockPrinting(func):
    def func_wrapper(*args, **kwargs):
        # block all printing to the console
        sys.stdout = open(os.devnull, 'w')
        # call the method in question
        value = func(*args, **kwargs)
        # enable all printing to the console
        sys.stdout = sys.__stdout__
        # pass the return value of the method back
        return value

    return func_wrapper

def pause_wittypi_schedule():
    try:
        if os.path.isfile(wittypi_scheduleFile) and os.stat(wittypi_scheduleFile).st_size > 1:
            os.rename(wittypi_scheduleFile, wittypi_scheduleFile + ".bak")
            update_wittypi_schedule("")
            logger.debug("Pausing wittyPi schedule...")

    except Exception as ex:
        logger.exception("Error in function pause_wittypi_schedule")

def continue_wittypi_schedule():
    try:
        if os.path.isfile(wittypi_scheduleFile + ".bak") and os.path.isfile(wittypi_scheduleFile):
            if os.stat(wittypi_scheduleFile).st_size > 1 and os.stat(wittypi_scheduleFile + ".bak").st_size != os.stat(wittypi_scheduleFile).st_size:
                # if schedule is not empty and schedule changed in the meantime (=> someone saved a new schedule in maintenance)
                os.remove(wittypi_scheduleFile + ".bak")
                logger.debug("Continuing wittyPi schedule (someone saved a new schedule in maintenance).")
            else:
                os.rename(wittypi_scheduleFile + ".bak", wittypi_scheduleFile)
                set_wittypi_schedule()
                logger.debug("Continuing wittyPi schedule...")
    except Exception as ex:
        logger.exception("Error in function continue_wittypi_schedule")

def set_wittypi_schedule():
    try:
        schedulefile_exists = os.path.isfile(wittypi_scheduleFile) and os.stat(wittypi_scheduleFile).st_size > 1
        wittyPiPath = ''
        if os.path.exists(homeFolder + '/wittyPi'):
            wittyPiPath = homeFolder + '/wittyPi'
            logger.debug("wittyPi 2 or wittyPi Mini installation detected in: " + wittyPiPath)
        elif os.path.exists(homeFolder + '/wittypi'):
            wittyPiPath = homeFolder + '/wittypi'
            logger.debug("wittypi 3 or 3 Mini installation detected in: " + wittyPiPath)
        else:
            logger.debug("No WittyPi software installed.")

        if os.path.isfile(wittyPiPath + '/wittyPi.sh') and os.path.isfile(wittyPiPath + '/syncTime.sh') and os.path.isfile(wittyPiPath + '/runScript.sh'):
            if schedulefile_exists:
                logger.debug("Setting  wittyPi schedule...")
                os.system("sudo sh " + backendFolder + "/shell-scripts/change_wittypi.sh 1 > /dev/null")
            else:
                logger.debug("Pausing  wittyPi schedule ...")
                os.system("sudo sh " + backendFolder + "/shell-scripts/change_wittypi.sh 0 > /dev/null")
            return True
        else:
            logger.debug('wittyPi installation is missing files - wittyPi.sh exists: ' + str(os.path.isfile(wittyPiPath + '/wittyPi.sh')) + ' syncTime.sh exists: ' + str(os.path.isfile(wittyPiPath + '/syncTime.sh')) + ' runScript.sh exists: ' +  str(os.path.isfile(wittyPiPath + '/runScript.sh')))
    except Exception as ex:
        logger.exception("Error in function set_wittypi_schedule")
    return False

def update_wittypi_schedule(schedule):
    try:
        # write values to file
        outfile = open(wittypi_scheduleFile, "w")
        outfile.truncate(0)
        outfile.write(schedule)
        outfile.close()
        # set file rights
        uid = pwd.getpwnam("www-data").pw_uid
        gid = grp.getgrnam("www-data").gr_gid
        os.chown(wittypi_scheduleFile, uid, gid)

        set_wittypi_schedule()
        return True
    except Exception as ex:
        logger.exception("Error in function update_wittypi_schedule")

    return False

def write_modeswitch_rule(id):
    try:
        modeswitchfilename = '/etc/usb_modeswitch/'+id
        # write values to file
        modeswitchfile = open(modeswitchfilename, "w")
        rule = "# Huawei E353 (3.se)\n" + "TargetVendor=" + "0x12d1" + "\n" + "TargetProduct=" + "0x1f01" +"\n" + "MessageContent=" +'"55534243123456780000000000000011062000000100000000000000000000"' + "\n" + "NoDriverLoading=1"
        outfile.write(rule)
        outfile.close()

    except Exception as ex:
        logger.exception("Error in function write_modeswitch_rule")

def getStateFromStorage(variable, default_value=False):
    file = scriptsFolder + '/.' + variable
    try:
        if os.path.exists(file):
            with open(file, 'r') as f:
                content = f.readline().replace('\n', '').replace('\r', '')
                if len(content) > 0:
                    if content == "True":
                        content = True
                    elif content == "False":
                        content = False
                    else:
                        logger.warning("Variable '" + variable + "' Fallback to default value")
                        content = default_value
                    logger.debug("Variable '" + variable + "' is type: '" + type(content).__name__ + "' with content: '" + str(content) + "'")
                    return content
                else:
                    logger.debug("Variable '" + variable + "' has initial state because file is empty.")
                    return None

        else:
            logger.debug("Variable '" + variable + "' does not exists. default_value = " + str(default_value))
    except Exception as ex:
        logger.exception("Error in function getStateFromStorage")
        pass
    return default_value

def setStateToStorage(variable, value):
    file = scriptsFolder + '/.' + variable
    try:
        with open(file, 'w') as f:
            print(value, file=f)
    except Exception as ex:
        logger.exception("Error in function setStateToStorage")
        pass
    return value
