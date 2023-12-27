#!/usr/bin/env python3
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
import inspect
import logging
import RPi.GPIO as GPIO
from pathlib import Path
import socket, struct, fcntl
import subprocess
import re

from constant import scriptsFolder, settingsFile, local_tz

logger = logging.getLogger('HoneyPi.utilities')

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

    
def is_service_active(servicename='honeypi.service'):
    try:
        status = os.system('systemctl is-active --quiet ' + servicename)
        if status == 0:
            return True
        return False
    except Exception as ex:
        logger.exception("Error in function is_service_active")

def get_abs_timedifference(datetime1, datetime2):
    get_abs_timedelta_totalseconds = 0
    try:
        #datetime1 = datetime.now(local_tz)
        if datetime2 >= datetime1:
            timedelta = datetime2 - datetime1
        else:
            timedelta = datetime1 - datetime2
        abs_timedelta_totalseconds = abs(timedelta.total_seconds())
    except Exception as ex:
        logger.exception("Error in function get_abs_timedifference")
    return abs_timedelta_totalseconds

def is_system_datetime_valid():
    datetimevalid = False
    try:
        datetimenow = datetime.now(local_tz)
        if datetimenow.year != 1969 and datetimenow.year != 1970:
            datetimevalid = True
        else:
            logger.critical("System time (" + datetimenow.strftime("%a %d %b %Y %H:%M:%S") +") has not been set before (stays in year 1969/1970).")

    except Exception as ex:
        logger.exception("Error in function validate_system_time")
    return datetimevalid

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
                        logger.warning("Variable '" + variable + "': Fallback to default value")
                        content = default_value
                    logger.debug("Variable '" + variable + "' is type: '" + type(content).__name__ + "' with content: '" + str(content) + "'")
                    return content
                else:
                    logger.debug("Variable '" + variable + "' has initial state '" + str(default_value) + "' because file is empty")
                    return default_value

        else:
            logger.debug("Variable '" + variable + "' does not exists. Use default:" + str(default_value))
    except Exception as ex:
        logger.exception("Error in function getStateFromStorage")
        pass
    return default_value

from wittypiutilities import get_wittypi_status, check_wittypi_rtc, set_wittypi_schedule, pause_wittypi_schedule, continue_wittypi_schedule


def setStateToStorage(variable, value):
    file = scriptsFolder + '/.' + variable
    try:
        with open(file, 'w') as f:
            print(value, file=f)
        if os.path.exists(file):
            logger.debug("Variable '" + variable + " with type: '" + type(value).__name__ + "' with content: '" + str(value) + "' wtitten to file " + str(file))
        else:
            logger.critical("Variable '" + variable + "' file " + str(file) + " still does not exists.")

    except Exception as ex:
        logger.exception("Error in function setStateToStorage")
        pass
    return value

def whoami():
    try:
        iam = pwd.getpwuid(os.geteuid()).pw_name
        return iam
    except Exception as ex:
        logger.exception("Exception in whoami")

def fix_fileaccess(file=scriptsFolder + '/err*.*'):
    try:
        os.system('sudo chown pi ' + file)
        os.system('sudo chgrp pi ' + file)
        os.system('sudo chmod ug+w ' + file)
    except Exception as ex:
        logger.exception("Exception in fix_fileaccess")

