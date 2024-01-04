#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


#original from https://github.com/marl2en/wittypi4python
#updated version on https://github.com/elschnorro77/wittypi4python

"""
library for WittyPi 3 mini
Version 3.50
"""

name = "wittypi"
__version__ = '0.1.0'
# pip3 install smbus2
# pip3 install pytz

import logging
from logging.handlers import RotatingFileHandler
logger = logging.getLogger('WittyPi')


import datetime as dt
import calendar
import time
import pytz
import os
import re

local_tz = dt.datetime.utcnow().astimezone().tzinfo
#local_tz = pytz.timezone('Europe/Stockholm')
utc_tz = pytz.timezone('UTC')

from smbus2 import SMBus
import RPi.GPIO as GPIO

#WittyPi 3
RTC_ADDRESS = 0x68
I2C_MC_ADDRESS = 0x69


I2C_ID=0
I2C_VOLTAGE_IN_I=1
I2C_VOLTAGE_IN_D=2
I2C_VOLTAGE_OUT_I=3
I2C_VOLTAGE_OUT_D=4
I2C_CURRENT_OUT_I=5
I2C_CURRENT_OUT_D=6
I2C_POWER_MODE=7
I2C_LV_SHUTDOWN=8

#WittyPi 3
I2C_CONF_ADDRESS=9
I2C_CONF_DEFAULT_ON=10
I2C_CONF_PULSE_INTERVAL=11
I2C_CONF_LOW_VOLTAGE=12
I2C_CONF_BLINK_LED=13
I2C_CONF_POWER_CUT_DELAY=14
I2C_CONF_RECOVERY_VOLTAGE=15
I2C_CONF_DUMMY_LOAD=16
I2C_CONF_ADJ_VIN=17
I2C_CONF_ADJ_VOUT=18
I2C_CONF_ADJ_IOUT=19

#WittyPi 3
I2C_RTC_SECONDS=0
I2C_RTC_MINUTES=1
I2C_RTC_HOURS=2
I2C_RTC_DAYS=4
I2C_RTC_WEEKDAYS=3
I2C_RTC_MONTHS=5
I2C_RTC_YEARS=6

I2C_CONF_SECOND_ALARM1=7
I2C_CONF_MINUTE_ALARM1=8
I2C_CONF_HOUR_ALARM1=9
I2C_CONF_DAY_ALARM1=10
#I2C_CONF_WEEKDAY_ALARM1=31

#I2C_CONF_SECOND_ALARM2=11
I2C_CONF_MINUTE_ALARM2=11
I2C_CONF_HOUR_ALARM2=12
I2C_CONF_DAY_ALARM2=13
#I2C_CONF_WEEKDAY_ALARM2=36

I2C_RTC_CTRL1=14
I2C_RTC_CTRL2=15

HALT_PIN=4    # halt by GPIO-4 (BCM naming)
SYSUP_PIN=17  # output SYS_UP signal on GPIO-17 (BCM naming)

# Check if a WittyP Pi 4 is connected via I2C
try:
    with SMBus(1) as bus: # does not work on Raspberry 1 as SMBus(0) is needed on Raspberry 1
        time.sleep(1) # short delay
        bus.read_byte(0x08) # Check I2C address from Witty Pi 4

    # No exception?
    # Then, define Witty Pi 4 constants and overwrite WittyPi 3 variables
    RTC_ADDRESS = 0x08
    I2C_MC_ADDRESS=0x08

    I2C_CONF_ADDRESS=16
    I2C_CONF_DEFAULT_ON=17
    I2C_CONF_PULSE_INTERVAL=18
    I2C_CONF_LOW_VOLTAGE=19
    I2C_CONF_BLINK_LED=20
    I2C_CONF_POWER_CUT_DELAY=21
    I2C_CONF_RECOVERY_VOLTAGE=22
    I2C_CONF_DUMMY_LOAD=23
    I2C_CONF_ADJ_VIN=24
    I2C_CONF_ADJ_VOUT=25
    I2C_CONF_ADJ_IOUT=26
    I2C_ALARM1_TRIGGERED=9
    I2C_ALARM2_TRIGGERED=10
    I2C_ACTION_REASON=11
    I2C_FW_REVISION=12

    I2C_CONF_SECOND_ALARM1=27
    I2C_CONF_MINUTE_ALARM1=28
    I2C_CONF_HOUR_ALARM1=29
    I2C_CONF_DAY_ALARM1=30
    I2C_CONF_WEEKDAY_ALARM1=31

    I2C_CONF_SECOND_ALARM2=32
    I2C_CONF_MINUTE_ALARM2=33
    I2C_CONF_HOUR_ALARM2=34
    I2C_CONF_DAY_ALARM2=35
    I2C_CONF_WEEKDAY_ALARM2=36

    I2C_RTC_CTRL1=54
    I2C_RTC_CTRL2=55

    I2C_RTC_SECONDS=58
    I2C_RTC_MINUTES=59
    I2C_RTC_HOURS=60
    I2C_RTC_DAYS=61
    I2C_RTC_WEEKDAYS=62
    I2C_RTC_MONTHS=63
    I2C_RTC_YEARS=64
except: # exception if read_byte fails
    pass