def offlinedata_prepare(ts_channels):
    try:
        offlinedata = []
        for (channelIndex, channel) in enumerate(ts_channels, 1):
            channeldata = {}
            channel_id = channel['ts_channel_id']
            channeldata['channel_id'] = channel_id
            csv_file = scriptsFolder + '/offline-' + str(channel_id) + '.csv'
            logger.debug("Checking offline file: " + csv_file + " for channel " + str(channel_id))
            #filename = scriptsFolder + "/offline-"
            if os.path.exists(csv_file):
                with open(csv_file, "r") as fp:
                    logger.debug("Offline file: " +  csv_file + " found")
                    for i, line in enumerate(fp):
                        pass
                    #print(line)

                    reader = line.strip().split(",")
                    #time.sleep(0.5)
                    channeldata['Date'] = reader[0][5:10]
                    channeldata['Time'] = reader[0][11:16]
                    channeldata['field1'] = reader[1]
                    channeldata['field2'] = reader[2]
                    channeldata['field3'] = reader[3]
                    channeldata['field4'] = reader[4]
                    channeldata['field5'] = reader[5]
                    channeldata['field6'] = reader[6]
                    channeldata['field7'] = reader[7]
                    channeldata['field8'] = reader[8]
                    #t = oled_view_channel(channel_id, Time, Date, field1, field2, field3, field4, field5, field6, field7, field8)
                offlinedata.append(channeldata)
            else:
                logger.debug("No offline File: " + csv_file + " does exist")
        return(offlinedata)
    except Exception as ex:
        logger.exception("Exception in offlinedata_prepare")

def get_interfacelist():
    try:
        ifaces = os.listdir('/sys/class/net/')
        return(ifaces)

    except Exception as ex:
        logger.exception("get_interfacelist")
        pass
    return None

def thingspeak_datetime():
    return datetime.utcnow().replace(microsecond=0).isoformat()

def get_cpu_temp():
    try:
        ## CPU-Temperatur ermitteln
        fd = open("/sys/class/thermal/thermal_zone0/temp")
        temperatur = float(fd.readline().rstrip())/1000.0
        fd.close()
        return temperatur
    except Exception as ex:
        logger.exception("Exception in get_cpu_temp")
        pass
    return None

@blockPrinting # suppress print messages on systemstart
def sync_time_ntp():
    try:
        os.system("sudo systemctl stop ntp")
        ntptimediff = os.popen("sudo ntpd -q -g -D 4 | grep 'ntpd:' | awk '/^ntpd:/{print $NF}'").read().strip()
        os.system("sudo systemctl start ntp")
        if not ntptimediff:
            logger.warning("Could not extract ntpd timedifference in sync_time_ntp")
        return(ntptimediff)
    except:
        logger.exception("Exception in get_ntp_status")
    return None

def get_ntp_status():
    try:
        ntpstatus = os.popen('timedatectl status | grep "System clock synchronized" | grep -Eo "(yes|no)"').read().strip().lower()
        if ntpstatus == "yes":
            ntpstatus = True
        elif ntpstatus == "no":
            ntpstatus = False
        else:
            ntpstatus = None
        return(ntpstatus)
    except Exception as ex:
        logger.exception("Exception in get_ntp_status")
        pass
    return None


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
                logger.info(line.decode("utf-8").rstrip("\n"))
            process.wait()
        else:
            if os.path.isfile(runpostupgradescriptfile):
                logger.debug("A finished post_upgrade found in '" + runpostupgradescriptfile + "' (all good)")
            else:
                logger.debug("No post_upgrade file found in '" + runpostupgradescriptfile + "' (all good)")
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
        logger.exception("Exception in is_zero")

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

def turn_led(onoff, led, trigger=False):
    # ACT = led0 # green LED
    # PWR = led1 # red LED
    if onoff == 1:
        trigger_echo = "mmc0"
    else:
        trigger_echo = "none"
    if led == "led0":
        newname = "ACT"
    else:
        newname = "PWR"
    if os.path.exists("/sys/class/leds/"+led+"/brightness"):
        os.system("sudo bash -c 'echo " + str(onoff) + " > /sys/class/leds/"+led+"/brightness'")
        if trigger == True:
            os.system("sudo bash -c 'echo "+trigger_echo+" > /sys/class/leds/"+led+"/trigger'")
    else:
        os.system("sudo bash -c 'echo " + str(onoff) + " > /sys/class/leds/"+newname+"/brightness'")
        if trigger == True:
            os.system("sudo bash -c 'echo "+trigger_echo+" > /sys/class/leds/"+newname+"/trigger'")


def stop_hdd_led():
    # Turn Raspi-LED off
    off = 0
    if is_zero():
        off = 1
    else:
        turn_led(off, "led0", True)