def send_sysup():
    try:
        GPIO.setmode(GPIO.BCM) # Counting the GPIO PINS on the board
        GPIO.setwarnings(False)
        GPIO.setup(SYSUP_PIN, GPIO.OUT)
        GPIO.output(SYSUP_PIN, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(SYSUP_PIN, GPIO.LOW)
    except RuntimeError as ex:
        logger.critical("RuntimeError occuered on GPIO access! "+ str(ex))
    except Exception as ex:
        logger.exception("Exception in send_sysup ")

def send_halt():
    try:
        GPIO.setmode(GPIO.BCM) # Counting the GPIO PINS on the board
        GPIO.setwarnings(False)
        # restore halt pin
        GPIO.setup(HALT_PIN, GPIO.IN)
        GPIO.output(HALT_PIN, GPIO.HIGH)
    except RuntimeError as ex:
        logger.critical("RuntimeError occuered on GPIO access! "+ str(ex))
    except Exception as ex:
        logger.exception("Exception in send_sysup ")

def add_halt_pin_event(halt_pin_event_detected_function):
    try:
        # setup Button
        GPIO.setmode(GPIO.BCM) # Counting the GPIO PINS on the board
        GPIO.setup(HALT_PIN, GPIO.IN) # Set HALT_PIN to be an input pin
        bouncetime = 100 # ignoring further edges for 100ms for switch bounce handling
        # register button press event
        GPIO.add_event_detect(HALT_PIN, GPIO.BOTH, callback=halt_pin_event_detected_function, bouncetime=bouncetime)
    except RuntimeError as ex:
        logger.critical("RuntimeError occuered on GPIO access! "+ str(ex))
    except Exception as ex:
        logger.exception("Exception in send_sysup ")

def halt_pin_event_detected():
    if GPIO.input(HALT_PIN) == 0:
        logger.critical("halt_pin_event_detected")

def dec2hex(datalist):
    try:
        res = []
        for v in datalist:
            hexInt = 10*(v//16) + (v%16)
            res.append(hexInt)
        return res
    except Exception as ex:
        logger.exception("Exception in dec2hex ")

def dec2bcd(dec):
    try:
        #result= $((10#$1/10*16+(10#$1%10)))
        t = int(dec) // 10;
        o = int(dec) - t * 10;
        result = (t << 4) + o;
        return result
    except Exception as ex:
        logger.exception("Exception in dec2bcd ")

def is_rtc_connected():
    try:
        out=[]
        with SMBus(1) as bus:
            time.sleep(2) # short delay
            b = bus.read_byte(RTC_ADDRESS)
            out.append(b)
        logger.debug("RTC is connected")
        return True
    except IOError as ex:
        if str(ex) == "[Errno 121] Remote I/O error":
            logger.debug("RTC is not connected")
            return False
        if str(ex) == "[Errno 16] Device or resource busy":
            logger.debug("RTC is busy - trying to remove module rtc-ds1307")
            os.system('sudo rmmod rtc-ds1307')
            try:
                out=[]
                with SMBus(1) as bus:
                    time.sleep(1) # short delay
                    b = bus.read_byte(RTC_ADDRESS)
                    out.append(b)
                logger.debug("RTC is connected")
                return True
            except IOError as ex:
                if str(ex) == "[Errno 121] Remote I/O error":
                    logger.debug("RTC is not connected")
                    return False
        else:
            logger.exception("IOError in is_rtc_connected ")
    except Exception as ex:
        logger.exception("Exception in is_rtc_connected ")

def is_mc_connected():
    try:
        out=[]
        with SMBus(1) as bus:
            time.sleep(1) # short delay
            b = bus.read_byte(I2C_MC_ADDRESS)
            out.append(b)
        logger.debug("MC is connected")
        return True
    except IOError as ex:
        if str(ex) == "[Errno 121] Remote I/O error":
            logger.debug("MC is not connected")
            return False
    except Exception as ex:
        logger.exception("Exception in is_mc_connected")

def get_wittypi_folder():
    wittyPiPath = None
    try:
        if os.path.exists('/home/pi/wittyPi'):
            wittyPiPath = '/home/pi/wittyPi'
            logger.debug("WittyPi 2 or WittyPi Mini installation detected in: " + wittyPiPath)
        elif os.path.exists('/home/pi/wittypi'):
            wittyPiPath = '/home/pi/wittypi'
            logger.debug("Wittypi 3 (Mini) installation detected in: " + wittyPiPath)
        else:
            logger.debug("No WittyPi installation detected!")
    except Exception as ex:
        logger.exception("Exception in get_wittypi_folder")
    return wittyPiPath


rtc_connected = is_rtc_connected()
mc_connected = is_mc_connected()
wittyPiPath = get_wittypi_folder()


def get_firmwareversion():
    firmwareversion = 0
    try:
        out=[]
        if mc_connected:
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                b = bus.read_byte_data(I2C_MC_ADDRESS, I2C_ID)
                out.append(b)
            firmwareversion =  dec2hex(out)[0]
        logger.debug("MC firmwareversion: "+ str(firmwareversion))
    except Exception as ex:
        logger.exception("Exception in get_firmwareversion" )
    return firmwareversion


def get_rtc_timestamp():
    out=[]
    UTCtime,localtime,timestamp = None, None, None
    try:
        if rtc_connected:
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                data = [I2C_RTC_SECONDS, I2C_RTC_MINUTES, I2C_RTC_HOURS, I2C_RTC_WEEKDAYS, I2C_RTC_DAYS, I2C_RTC_MONTHS, I2C_RTC_YEARS]
                for ele in data:
                    b = bus.read_byte_data(RTC_ADDRESS, ele)
                    out.append(b)
            res = dec2hex(out)
            UTCtime = dt.datetime(res[6]+2000,res[5],res[4],res[2],res[1],res[0])
            UTCtime = pytz.utc.localize(UTCtime).astimezone(utc_tz)
            localtime = UTCtime.astimezone(local_tz)
            timestamp = int(time.mktime(UTCtime.timetuple()))
            logger.debug("RTC time is " + str(localtime.strftime("%a %d %b %Y %H:%M:%S")) + " " + str(local_tz))
    except Exception as ex:
        logger.exception("Exception in get_rtc_timestamp")
    return UTCtime,localtime,timestamp



def get_input_voltage():
    res = 0
    try:
        if mc_connected:
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                i = bus.read_byte_data(I2C_MC_ADDRESS, I2C_VOLTAGE_IN_I)
                d = bus.read_byte_data(I2C_MC_ADDRESS, I2C_VOLTAGE_IN_D)
            res = i + float(d)/100.
    except Exception as ex:
        logger.exception("Exception in get_input_voltage")
    return res

def get_startup_time(): # [?? 07:00:00], ignore: [?? ??:??:00] and [?? ??:??:??]
    res = []
    try:
        if rtc_connected:
            out = []
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                for ele in [I2C_CONF_SECOND_ALARM1 ,I2C_CONF_MINUTE_ALARM1 ,I2C_CONF_HOUR_ALARM1 ,I2C_CONF_DAY_ALARM1 ]:
                    b = bus.read_byte_data(RTC_ADDRESS, ele)
                    out.append(b)
            res = dec2hex(out) # sec, min, hour, day
    except Exception as ex:
        logger.exception("Exception in get_startup_time")
    return calcTime(res)

def add_one_month(orig_date):
    # advance year and month by one month
    new_date = None
    try:
        new_year = orig_date.year
        new_month = orig_date.month + 1
        # note: in datetime.date, months go from 1 to 12
        if new_month > 12:
            new_year += 1
            new_month -= 12
        last_day_of_month = calendar.monthrange(new_year, new_month)[1]
        new_day = min(orig_date.day, last_day_of_month)
        new_date = orig_date.replace(year=new_year, month=new_month, day=new_day)
    except Exception as ex:
        logger.exception("Exception in add_one_month")
    return new_date

def calcTime(res=[0, 0, 0]):
    """calculate startup/shutdown time from wittypi output"""
    time_local = None
    timedelta = None
    str_time = [] # [0, 20, 80]
    try:
        nowUTC = dt.datetime.now(utc_tz)
        nowLOCAL = nowUTC.astimezone(local_tz)
        #  sec, min, hour, day
        logger.debug("Calculating datetime for " + str(res))
        day = 0
        if len(res) >= 3:
            day = res[-1]
            hour = res[-2]
            minute = res[-3]
        if len(res) == 4:
            second = res[-4]
        else:
            second = 0
        if (day == 0): # [0, 0, 0] if day = 0 -> no time or date defined
            #time_utc = dt.datetime(nowUTC.year+1,nowUTC.month,nowUTC.day,nowUTC.hour,nowUTC.minute,0) #.astimezone(utc_tz) # add 1 year
            #time_utc = utc_tz.localize(time_utc)
            time_utc = None
        else:
            try:
                time_temp = dt.datetime(nowUTC.year,nowUTC.month,day,nowUTC.hour,nowUTC.minute,second)
            except ValueError as ex:
                oldmonth = nowUTC.strftime("%B")
                nowUTC = add_one_month(nowUTC)
                nowLOCAL = nowUTC.astimezone(local_tz)
                logger.debug('For '+ oldmonth + ' the day ' + str(day) + ' does not exist, added a month')
                pass
            except Exception as ex:
                logger.exception("Another Exception in calcTime")

            if (day == 80) and (hour != 80): # day not defined, start every day
                time_utc = dt.datetime(nowUTC.year,nowUTC.month,nowUTC.day,hour,minute,second) #.astimezone(utc_tz)
                time_utc = utc_tz.localize(time_utc)
                if time_utc < nowUTC: time_utc += dt.timedelta(days=1)
            if (day != 80) and (hour != 80): # day defined, start every month
                time_utc = dt.datetime(nowUTC.year,nowUTC.month,day,hour,minute,second) #.astimezone(utc_tz)
                time_utc = utc_tz.localize(time_utc)
                if time_utc < nowUTC: time_utc = add_one_month(time_utc)
            if (day == 80) and (hour == 80) and (minute == 80) and (second == 80): # day and hour and minute not defined, start every minute (invalid using software but possible on webinterface
                time_utc = dt.datetime(nowUTC.year,nowUTC.month,nowUTC.day,nowUTC.hour,nowUTC.minute,0) #.astimezone(utc_tz)
                time_utc = utc_tz.localize(time_utc)
                if time_utc < nowUTC: time_utc += dt.timedelta(minutes=1)
            if (day == 80) and (hour == 80) and (minute == 80) and (second != 80): # day and hour and minute not defined, start every minute at seconds
                time_utc = dt.datetime(nowUTC.year,nowUTC.month,nowUTC.day,nowUTC.hour,nowUTC.minute,second) #.astimezone(utc_tz)
                time_utc = utc_tz.localize(time_utc)
                if time_utc < nowUTC: time_utc += dt.timedelta(minutes=1)
            if (day == 80) and (hour == 80) and (minute != 80): # day and hour not defined, start every hour
                time_utc = dt.datetime(nowUTC.year,nowUTC.month,nowUTC.day,nowUTC.hour,minute,second) #.astimezone(utc_tz)
                time_utc = utc_tz.localize(time_utc)
                if time_utc < nowUTC: time_utc += dt.timedelta(hours=1)

        if time_utc is not None:
            time_local =  time_utc.astimezone(local_tz)
            timedelta = time_local - nowLOCAL
        strtime=[]
        for ele in res:
            if ele == 80: strtime.append('??')
            else: strtime.append(str(ele))
        if len(strtime) == 4: str_time = strtime[-1] + ' ' + strtime[-2] + ':' + strtime[-3] + ':' + strtime[-4]
        else: str_time = strtime[-1] + ' ' + strtime[-2] + ':' + strtime[-3] + ':00'
    except Exception as ex:
        logger.exception("Exception in calcTime")
    return time_utc,time_local,str_time,timedelta

def calcTimeOld(res):
    """calculate startup/shutdown time from wittypi output"""
    nowUTC = dt.datetime.now(utc_tz)
    nowLOCAL = dt.datetime.now(local_tz)
    #  sec, min, hour, day
    if (res[-1] == 0): # [0, 0, 0] if day = 0 -> no time or date defined
        startup_time_local = dt.datetime(nowLOCAL.year+1,nowLOCAL.month,nowLOCAL.day,nowLOCAL.hour,nowLOCAL.minute,0).astimezone(local_tz) # add 1 year
    else:
        if (res[-1] == 80) and (res[-2] != 80): # day not defined, start every day
            startup_time_local = dt.datetime(nowLOCAL.year,nowLOCAL.month,nowLOCAL.day,res[-2],res[-3],0).astimezone(local_tz)
            if startup_time_local < nowLOCAL: startup_time_local += dt.timedelta(days=1)
        if (res[-1] != 80) and (res[-2] != 80): # day defined, start every month
            startup_time_local = dt.datetime(nowLOCAL.year,nowLOCAL.month,res[-1],res[-2],res[-3],0).astimezone(local_tz)
            if startup_time_local < nowLOCAL: startup_time_local = add_one_month(startup_time_local)
        if (res[-1] == 80) and (res[-2] == 80): # day and hour not defined, start every hour
            startup_time_local = dt.datetime(nowLOCAL.year,nowLOCAL.month,nowLOCAL.day,nowLOCAL.hour,res[-3],0).astimezone(local_tz)
            if startup_time_local < nowLOCAL: startup_time_local += dt.timedelta(hours=1)
    #startup_time_local =  startup_time_utc.astimezone(local_tz)
    startup_time_utc =  startup_time_local.astimezone(utc_tz)
    strtime = [] # [0, 20, 80]
    for ele in res:
        if ele == 80: strtime.append('??')
        else: strtime.append(str(ele))
    if len(strtime) == 4: str_time = strtime[-1] + ' ' + strtime[-2] + ':' + strtime[-3] + ':' + strtime[-4]
    else: str_time = strtime[-1] + ' ' + strtime[-2] + ':' + strtime[-3] + ':00'
    timedelta = startup_time_local - nowLOCAL
    return startup_time_utc,startup_time_local,str_time,timedelta

def get_shutdown_time(): # [?? 07:00:00], ignore: [?? ??:??:00] and [?? ??:??:??]
    res = []
    try:
        if rtc_connected:
            out = []
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                for ele in [I2C_CONF_MINUTE_ALARM2,I2C_CONF_HOUR_ALARM2,I2C_CONF_DAY_ALARM2]: #[0x0B, 0x0C, 0x0D]
                    b = bus.read_byte_data(RTC_ADDRESS, ele)
                    out.append(b)
            res = dec2hex(out) # sec, min, hour, day
    except Exception as ex:
        logger.exception("Exception in get_shutdown_time")
    return calcTime(res)

def datetime2stringtime(dt):
    result = ""
    try:
        result = dt.strftime("%d %H:%M:%S")
    except Exception as ex:
        logger.exception("Exception in datetime2stringtime")
    return result


def stringtime2timetuple(stringtime='?? 20:00:00'):
    try:
        if stringtime is not None:
            logger.debug('stringtime: ' + str(stringtime))
            day = stringtime.split(' ')[0]
            if day == '??':
                day = 80 #128
            elif 1<= int(day) <=31:
                day = int(day)
            else:
                logger.debug('invalid day: ' + str(day))
                day = None
            hour = stringtime.split(' ')[1].split(':')[0]
            if hour == '??':
                hour = 80 #128
            elif 0<= int(hour) <=23:
                hour = int(hour)
            else:
                logger.debug('invalid hour: ' + str(hour))
                hour = None
            minute = stringtime.split(' ')[1].split(':')[1]
            if minute == '??':
                minute = 80 #128
            elif 0<= int(minute) <=59:
                minute = int(minute)
            else:
                logger.debug('invalid minute: ' + str(minute))
                minute = None
            if len(stringtime) > 8:
                second = stringtime.split(' ')[1].split(':')[2]
                if second == '??':
                    second = 80 #128
                elif 0<= int(second) <=59:
                    second = int(second)
                else:
                    logger.debug('invalid second: ' + str(second))
                    second = None
                logger.debug('day: ' + str(day) + ' hour: ' + str(hour) + 'minute: ' + str(minute)+ ' second: ' + str(second))
                return (second,minute,hour,day)
            else:
                logger.debug('day: ' + str(day) + ' hour: ' + str(hour) + 'minute: ' + str(minute))
                return (minute,hour,day)
    except Exception as ex:
        logger.exception("Exception in stringtime2timetuple")
    return None

def system_to_rtc():
    for x in range(0, 5):  # try 5 times
        try:
            if rtc_connected:
                sys_ts=dt.datetime.now(utc_tz)
                second=sys_ts.strftime("%S")
                minute=sys_ts.strftime("%M")
                hour=sys_ts.strftime("%H")
                day=sys_ts.strftime("%u")
                date=sys_ts.strftime("%d")
                month=sys_ts.strftime("%m")
                year=sys_ts.strftime("%y")
                with SMBus(1) as bus:
                    time.sleep(1) # short delay after SMBus(1) might help connection tinemout issues
                    bus.write_byte_data(RTC_ADDRESS, I2C_RTC_SECONDS, dec2bcd(second))
                    bus.write_byte_data(RTC_ADDRESS, I2C_RTC_MINUTES, dec2bcd(minute))
                    bus.write_byte_data(RTC_ADDRESS, I2C_RTC_HOURS, dec2bcd(hour))
                    bus.write_byte_data(RTC_ADDRESS, I2C_RTC_WEEKDAYS, dec2bcd(day))
                    bus.write_byte_data(RTC_ADDRESS, I2C_RTC_DAYS, dec2bcd(date))
                    bus.write_byte_data(RTC_ADDRESS, I2C_RTC_MONTHS, dec2bcd(month))
                    bus.write_byte_data(RTC_ADDRESS, I2C_RTC_YEARS, dec2bcd(year))
                return True
        except Exception as ex:
            logger.exception("Exception in system_to_rtc")
            time.sleep(1)  # wait for 1 seconds before trying to fetch the data again
    return False

def rtc_to_system():
    try:
        if rtc_connected:
            UTCtime,localtime,timestamp = get_rtc_timestamp()
            if UTCtime is not None and localtime is not None:
                if rtc_time_is_valid(localtime):
                    logger.info('Writing RTC time ' + localtime.strftime("%a %d %b %Y %H:%M:%S") + ' to system...')
                    value = os.system('sudo date -u -s "' + UTCtime.strftime("%d %b %Y %H:%M:%S") + '" >>/dev/null')
                    if value == 0:
                        logger.debug('Successfully wrote RTC time to system...')
                    else:
                        logger.error('Failure writing RTC time to system...')
    except Exception as ex:
        logger.exception("Exception in system_to_rtc")
    return False

def set_shutdown_time(stringtime='?? 20:00'):
    try:
        if rtc_connected:
            minute,hour,day = stringtime2timetuple(stringtime)
            if (day is not None ) and (hour is not None) and (minute is not None):
                with SMBus(1) as bus:
                    time.sleep(1) # short delay
                    bus.write_byte_data(RTC_ADDRESS, 14,7) # write_byte_data(i2c_addr, register, value, force=None) #WittyPi Mini and 3 only
                    #bus.write_byte_data(RTC_ADDRESS, I2C_CONF_SECOND_ALARM2 ,dec2bcd(minute)) #WittyPi 4 only
                    bus.write_byte_data(RTC_ADDRESS, I2C_CONF_MINUTE_ALARM2 ,dec2bcd(minute))
                    bus.write_byte_data(RTC_ADDRESS, I2C_CONF_HOUR_ALARM2 ,dec2bcd(hour))
                    bus.write_byte_data(RTC_ADDRESS, I2C_CONF_DAY_ALARM2 ,dec2bcd(day))
                return True
            else:
                logger.debug("invalid Time")
    except Exception as ex:
        logger.exception("Exception in set_shutdown_time")
    return False

def set_startup_time(stringtime='?? 20:00:00'):
    try:
        if rtc_connected:
            second,minute,hour,day = stringtime2timetuple(stringtime)
            if (day is not None ) and (hour is not None) and (minute is not None) and (second is not None):
                with SMBus(1) as bus:
                    time.sleep(1) # short delay
                    bus.write_byte_data(RTC_ADDRESS, 14,7) # write_byte_data(i2c_addr, register, value, force=None)#WittyPi Mini and 3 only
                    bus.write_byte_data(RTC_ADDRESS, I2C_CONF_SECOND_ALARM1 ,dec2bcd(second))
                    bus.write_byte_data(RTC_ADDRESS, I2C_CONF_MINUTE_ALARM1 ,dec2bcd(minute))
                    bus.write_byte_data(RTC_ADDRESS, I2C_CONF_HOUR_ALARM1 ,dec2bcd(hour))
                    bus.write_byte_data(RTC_ADDRESS, I2C_CONF_DAY_ALARM1 ,dec2bcd(day))
                return True
            else:
                logger.debug("invalid Time")
    except Exception as ex:
        logger.exception("Exception in set_startup_time")
    return False

def clear_startup_time():
    try:
        if rtc_connected:
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                bus.write_byte_data(RTC_ADDRESS, I2C_CONF_SECOND_ALARM1 ,0) # write_byte_data(i2c_addr, register, value, force=None)
                bus.write_byte_data(RTC_ADDRESS, I2C_CONF_MINUTE_ALARM1 ,0) # write_byte_data(i2c_addr, register, value, force=None)
                bus.write_byte_data(RTC_ADDRESS, I2C_CONF_HOUR_ALARM1 ,0) # write_byte_data(i2c_addr, register, value, force=None)
                bus.write_byte_data(RTC_ADDRESS, I2C_CONF_DAY_ALARM1 ,0) # write_byte_data(i2c_addr, register, value, force=None)
            return True
    except Exception as ex:
        logger.exception("Exception in clear_startup_time")
    return False

def clear_shutdown_time():
    try:
        if rtc_connected:
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                #bus.write_byte_data(RTC_ADDRESS, I2C_CONF_SECOND_ALARM2,0) # write_byte_data(i2c_addr, register, value, force=None) #WittyPi 4 only
                bus.write_byte_data(RTC_ADDRESS, I2C_CONF_MINUTE_ALARM2,0) # write_byte_data(i2c_addr, register, value, force=None)
                bus.write_byte_data(RTC_ADDRESS, I2C_CONF_HOUR_ALARM2,0) # write_byte_data(i2c_addr, register, value, force=None)
                bus.write_byte_data(RTC_ADDRESS, I2C_CONF_DAY_ALARM2,0) # write_byte_data(i2c_addr, register, value, force=None)
            return True
    except Exception as ex:
        logger.exception("Exception in clear_shutdown_time")
    return False

def get_power_mode():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                b = bus.read_byte_data(I2C_MC_ADDRESS, I2C_POWER_MODE)
            return b # int 0 or 1
    except Exception as ex:
        logger.exception("Exception in get_power_mode")

def get_output_voltage():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                i = bus.read_byte_data(I2C_MC_ADDRESS, I2C_VOLTAGE_OUT_I)
                d = bus.read_byte_data(I2C_MC_ADDRESS, I2C_VOLTAGE_OUT_D)
            return float(i) + float(d)/100.
    except Exception as ex:
        logger.exception("Exception in get_output_voltage")

def get_output_current():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                i = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CURRENT_OUT_I)
                d = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CURRENT_OUT_D)
            return float(i) + float(d)/100.
    except Exception as ex:
        logger.exception("Exception in get_output_current")