def start_hdd_led():
    # Turn Raspi-LED on
    on = 1
    if is_zero():
        on = 0
    else:
        turn_led(on, "led0", True)

def stop_led(gpio=21):
    # Turn Raspi-LED off
    off = 0
    if is_zero():
        off = 1
        turn_led(off, "led0")
    turn_led(off, "led1")

    # Setup GPIO LED
    GPIO.setmode(GPIO.BCM) # Counting the GPIO PINS on the board
    GPIO.output(gpio, GPIO.LOW)

def start_led(gpio=21):
    # Turn Raspi-LED on
    on = 1
    if is_zero():
        on = 0
        turn_led(on, "led0")
    turn_led(on, "led1")
    # Setup GPIO LED
    GPIO.setmode(GPIO.BCM) # Counting the GPIO PINS on the board
    GPIO.output(gpio, GPIO.HIGH)

def toggle_blink_led(gpio=21, duration=0.25):
    GPIO.setmode(GPIO.BCM) # Counting the GPIO PINS on the board
    state = bool(GPIO.input(gpio))
    if is_zero():
        turn_led(int(state), "led0")
    turn_led(int(not state), "led1")
    GPIO.output(gpio, not state)
    time.sleep(duration)
    if is_zero():
        turn_led(int(not state), "led0")
    turn_led(int(state), "led1")
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
                surfstickstorageid = surfstick['id-storage']
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
                elif deviceid ==  surfstickstorageid:
                    logger.warning('Surfstick with ID ' + deviceid + ' ' + device['name'] + ', ' + surfstick['name'] + ', ' + surfstick['alternatename'] + ' found in Storage mode on ' + device['device'] + '. A modeswitch rule is required to use this stick with wvdial! You can save a modeswitch file to this path: /etc/usb_modeswitch.d/')
        if not devicefound:
            logger.debug('No known Surfstick found!')
    if os.path.exists('/dev/'+ modempath): # Modem attatched to UART will not be found usíng above routine, but will work with configuration settings
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
            logger.debug("Default gateway used for Internet connection is: " +  str(get_default_gateway_linux()))
            logger.debug("Check Interface status - wwan0 is up: " +  str(get_interface_upstatus_linux('wwan0')) + " usb0 is up: " +  str(get_interface_upstatus_linux('usb0')) + " wlan0 is up: " +  str(get_interface_upstatus_linux('wlan0')) + " eth0 is up: " +  str(get_interface_upstatus_linux('eth0')) + " eth1 is up: " +  str(get_interface_upstatus_linux('eth1')))
        elif modem_mode == 0:
            logger.debug('Use of surfstick is configured as disabled.')
            logger.debug("Default gateway used for Internet connection is: " +  str(get_default_gateway_linux()))
            logger.debug("Check Interface status - eth0 is up: " +  str(get_interface_upstatus_linux('eth0')) + " wlan0 is up: " +  str(get_interface_upstatus_linux('wlan0')))
        else:
            logger.warning('Undefined state for surfstick mode.')
    except Exception as ex:
        logger.exception("Exception in connect_internet_modem")

def client_to_ap_mode():
    logger.info("Starting HoneyPi maintenance webinterface...")
    pause_wittypi_schedule()
    process = subprocess.Popen(scriptsFolder + "/shell-scripts/client_to_ap_mode.sh", shell=True, stdout=subprocess.PIPE)
    for line in process.stdout:
        logger.debug(line.decode("utf-8").rstrip("\n"))
    process.wait()

def ap_to_client_mode():
    logger.info("Stopping HoneyPi maintenance webinterface...")
    process = subprocess.Popen(scriptsFolder + "/shell-scripts/ap_to_client_mode.sh", shell=True, stdout=subprocess.PIPE)
    for line in process.stdout:
        logger.debug(line.decode("utf-8").rstrip("\n"))
    process.wait()
    continue_wittypi_schedule()