def get_low_voltage_threshold():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                i = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CONF_LOW_VOLTAGE)
            if i == 255: thresh = 'disabled'
            else: thresh = float(i)/10.
            return thresh
    except Exception as ex:
        logger.exception("Exception in get_low_voltage_threshold")

def get_recovery_voltage_threshold():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                i = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CONF_RECOVERY_VOLTAGE)
            if i == 255: thresh = 'disabled'
            else: thresh = float(i)/10.
            return thresh
    except Exception as ex:
        logger.exception("Exception in get_recovery_voltage_threshold")

def set_low_voltage_threshold(volt='11.5'):
    try:
        if mc_connected:
            if len(volt) == 4:
                volt = int(float(volt) * 10.)
                if not (50 < volt < 254): volt = 255 # clear threshold if threshold is not between 5V and 25.4V
                else: print(' setting threshold to ',volt)
                try:
                    with SMBus(1) as bus:
                        time.sleep(1) # short delay
                        bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_LOW_VOLTAGE,volt)
                    return True
                except Exception as e:
                    print(e)
                    return False
                else:
                    print('wrong input for voltage threshold',volt)
                    return False
    except Exception as ex:
        logger.exception("Exception in set_low_voltage_threshold")

def set_recovery_voltage_threshold(volt='12.8'):
    try:
        if mc_connected:
            if len(volt) == 4:
                volt = int(float(volt) * 10.)
                if not (50 < volt < 254):
                    volt = 255 # clear threshold if threshold is not between 5V and 25.4V
                else:
                    print(' setting threshold to ',volt)
                    with SMBus(1) as bus:
                        time.sleep(1) # short delay
                        bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_RECOVERY_VOLTAGE,volt)
                    return True
            else:
                logger.error('wrong input for voltage threshold ' + str(volt))
    except Exception as ex:
        logger.exception("Exception in set_low_voltage_threshold ")
    return False

def clear_low_voltage_threshold():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_LOW_VOLTAGE, 0xFF)
            return True
    except Exception as ex:
        logger.exception("Exception in clear_low_voltage_threshold ")
    return False

def clear_recovery_voltage_threshold():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_RECOVERY_VOLTAGE, 0xFF)
            return True
    except Exception as ex:
        logger.exception("Exception in clear_recovery_voltage_threshold ")
    return False

def get_temperature():
    try:
        if rtc_connected:
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                ctrl = bus.read_byte_data(RTC_ADDRESS, 14)
                ctrl2 = 7|0x20 #39 bitwise or
                bus.write_byte_data(RTC_ADDRESS, 14,ctrl2)
                time.sleep(0.2)
                t1 = bus.read_byte_data(RTC_ADDRESS, 17)
                t2 = bus.read_byte_data(RTC_ADDRESS, 18)
                c = ''
                sign = t1&0x80
                if sign < 0: c+='-'
                else: c += str(t1&0x7F)
                c+='.'
                c += str(((t2&0xC0)>>6)*25 )
            return float(c)
    except Exception as ex:
        logger.exception("Exception in get_temperature")

def clear_alarm_flags(byte_F=0x0):
    try:
        if rtc_connected:
            if byte_F==0x0:
                with SMBus(1) as bus:
                    time.sleep(1) # short delay
                    byte_F=bus.read_byte_data(RTC_ADDRESS, I2C_RTC_CTRL2)
            #print(format(byte_F, '0>8b')) #((byte_F)))
            byte_F=(byte_F&0xFC)
            #print(format(byte_F, '0>8b')) #((byte_F)))
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                bus.write_byte_data(RTC_ADDRESS, I2C_RTC_CTRL2, byte_F)
    except Exception as ex:
        logger.exception("Exception in clear_alarm_flags")