def reboot(settings):
    wittypi_status = get_wittypi_status(settings)
    check_wittypi_rtc(settings, wittypi_status)
    if 'startup_time_local' in wittypi_status:
        old_startup_time = wittypi_status['startup_time_local']
    else:
        old_startup_time = None
    if 'shutdown_time_local' in wittypi_status:
        old_shutdown_time = wittypi_status['shutdown_time_local']
    else:
        old_shutdown_time = None
    set_wittypi_schedule() # run wittypi runScript.sh to sync latest schedule
    wittypi_status = get_wittypi_status(settings)
    if (('startup_time_local' in wittypi_status) and (old_startup_time != wittypi_status['startup_time_local'])) or (('shutdown_time_local' in wittypi_status) and (old_shutdown_time != wittypi_status['shutdown_time_local'])):
        logger.info("Startup / shutdown time on wittypi updated during reboot!")
    os.system("sudo systemctl stop hostapd.service")
    os.system("sudo systemctl disable hostapd.service")
    os.system("sudo systemctl stop dnsmasq.service")
    os.system("sudo systemctl disable dnsmasq.service")
    logger.info('HoneyPi rebooting...')
    os.system("sudo reboot")

def shutdown(settings):
    wittypi_status = get_wittypi_status(settings)
    check_wittypi_rtc(settings, wittypi_status)
    if 'startup_time_local' in wittypi_status:
        old_startup_time = wittypi_status['startup_time_local']
    else:
        old_startup_time = None
    if 'shutdown_time_local' in wittypi_status:
        old_shutdown_time = wittypi_status['shutdown_time_local']
    else:
        old_shutdown_time = None
    set_wittypi_schedule() # run wittypi runScript.sh to sync latest schedule
    wittypi_status = get_wittypi_status(settings)
    if (('startup_time_local' in wittypi_status) and (old_startup_time != wittypi_status['startup_time_local'])) or (('shutdown_time_local' in wittypi_status) and (old_shutdown_time != wittypi_status['shutdown_time_local'])):
        logger.info("Startup / shutdown time on wittypi updated during shutdown!")
    os.system("sudo systemctl stop hostapd.service")
    os.system("sudo systemctl disable hostapd.service")
    os.system("sudo systemctl stop dnsmasq.service")
    os.system("sudo systemctl disable dnsmasq.service")
    if settings['wittyPi']['enabled']:
        if ('startup_time_local' in wittypi_status) and not wittypi_status['startup_time_local'] is None:
            logger.info('HoneyPi shutting down, next startup schedule is ' + wittypi_status['startup_time_local'].strftime("%a %d %b %Y %H:%M:%S"))
        else:
            logger.critical('HoneyPi shutting down but no startup is scheduled!')
    else:
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
        # If file is writable
        if os.access(file, os.W_OK):
            logger.debug("File access rights are correct for '"+ file + "'")
        else:
            logger.info("File access rights were missing for '"+ file + "', applying permission changes...")
            if os.path.exists(file):
                fix_fileaccess(file)
            else:
                logger.warning("Canceled fixing file access rights for '"+ file + "' because file did not exist.")
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
    logger.error("Do not call this function. Deprecated.")

def check_undervoltage(since_last_check=""):
    #since_last_check = '0x7' #for check since last check # TODO add comment with info what 0x7 means
    message = ""
    try:
        undervoltage = str(os.popen("sudo vcgencmd get_throttled " + since_last_check).readlines())
        if "0x0" in undervoltage:
            message = "No undervoltage alarm"

        elif "0x50000" in undervoltage:
            if since_last_check == "":
                message = "Undervoltage alarm had happened since system start " + undervoltage
            else:
                message = "Undervoltage alarm had happened since last check " + undervoltage
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
        if field in ('latitude', 'longitude', 'elevation', 'created_at'):
            ts_fields_cleaned[field]=ts_fields[field]
            continue
        fieldNumber = int(field.replace('field',''))
        fieldNumberNew = fieldNumber - (8 * countChannels)
        if fieldNumberNew <= 8 and fieldNumberNew > 0 :
            ts_fields_cleaned['field' + str(fieldNumberNew)]=ts_fields['field' + str(fieldNumber)]
    return ts_fields_cleaned

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