def get_alarm_flags(RTC_ALARM_ADDRESS=I2C_RTC_CTRL2):
    try:
        if rtc_connected:
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                byte_F=bus.read_byte_data(RTC_ADDRESS, RTC_ALARM_ADDRESS)
            #print(format(byte_F, '0>8b')) #((byte_F)))
            return byte_F
    except Exception as ex:
        logger.exception("Exception in clear_alarm_flags")

def check_alarm_flags(byte_F):
    #byte_F should be read from I2C_RTC_ADDRESS in register 0x0F)
    alarm = 0
    try:
        if (byte_F&0x1) != 0:
            # woke up by alarm 1 (startup)
            logger.debug('System startup as scheduled.')
            alarm = 1
        elif (byte_F&0x2) != 0:
            # woke up by alarm 2 (shutdown), turn it off immediately
            logger.debug('Seems I was unexpectedly woken up by shutdown alarm, must go back to sleep...')
            #do_shutdown $HALT_PIN $has_rtc
            alarm = 2
    except Exception as ex:
        logger.exception("Exception in check_alarm_flags")
    return alarm

def do_shutdown():
    try:
        # restore halt pin
        send_halt()
        if rtc_connected:
            # clear alarm flags
            clear_alarm_flags()
            # only enable alarm 1 (startup)
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                bus.write_byte_data(RTC_ADDRESS, 0x0E,0x05)
            os.system("sudo shutdown -h now")
    except Exception as ex:
        logger.exception("Exception in do_shutdown")

def get_power_cut_delay():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                pcd = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CONF_POWER_CUT_DELAY)
            pcd=pcd/10
            return pcd
    except Exception as ex:
        logger.exception("Exception in get_power_cut_delay")

def set_power_cut_delay(delay=8):
    try:
        if mc_connected:
            maxVal=8.0;
            if get_firmwareversion() >= 35:
                maxVal='25.0'
            if delay >= 0 and delay <= maxVal:
                d=delay*10
                with SMBus(1) as bus:
                    time.sleep(1) # short delay
                    bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_POWER_CUT_DELAY, d)
                logger.debug("Power cut delay set to ", delay , " seconds!")
                return True
            else:
                logger.error('wrong input for power cut delay threshold ' + str(delay) + 'Please input from 0.0 to ' + str(maxVal) + ' ...')
    except Exception as ex:
        logger.exception("Exception in set_power_cut_delay")
    return False

def get_dummy_load_duration():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                dummy_load_duration = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CONF_DUMMY_LOAD)
            return dummy_load_duration #[0]
    except Exception as ex:
        logger.exception("Exception in get_dummy_load_duration")

def set_dummy_load_duration(duration=0):
    try:
        if mc_connected:
            if duration >=- 0 and duration <= 254:
                with SMBus(1) as bus:
                    time.sleep(1) # short delay
                    bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_DUMMY_LOAD, duration)
                logger.debug("Dummy load duration set to " + str(duration) + " !")
                return True
            else:
                logger.error('wrong input for dummy load duration ' + str(duration) + ' Please input from 0 to 254')
    except Exception as ex:
        logger.exception("Exception in set_dummy_load_duration")
    return False

def set_pulsing_interval(interval):
    try:
        if mc_connected:
            pi = None
            if interval==1:
                pi = 0x06
            elif interval==2:
                pi = 0x07
            elif interval==4:
                pi = 0x08
            elif interval==8:
                pi = 0x0
            else:
                logger.error('wrong input for pulsing invterval' +str(interval) + ' Please input 1,2,4 or 8 seconds')
            if pi is not None:
                with SMBus(1) as bus:
                    time.sleep(1) # short delay
                    bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_PULSE_INTERVAL, pi)
                logger.debug("Pulsing interval set to " + str(interval) + "seconds")
                return True
    except Exception as ex:
        logger.exception("Exception in set_pulsing_interval")
    return False

def get_pulsing_interval():
    try:
        if mc_connected:
            interval = None
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                pi = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CONF_PULSE_INTERVAL)
            if pi == 0x09:
                interval=8
            elif pi == 0x07:
                interval=2
            elif pi == 0x06:
                interval=1
            else:
                interval=4
            return interval
    except Exception as ex:
        logger.exception("Exception in get_pulsing_interval")

def set_white_led_duration(duration):
    try:
        if mc_connected:
            if duration >=- 0 and duration <= 254:
                    with SMBus(1) as bus:
                        time.sleep(1) # short delay
                        bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_BLINK_LED, duration)
                        logger.debug("White LED duration set to "+ str(duration) + " !")
            else:
                logger.error('wrong input for white LED duration ' + str(duration) + ' Please input from 0 to 254')
    except Exception as ex:
        logger.exception("Exception in set_white_led_duration")
    return False

def get_white_led_duration():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                duration = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CONF_BLINK_LED)
            return duration
    except Exception as ex:
        logger.exception("Exception in get_white_led_duration")

def set_default_state(state):
    try:
        if mc_connected:
            if int(state)>=0 and int(state)<=1:
                hexstate = None
                if int(state)==1:
                    hexstate = 0x01
                elif int(state)==0:
                    hexstate = 0x00
                with SMBus(1) as bus:
                    time.sleep(1) # short delay
                    bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_DEFAULT_ON, hexstate)
                if hexstate == 0x01:
                    logger.debug('Default state when powered set to "ON"!')
                elif hexstate == 0x00:
                    logger.debug('Default state when powered set to "OFF"!')
                return True
            else:
                logger.error('wrong input for default state. Please use 1 for "Default ON" or 0 for "Default OFF"')
    except Exception as ex:
        logger.exception("Exception in set_default_state")
    return False

def get_default_state(): #1=ON, 0=OFF
    try:
        if mc_connected:
            with SMBus(1) as bus:
                time.sleep(1) # short delay
                hexstate = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CONF_DEFAULT_ON)
            if hexstate == 0x01:
                state=1
            elif hexstate == 0x00:
                state=0
            return state
    except Exception as ex:
        logger.exception("Exception in get_default_state")

def rtc_time_is_valid(rtc_time_utc):
    try:

        if rtc_time_utc.strftime("%Y") == "1999" or rtc_time_utc.strftime("%Y") == "2000": # if you never set RTC time before
            logger.debug('RTC time ' + rtc_time_utc.strftime("%a %d %b %Y %H:%M:%S")+ ' ' + str(utc_tz) + ' has not been set before (stays in year 1999/2000).')
            return False
        else:
            logger.debug('RTC time ' + rtc_time_utc.strftime("%a %d %b %Y %H:%M:%S")+ ' ' + str(utc_tz) + ' is a valid time.')
            return True
    except Exception as ex:
        logger.exception("Exception in rtc_time_is_valid")

def is_schedule_file_in_use(schedule_file = str(wittyPiPath) + '/schedule.wpi'):

    if os.path.isfile(schedule_file) and os.stat(schedule_file).st_size > 1:
        return True
    else:
        return False

def extract_timestamp(datetimestr):
    timestamp = None
    try:
        datetimestr = datetimestr.split(' ')
        date_reg = re.search('(20[0-9][0-9])-([0-9][0-9])-([0-3][0-9])', datetimestr[0]).groups()
        time_reg = re.search('([0-2][0-9]):([0-5][0-9]):([0-5][0-9])', datetimestr[1]).groups()
        if len(date_reg)==3 and len(time_reg) ==3:
            #timestamp = dt.datetime(dt.date(int(date_reg[0]), int(date_reg[1]), int(date_reg[2])), dt.time(int(time_reg[0]), int(time_reg[1]), int(time_reg[2])))
            timestamp = dt.datetime(int(date_reg[0]), int(date_reg[1]), int(date_reg[2]), int(time_reg[0]), int(time_reg[1]), int(time_reg[2]), tzinfo=local_tz)
            logger.debug('extracted timestamp: ' + timestamp.strftime("%a %d %b %Y %H:%M:%S"))
        else:
            logger.debug('invalid timestamp!')

    except Exception as ex:
        logger.exception("Exception in extract_timestamp")
    return timestamp

def get_local_date_time(timestr, wildcard=True):
    result = None
    try:
        nowUTC = dt.datetime.now(utc_tz)
        when=timestr
        logger.debug("Calculating get_local_date_time for "+ str(timestr))
        #IFS=' ' read -r date timestr <<< "$when"
        #IFS=':' read -r hour minute second <<< "$timestr"
        date = when.split(' ')[0]
        bk_date = date
        hour=when.split(' ')[1].split(':')[0]
        bk_hour=hour
        minute=when.split(' ')[1].split(':')[1]
        bk_min=minute
        second=when.split(' ')[1].split(':')[2]
        bk_sec=second
        if date == '??':
            date='01'
        if date == '0':
            return result #0 at date - nothing scheduled
        if hour == '??':
            hour='12'
        if minute == '??':
            minute='00'
        if second == '??':
            second='00'
        result_year=nowUTC.strftime("%Y")
        curDate=nowUTC.strftime("%d")
        result_month = ""
        if date < curDate:
            result_month = add_one_month(dt.date(int(result_year), int(nowUTC.strftime("%m")), 15)).strftime("%m")
        else:
            result_month = nowUTC.strftime("%m")
        try:
            time_temp = dt.datetime(nowUTC.year,int(result_month),int(date),nowUTC.hour,nowUTC.minute,nowUTC.second)
        except ValueError as ex:
            oldmonth = result_month
            nowUTC = add_one_month(nowUTC)
            result_month = nowUTC.strftime("%m")
            logger.debug('For '+ oldmonth + ' the day ' + str(date) + ' does not exist, added a month')
            pass
        except Exception as ex:
            logger.exception("Another Exception in calcTime")
        result_datetime = dt.datetime(int(result_year), int(result_month), int(date), int(hour), int(minute), int(second), 0 ,utc_tz)
        result = datetime2stringtime(result_datetime)
        #IFS=' ' read -r date timestr <<< "$result"
        #IFS=':' read -r hour minute second <<< "$timestr"
        date = result.split(' ')[0]
        hour=result.split(' ')[1].split(':')[0]
        minute=result.split(' ')[1].split(':')[1]
        second=result.split(' ')[1].split(':')[2]
        if wildcard:
            if bk_date == '??':
                date='??'
            if bk_hour == '??':
                hour='??'
            if bk_min == '??':
                minute='??'
            if bk_sec == '??':
                second='??'
        result = date + ' ' + hour + ' ' + minute + ' ' + second
    except Exception as ex:
        logger.exception("Exception in get_local_date_time")
    return result


def schedule_script_interrupted():
    try:
        startup_time_utc,startup_time_local,startup_str_time,startup_timedelta = get_startup_time()
        shutdown_time_utc,shutdown_time_local,shutdown_str_time,shutdown_timedelta = get_shutdown_time()
        startup_time=get_local_date_time(startup_str_time, False)
        shutdown_time=get_local_date_time(shutdown_str_time, False)
        if startup_time is not None and shutdown_time is not None:

            """    local st_timestamp=$(date --date="$(date +%Y-%m-)$startup_time" +%s)
            local sd_timestamp=$(date --date="$(date +%Y-%m-)$shutdown_time" +%s)"""
            cur_timestamp = dt.datetime.now(local_tz)
            if startup_time_local > cur_timestamp  and shutdown_time_local < cur_timestamp:
                return True
    except Exception as ex:
        logger.exception("Exception in schedule_script_interrupted")
    return False


def get_schedule_file(schedule_file = str(wittyPiPath) + '/schedule.wpi'):
    schedule_file_lines = []
    try:
        if is_schedule_file_in_use(schedule_file):
            with open(schedule_file) as schedule_file_fh:
                schedule_file_lines = schedule_file_fh.readlines()
            logger.debug('Succesfully read ' + str(schedule_file))
        else:
            logger.info ("File " + schedule_file + "not found, skip reading schedule script.")
    except Exception as ex:
        logger.exception("Exception in get_schedule_file")
    return schedule_file_lines

def schedule_file_lines2schedule_file_data(schedule_file_lines):
    begin = None
    end = None
    states = []
    schedule_file_data = {}
    count=0
    try:
        for line in schedule_file_lines:
            cpos=line.find('#')
            if cpos != -1:
                line = line[0:cpos]
            line = line.strip()
            if line.startswith('BEGIN'):
                begin = extract_timestamp(line[6:].strip())
            elif line.startswith('END'):
                end = extract_timestamp(line[4:].strip())
            elif line != "":
                states.append(line)
                count = count+1
        if begin == None:
            logger.debug('I can not find the begin time in the script...')
        elif end == None:
            logger.debug('I can not find the end time in the script...')
        elif count == 0:
            logger.debug('I can not find any state defined in the script.')
        else:
            logger.debug('Succesfully read Begin: ' + begin.strftime("%a %d %b %Y %H:%M:%S") + ' End: ' + end.strftime("%a %d %b %Y %H:%M:%S") + ' States: ' + str(count))
    except Exception as ex:
        logger.exception("Exception in get_schedule_file")
    schedule_file_data['begin'] = begin
    schedule_file_data['end'] = end
    schedule_file_data['states'] = states
    return schedule_file_data

def extract_duration(state):
    duration=0
    try:
        #print(str(state))
        day_reg=re.findall('D([0-9]+)', state)
        hour_reg=re.findall('H([0-9]+)', state)
        min_reg=re.findall('M([0-9]+)', state)
        sec_reg=re.findall('S([0-9]+)', state)
        #if day_reg is not None:
        for index, element in enumerate(day_reg):
                duration=duration+int(element)*86400
        #if hour_reg is not None:
        for index, element in enumerate(hour_reg):
                duration=duration+int(element)*3600
        #if min_reg is not None:
        for index, element in enumerate(min_reg):
                duration=duration+int(element)*60
        #if sec_reg is not None:
        for index, element in enumerate(sec_reg):
                duration=duration+int(element)*1
        #print(duration)
    except Exception as ex:
        logger.exception("Exception in extract_duration")
    return duration

def verify_schedule_data(schedule_file_data):
    begin = None
    beginissue=""
    end = None
    endissue=""
    states = []
    count=0
    script_duration=0
    found_off=0
    found_on=0
    found_irregular=0
    found_irregular_order = 0
    found_off_wait=0
    found_on_wait=0
    try:
        if not 'begin' in schedule_file_data or schedule_file_data['begin'] is None:
            logger.critical('I can not find the begin time in the script...')
            beginissue='I can not find the begin time in the script...'
        elif not 'end' in schedule_file_data or schedule_file_data['end'] is None:
            logger.critical('I can not find the end time in the script...')
            endissue='I can not find the end time in the script...'
        elif not 'states' in schedule_file_data or len(schedule_file_data['states']) == 0:
            logger.critical('I can not find any state defined in the script.')
        else:
            begin = schedule_file_data['begin']
            end = schedule_file_data['end']
            states = schedule_file_data['states']
            count=len(states)
            logger.debug('Count: ' + str(count))
            cur_time = dt.datetime.now(local_tz)
            logger.debug('begin: ' + begin.strftime("%a %d %b %Y %H:%M:%S"))
            if int(begin.strftime("%Y")) >= 2038 or int(begin.strftime("%Y")) <= 2010:
                logger.critical('begin is invalid, must be less than 2038 and greater than 2010')
                beginissue='begin is invalid, must be less than 2038 and greater than 2010'
            logger.debug('end: ' + end.strftime("%a %d %b %Y %H:%M:%S"))
            if int(end.strftime("%Y")) >= 2038 or int(end.strftime("%Y")) <= 2010:
                logger.critical('end is invalid, must be less than 2038 and greater than 2010')
                endissue='end is invalid, must be less than 2038 and greater than 2010'
            logger.debug('cur_time: ' + cur_time.strftime("%a %d %b %Y %H:%M:%S"))
            if cur_time < begin:
                logger.debug('The schedule script starts in future')
                cur_time=begin
            elif cur_time >= begin:
                logger.debug('The schedule script started in past')
            elif  cur_time >= end:
                logger.critical('The schedule script has ended already.')
            #else:
            index=0
            found_on_state=False
            while index <= (count-1):
                #logger.debug('index: ' + str(index))
                script_duration=script_duration+extract_duration(states[index])
                if states[index].startswith('ON'):
                    if not found_on_state:
                        found_on_state = True
                    else:
                        logger.warning('Irregular order at # ' +str(index) + ' ' + str(states[index]))
                        found_irregular_order=found_irregular_order+1
                    found_on=found_on+1
                    if states[index].endswith('WAIT'):
                        found_on_wait=found_on_wait+1
                elif states[index].startswith('OFF'):
                    found_off=found_off+1
                    if found_on_state:
                        found_on_state = False
                    else:
                        logger.warning('Irregular order at # ' +str(index) + ' ' + str(states[index]))
                        found_irregular_order=found_irregular_order+1
                    if states[index].endswith('WAIT'):
                        found_off_wait=found_off_wait+1
                else:
                    logger.warning('I can not recognize this state: ' + str(states[index]))
                    found_irregular=found_irregular+1
                index=index+1
        if count != (found_off + found_on + found_irregular):
            logger.error('Error during verify_schedule_data, number of states: ' + str(count) + ' differs from number of recognized states: ' + str(found_off + found_on + found_irregular))
        logger.debug('found_off: ' + str(found_off))
        logger.debug('found_on: ' + str(found_on))
        logger.debug('found_off_wait: ' + str(found_off_wait))
        logger.debug('found_on_wait: ' + str(found_on_wait))
        logger.debug('found_irregular: ' + str(found_irregular))
        logger.debug('script_duration: ' + str(script_duration))
        logger.debug('found_irregular_order : ' + str(found_irregular_order))
    except Exception as ex:
        logger.exception("Exception in verify_schedule_data")
    return count, script_duration, found_off, found_on, found_irregular, found_irregular_order, found_off_wait, found_on_wait, beginissue, endissue

def process_schedule_data(schedule_file_data):
    begin = None
    end = None
    states = []
    count=0
    res_shutdown_time_local = None
    res_shutdown_time_utc = None
    res_shutdown_str_time = None
    res_startup_time_local = None
    res_startup_time_utc = None
    res_startup_str_time = None

    try:

        if not 'begin' in schedule_file_data or schedule_file_data['begin'] is None:
            logger.critical('I can not find the begin time in the script...')
        elif not 'end' in schedule_file_data or schedule_file_data['end'] is None:
            logger.critical('I can not find the end time in the script...')
        elif not 'states' in schedule_file_data or len(schedule_file_data['states']) == 0:
            logger.critical('I can not find any state defined in the script.')
        else:
            begin = schedule_file_data['begin']
            end = schedule_file_data['end']
            states = schedule_file_data['states']
            count=len(states)
            logger.debug('Count: ' + str(count))
            logger.debug(str(states))
            cur_time = dt.datetime.now(local_tz)
            logger.debug('begin: ' + begin.strftime("%a %d %b %Y %H:%M:%S"))
            logger.debug('end: ' + end.strftime("%a %d %b %Y %H:%M:%S"))
            logger.debug('cur_time: ' + cur_time.strftime("%a %d %b %Y %H:%M:%S"))
            if cur_time < begin:
                logger.debug('The schedule script starts in future')
                cur_time=begin
            elif cur_time >= begin:
                logger.debug('The schedule script started in past')
            elif  cur_time >= end:
                logger.debug('The schedule script has ended already.')
            #else:
            interrupted=schedule_script_interrupted()
            if interrupted: # should be False if scheduled startup is in the future and shutdown is in the pass
                logger.debug('Schedule script is interrupted, revising the schedule...')
            index=0
            found_states=0
            check_time=begin
            script_duration=0
            found_off=0
            found_on=0
            while found_states != 2 and check_time < end:
                duration=extract_duration(states[index])
                #logger.debug('duration: ' + str(duration))
                check_time=check_time+dt.timedelta(seconds=duration)
                if found_off == 0 and states[index].startswith('OFF'):
                    found_off=1
                if found_on == 0 and states[index].startswith('ON'):
                    found_on=1
                #find the current ON state and incoming OFF state
                #logger.debug('check_time: ' + check_time.strftime("%a %d %b %Y %H:%M:%S"))
                #logger.debug('cur_time: ' + cur_time.strftime("%a %d %b %Y %H:%M:%S"))
                #logger.debug('check_time >= cur_time: ' + str(check_time >= cur_time) + ' found_states: ' + str(found_states == 1) + ' state starts with on: ' + str(states[index].startswith('ON')))
                #if check_time >= (cur_time) and (found_states == 1 or states[index].startswith('ON')):
                if check_time >= (cur_time+dt.timedelta(seconds=60)) and (found_states == 1 or states[index].startswith('ON')):
                    found_states=found_states+1
                    if states[index].startswith('ON'):
                        if states[index].endswith('WAIT'):
                            logger.debug('Skip scheduling next shutdown, which should be done externally.')
                        else:
                            if interrupted:
                                #if [ ! -z "$2" ] && [ $interrupted == 0 ] ; then
                                # schedule a shutdown 1 minute before next startup
                                temptime=check_time-dt.timedelta(seconds=duration)-dt.timedelta(seconds=60)
                                logger.debug('Scheduling next shutdown 1 minute before next startup at ' + temptime.strftime("%a %d %b %Y %H:%M:%S"))
                                res_shutdown_time_local = temptime
                                res_shutdown_time_utc = res_shutdown_time_local.replace(tzinfo=local_tz).astimezone(tz=utc_tz)
                                res_shutdown_str_time = datetime2stringtime(res_shutdown_time_utc)[:8]
                                """setup_on_state(temptime)"""
                            else:
                                logger.debug('Scheduling next shutdown at ' + check_time.strftime("%a %d %b %Y %H:%M:%S"))
                                res_shutdown_time_local = check_time
                                res_shutdown_time_utc = res_shutdown_time_local.replace(tzinfo=local_tz).astimezone(tz=utc_tz)
                                res_shutdown_str_time = datetime2stringtime(res_shutdown_time_utc)[:8]
                                """setup_on_state(check_time)"""
                    elif states[index].startswith('OFF'):
                        logger.debug('off state')
                        if states[index].endswith('WAIT'):
                            logger.debug('Skip scheduling next startup, which should be done externally.')
                        else:
                            if interrupted and index != 0:
                                # if [ ! -z "$2" ] && [ $interrupted == 0 ] && [ $index != 0 ] ; then
                                # jump back to previous OFF state
                                prev_state=states[(index-1)]
                                prev_duration=extract_duration(prev_state)
                                temptime=check_time-dt.timedelta(seconds=duration)-dt.timedelta(seconds=prev_duration)
                                logger.debug('Scheduling next startup 1 state before at ' + temptime.strftime("%a %d %b %Y %H:%M:%S"))
                                res_startup_time_local = temptime
                                res_startup_time_utc = res_startup_time_local.replace(tzinfo=local_tz).astimezone(tz=utc_tz)
                                res_startup_str_time = datetime2stringtime(res_startup_time_utc)
                                """setup_off_state(temptime)"""
                            else:
                                logger.debug('Scheduling next startup at ' + check_time.strftime("%a %d %b %Y %H:%M:%S"))
                                res_startup_time_local = check_time
                                res_startup_time_utc = res_startup_time_local.replace(tzinfo=local_tz).astimezone(tz=utc_tz)
                                res_startup_str_time = datetime2stringtime(res_startup_time_utc)
                                """setup_off_state(check_time)"""
                    else:
                        logger.warning('I can not recognize this state: ' + str(states[index]))
                index=index+1
                if index == count:
                    index=0
                    if script_duration == 0:
                        if found_off == 0:
                            logger.warning('I need at least one OFF state in the script.')
                            check_time=end     # skip all remaining cycles
                        elif found_on == 0:
                            logger.warning('I need at least one ON state in the script.')
                            check_time=end     # skip all remaining cycles
                        else:
                            script_duration=check_time-begin
                            skip=cur_time-check_time
                            skip=skip-skip%script_duration
                            check_time=check_time+skip
    except Exception as ex:
        logger.exception("Exception in process_schedule_data")
    return res_shutdown_time_utc, res_shutdown_time_local, res_shutdown_str_time, res_startup_time_utc, res_startup_time_local, res_startup_str_time


def getAll():
    wittypi = {}
    wittypi['is_rtc_connected'] = is_rtc_connected()
    if wittypi['is_rtc_connected']:
        wittypi['is_rtc_connected'] = True
        rtc_time_utc,rtc_time_local,rtc_timestamp = get_rtc_timestamp()
        wittypi['rtc_time_utc'] = rtc_time_utc
        wittypi['rtc_time_local'] = rtc_time_local
        wittypi['rtc_timestamp'] = rtc_timestamp
        wittypi['rtc_time_is_valid'] = rtc_time_is_valid(rtc_time_utc)
        startup_time_utc,startup_time_local,startup_str_time,startup_timedelta = get_startup_time()
        wittypi['startup_time_utc'] = startup_time_utc
        wittypi['startup_time_local'] = startup_time_local
        wittypi['startup_str_time'] = startup_str_time
        wittypi['startup_timedelta'] = startup_timedelta
        shutdown_time_utc,shutdown_time_local,shutdown_str_time,shutdown_timedelta = get_shutdown_time()
        wittypi['shutdown_time_utc'] = shutdown_time_utc
        wittypi['shutdown_time_local'] = shutdown_time_local
        wittypi['shutdown_str_time'] = shutdown_str_time
        wittypi['shutdown_timedelta'] = shutdown_timedelta
        wittypi['temperature'] = get_temperature()
        wittypi['alarm_flags'] = get_alarm_flags()
    wittypi['is_mc_connected'] = is_mc_connected()
    if wittypi['is_mc_connected']:
        wittypi['is_mc_connected'] = True
        wittypi['firmwareversion'] = get_firmwareversion()
        wittypi['input_voltage'] = get_input_voltage()
        wittypi['output_voltage'] = get_output_voltage()
        wittypi['outputcurrent'] = get_output_current()
        wittypi['default_state'] = get_default_state()
        wittypi['dummy_load_duration'] = get_dummy_load_duration()
        wittypi['power_cut_delay'] = get_power_cut_delay()
        wittypi['pulsing_interval'] = get_pulsing_interval()
        wittypi['white_led_duration'] = get_white_led_duration()
        wittypi['low_voltage_threshold'] = get_low_voltage_threshold()
        wittypi['recovery_voltage_threshold'] = get_recovery_voltage_threshold()
    wittypi['wittyPiPath'] = get_wittypi_folder()
    wittypi['is_schedule_file_in_use'] = is_schedule_file_in_use()
    if wittypi['is_schedule_file_in_use']:
        wittypi['schedule_file_data'] = schedule_file_lines2schedule_file_data(get_schedule_file())
    return wittypi


def main():
    try:
        logging.basicConfig(level=logging.INFO)
        wittypi = {}
        wittypi = getAll()
        print("================================================================================")
        print("|                                                                              |")
        print("|   Witty Pi - Realtime Clock + Power Management for Raspberry Pi              |")
        print("|                                                                              |")
        print("|               < Version " + str(__version__) + " >     by elschnorro77                          |")
        print("|                                                                              |")
        print("================================================================================")
        if wittypi['is_rtc_connected']:
            print(">>> Current temperature: " + str(wittypi['temperature']) + "°C / " + str(int(wittypi['temperature']) * 1.8 + 32) + " °F")
            print(">>> Your system time is:       " + str(dt.datetime.now(local_tz).strftime("%a %d %b %Y %H:%M:%S")) + " " +  str(local_tz))
            if wittypi['rtc_time_local'] is not None:
                print(">>> Your RTC time is:          " + str(wittypi['rtc_time_local'].strftime("%a %d %b %Y %H:%M:%S")) + " " + str(local_tz))
                if not wittypi['rtc_time_is_valid']:
                    print(">>> Your RTC time has not been set before (stays in year 1999/2000).")
            if wittypi['shutdown_time_local'] is not None:
                str_shutdown_time_local = str(wittypi['shutdown_time_local'].strftime("%a %d %b %Y %H:%M:%S")) + " " +  str(local_tz)
            else:
                str_shutdown_time_local = "Never"
            print(">>> Schedule next shutdown at: " + str_shutdown_time_local)
            if wittypi['startup_time_local'] is not None:
                str_startup_time_local = str(wittypi['startup_time_local'].strftime("%a %d %b %Y %H:%M:%S")) + " " +  str(local_tz)
            else:
                str_startup_time_local = "Never"
            print(">>> Schedule next startup at:  " + str_startup_time_local)
            print(">>> RTC Alarm flags: " +  format(wittypi['alarm_flags'], '0>8b'))
        else:
            print("no WittyPi RTC is connected")
        if wittypi['is_mc_connected']:
            print(">>> Vout=" + str(wittypi['output_voltage']) + "V, Iout=" + str(wittypi['outputcurrent']) + "A")
            print(">>> Vin= " + str(wittypi['input_voltage']) + "V")
            print(">>> low voltage threshold= " + str(wittypi['low_voltage_threshold']))
            print(">>> recovery voltage threshold= " + str(wittypi['recovery_voltage_threshold']))

            print(">>> Firmware version: " + str(wittypi['firmwareversion']))
            if  wittypi['default_state'] == 0:
                print(">>> Default state when powered [OFF]")
            if  wittypi['default_state'] == 1:
                print(">>> Default state when powered [ON]")
            print(">>> Power cut delay after shutdown. " + str(wittypi['power_cut_delay']) + "seconds")
            print(">>> Pulsing interval during sleep " + str(wittypi['pulsing_interval']) + "seconds")
            print(">>> White LED duration " + str(wittypi['white_led_duration']) + "ms")
            print(">>> Dummy load duration " + str(wittypi['dummy_load_duration']) + "ms")
            if is_schedule_file_in_use():
                print(">>> schedule script " + str(wittypi['wittyPiPath']) + "/schedule.wpi is in use")
            else:
                print(">>> schedule script is not in use")
        else:
            print("no WittyPi MC is connected")
    except Exception as ex:
        logger.critical("Unhandled Exception in main: " + repr(ex))

if __name__ == '__main__':
    try:
        main()

    except (KeyboardInterrupt, SystemExit):
        close_script()

    except Exception as ex:
        logger.error("Unhandled Exception in __main__ " + repr(ex))
