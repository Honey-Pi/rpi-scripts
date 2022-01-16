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

local_tz = dt.datetime.utcnow().astimezone().tzinfo
#local_tz = pytz.timezone('Europe/Stockholm')
utc_tz = pytz.timezone('UTC')

from smbus2 import SMBus


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

HALT_PIN=4    # halt by GPIO-4 (BCM naming)
SYSUP_PIN=17  # output SYS_UP signal on GPIO-17 (BCM naming)


def dec2hex(datalist):
    try:
        res = []
        for v in datalist:
            hexInt = 10*(v//16) + (v%16)
            res.append(hexInt)
        return res
    except Exception as ex:
        logger.exception("Exception in dec2hex " + str(ex))

def dec2bcd(dec):
    try:
        #result= $((10#$1/10*16+(10#$1%10)))
        t = int(dec) // 10;
        o = int(dec) - t * 10;
        result = (t << 4) + o;
        return result
    except Exception as ex:
        logger.exception("Exception in dec2bcd " + str(ex))

def is_rtc_connected():
    try:
        out=[]
        with SMBus(1) as bus:
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
                    b = bus.read_byte(RTC_ADDRESS)
                    out.append(b)
                logger.debug("RTC is connected")
                return True
            except IOError as ex:
                if str(ex) == "[Errno 121] Remote I/O error":
                    logger.debug("RTC is not connected")
                    return False
        else:
            logger.exception("IOError in is_rtc_connected " + str(ex))
    except Exception as ex:
        logger.exception("Exception in is_rtc_connected " + str(ex))

def is_mc_connected():
    try:
        out=[]
        with SMBus(1) as bus:
            b = bus.read_byte(I2C_MC_ADDRESS)
            out.append(b)
        logger.debug("MC is connected")
        return True
    except IOError as ex:
        if str(ex) == "[Errno 121] Remote I/O error":
            logger.debug("MC is not connected")
            return False
    except Exception as ex:
        logger.exception("Exception in is_mc_connected" + str(ex))


rtc_connected = is_rtc_connected()
mc_connected = is_mc_connected()


def get_firmwareversion():
    firmwareversion = 0
    try:
        out=[]
        if mc_connected:
            with SMBus(1) as bus:
                b = bus.read_byte_data(I2C_MC_ADDRESS, I2C_ID)
                out.append(b)
            firmwareversion =  dec2hex(out)[0]
        logger.debug("MC firmwareversion: "+ str(firmwareversion))
    except Exception as ex:
        logger.exception("Exception in get_firmwareversion"  + str(ex))
    return firmwareversion


def get_rtc_timestamp(): 
    out=[]
    UTCtime,localtime,timestamp = None, None, None
    try:
        if rtc_connected:
            with SMBus(1) as bus:
                data = [0, 1, 2, 3, 4, 5, 6]
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
        logger.exception("Exception in get_rtc_timestamp" + str(ex))
    return UTCtime,localtime,timestamp



def get_input_voltage():
    res = 0
    try:
        if mc_connected:
            with SMBus(1) as bus:
                i = bus.read_byte_data(I2C_MC_ADDRESS, I2C_VOLTAGE_IN_I)
                d = bus.read_byte_data(I2C_MC_ADDRESS, I2C_VOLTAGE_IN_D)
            res = i + float(d)/100.
    except Exception as ex:
        logger.exception("Exception in get_input_voltage" + str(ex))
    return res

def get_startup_time(): # [?? 07:00:00], ignore: [?? ??:??:00] and [?? ??:??:??]
    res = []
    try:
        if rtc_connected:
            out = []
            with SMBus(1) as bus:
                for ele in [7,8,9,10]:
                    b = bus.read_byte_data(RTC_ADDRESS, ele)
                    out.append(b)
            res = dec2hex(out) # sec, min, hour, day
    except Exception as ex:
        logger.exception("Exception in get_startup_time" + str(ex))
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
        logger.exception("Exception in add_one_month" + str(ex))
    return new_date

def calcTime(res=[0, 0, 0]):
    """calculate startup/shutdown time from wittypi output"""
    time_local = None
    timedelta = None
    str_time = None
    try:
        nowUTC = dt.datetime.now(utc_tz)
        nowLOCAL = dt.datetime.now(local_tz)
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
            strtime = [] # [0, 20, 80]
            for ele in res:
                if ele == 80: strtime.append('??')
                else: strtime.append(str(ele))
            if len(strtime) == 4: str_time = strtime[-1] + ' ' + strtime[-2] + ':' + strtime[-3] + ':' + strtime[-4]
            else: str_time = strtime[-1] + ' ' + strtime[-2] + ':' + strtime[-3] + ':00' 
            timedelta = time_local - nowLOCAL
    except Exception as ex:
        logger.exception("Exception in calcTime" + str(ex))
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
                for ele in [11,12,13]:
                    b = bus.read_byte_data(RTC_ADDRESS, ele)
                    out.append(b)
            res = dec2hex(out) # sec, min, hour, day
    except Exception as ex:
        logger.exception("Exception in get_shutdown_time" + str(ex))
    return calcTime(res)

def stringtime2timetuple(stringtime='?? 20:00:00'):
    logger.debug(str(stringtime))
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
        return (day,hour,minute,second)
    else: 
        logger.debug('day: ' + str(day) + ' hour: ' + str(hour) + 'minute: ' + str(minute))
        return (day,hour,minute)

def system_to_rtc():
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
                bus.write_byte_data(RTC_ADDRESS, 0x00, dec2bcd(second))
                bus.write_byte_data(RTC_ADDRESS, 0x01, dec2bcd(minute))
                bus.write_byte_data(RTC_ADDRESS, 0x02, dec2bcd(hour))
                bus.write_byte_data(RTC_ADDRESS, 0x03, dec2bcd(day))
                bus.write_byte_data(RTC_ADDRESS, 0x04, dec2bcd(date))
                bus.write_byte_data(RTC_ADDRESS, 0x05, dec2bcd(month))
                bus.write_byte_data(RTC_ADDRESS, 0x06, dec2bcd(year))
            return True
    except Exception as ex:
        logger.exception("Exception in system_to_rtc" + str(ex))
    return False

def set_shutdown_time(stringtime='?? 20:00'):
    try:
        if rtc_connected:
            day,hour,minute = stringtime2timetuple(stringtime)
            if (day is not None ) and (hour is not None) and (minute is not None):
                with SMBus(1) as bus:
                    bus.write_byte_data(RTC_ADDRESS, 14,7) # write_byte_data(i2c_addr, register, value, force=None)
                    bus.write_byte_data(RTC_ADDRESS, 11,dec2bcd(minute)) 
                    bus.write_byte_data(RTC_ADDRESS, 12,dec2bcd(hour)) 
                    bus.write_byte_data(RTC_ADDRESS, 13,dec2bcd(day)) 
                return True
            else:
                logger.debug("invalid Time")
    except Exception as ex:
        logger.exception("Exception in set_shutdown_time" + str(ex))
    return False

def set_startup_time(stringtime='?? 20:00:00'):
    try:
        if rtc_connected:
            day,hour,minute,second = stringtime2timetuple(stringtime)
            if (day is not None ) and (hour is not None) and (minute is not None) and (second is not None):
                with SMBus(1) as bus:
                    bus.write_byte_data(RTC_ADDRESS, 14,7) # write_byte_data(i2c_addr, register, value, force=None)
                    bus.write_byte_data(RTC_ADDRESS, 7,dec2bcd(second)) 
                    bus.write_byte_data(RTC_ADDRESS, 8,dec2bcd(minute)) 
                    bus.write_byte_data(RTC_ADDRESS, 9,dec2bcd(hour)) 
                    bus.write_byte_data(RTC_ADDRESS, 10,dec2bcd(day)) 
                return True
            else:
                logger.debug("invalid Time")
    except Exception as e:
        print(e)
        return False

def clear_startup_time():
    try:
        if rtc_connected:
            with SMBus(1) as bus:
                bus.write_byte_data(RTC_ADDRESS, 7,0) # write_byte_data(i2c_addr, register, value, force=None)
                bus.write_byte_data(RTC_ADDRESS, 8,0) # write_byte_data(i2c_addr, register, value, force=None)
                bus.write_byte_data(RTC_ADDRESS, 9,0) # write_byte_data(i2c_addr, register, value, force=None)
                bus.write_byte_data(RTC_ADDRESS, 10,0) # write_byte_data(i2c_addr, register, value, force=None)
            return True
    except Exception as ex:
        logger.exception("Exception in clear_startup_time" + str(ex))
    return False

def clear_shutdown_time():
    try:
        if rtc_connected:
            with SMBus(1) as bus:
                bus.write_byte_data(RTC_ADDRESS, 11,0) # write_byte_data(i2c_addr, register, value, force=None)
                bus.write_byte_data(RTC_ADDRESS, 12,0) # write_byte_data(i2c_addr, register, value, force=None)
                bus.write_byte_data(RTC_ADDRESS, 13,0) # write_byte_data(i2c_addr, register, value, force=None)
            return True
    except Exception as ex:
        logger.exception("Exception in clear_shutdown_time" + str(ex))
    return False

def get_power_mode():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                b = bus.read_byte_data(I2C_MC_ADDRESS, I2C_POWER_MODE)
            return b # int 0 or 1
    except Exception as ex:
        logger.exception("Exception in get_power_mode" + str(ex))

def get_output_voltage():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                i = bus.read_byte_data(I2C_MC_ADDRESS, I2C_VOLTAGE_OUT_I)
                d = bus.read_byte_data(I2C_MC_ADDRESS, I2C_VOLTAGE_OUT_D)
            return float(i) + float(d)/100.
    except Exception as ex:
        logger.exception("Exception in get_output_voltage" + str(ex))

def get_output_current():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                i = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CURRENT_OUT_I)
                d = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CURRENT_OUT_D)
            return float(i) + float(d)/100.
    except Exception as ex:
        logger.exception("Exception in get_output_current" + str(ex))

def get_low_voltage_threshold():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                i = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CONF_LOW_VOLTAGE)
            if i == 255: thresh = 'disabled'
            else: thresh = float(i)/10.
            return thresh
    except Exception as ex:
        logger.exception("Exception in get_low_voltage_threshold" + str(ex))

def get_recovery_voltage_threshold():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                i = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CONF_RECOVERY_VOLTAGE)
            if i == 255: thresh = 'disabled'
            else: thresh = float(i)/10.
            return thresh
    except Exception as ex:
        logger.exception("Exception in get_recovery_voltage_threshold" + str(ex))

def set_low_voltage_threshold(volt='11.5'): 
    try:
        if mc_connected:
            if len(volt) == 4:
                volt = int(float(volt) * 10.)
                if not (50 < volt < 254): volt = 255 # clear threshold if threshold is not between 5V and 25.4V
                else: print(' setting threshold to ',volt)
                try:
                    with SMBus(1) as bus:
                        bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_LOW_VOLTAGE,volt) 
                    return True
                except Exception as e:
                    print(e)
                    return False
                else:
                    print('wrong input for voltage threshold',volt)
                    return False
    except Exception as ex:
        logger.exception("Exception in set_low_voltage_threshold" + str(ex))

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
                        bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_RECOVERY_VOLTAGE,volt) 
                    return True
            else:
                logger.error('wrong input for voltage threshold ' + str(volt))
    except Exception as ex:
        logger.exception("Exception in set_low_voltage_threshold " + str(ex))
    return False

def clear_low_voltage_threshold():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_LOW_VOLTAGE, 0xFF)
            return True
    except Exception as ex:
        logger.exception("Exception in clear_low_voltage_threshold " + str(ex))
    return False

def clear_recovery_voltage_threshold():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_RECOVERY_VOLTAGE, 0xFF)
            return True
    except Exception as ex:
        logger.exception("Exception in clear_recovery_voltage_threshold " + str(ex))
    return False

def get_temperature():
    try:
        if rtc_connected:
            with SMBus(1) as bus:
                ctrl = bus.read_byte_data(RTC_ADDRESS, 14)
                ctrl2 = 7|0x20 #39 bitwise or
                bus.write_byte_data(RTC_ADDRESS, 14,ctrl2) 
                time.sleep(0.2)
                t1 = bus.read_byte_data(RTC_ADDRESS, 0x11)
                t2 = bus.read_byte_data(RTC_ADDRESS, 0x12)
                c = ''
                sign = t1&0x80
                if sign < 0: c+='-'
                else: c += str(t1&0x7F)
                c+='.'
                c += str(((t2&0xC0)>>6)*25 )
            return float(c)
    except Exception as ex:
        logger.exception("Exception in get_temperature" + str(ex))

def clear_alarm_flags():
    try:
        if rtc_connected:
            byte_F=0x0
            """{
            if [ -z "$1" ]:
            with SMBus(1) as bus:
                byte_F=bus.read_byte_data(I2C_RTC_ADDRESS 0x0F)
            else:
                byte_F=$1
            byte_F=$(($byte_F&0xFC))
            """
            with SMBus(1) as bus:
                bus.write_byte_data(I2C_RTC_ADDRESS, 0x0F, byte_F)
    except Exception as ex:
        logger.exception("Exception in get_temperature" + str(ex))

def get_power_cut_delay():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                pcd = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CONF_POWER_CUT_DELAY)
            pcd=pcd/10
            return pcd
    except Exception as ex:
        logger.exception("Exception in get_power_cut_delay" + str(ex))

def set_power_cut_delay(delay=8):
    try:
        if mc_connected:
            maxVal=8.0;
            if get_firmwareversion() >= 35:
                maxVal='25.0'
            if delay >= 0 and delay <= maxVal:
                d=delay*10
                with SMBus(1) as bus:
                    bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_POWER_CUT_DELAY, d)
                logger.debug("Power cut delay set to ", delay , " seconds!")
                return True
            else:
                logger.error('wrong input for power cut delay threshold ' + str(delay) + 'Please input from 0.0 to ' + str(maxVal) + ' ...')
    except Exception as ex:
        logger.exception("Exception in set_power_cut_delay" + str(ex))
    return False

def get_dummy_load_duration():
    try:
        if mc_connected:
            with SMBus(1) as bus:
                dummy_load_duration = bus.read_byte_data(I2C_MC_ADDRESS, I2C_CONF_DUMMY_LOAD)
            return dummy_load_duration #[0]
    except Exception as ex:
        logger.exception("Exception in get_dummy_load_duration")

def set_dummy_load_duration(duration=0):
    try:
        if mc_connected:
            if duration >=- 0 and duration <= 254:
                with SMBus(1) as bus:
                    bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_DUMMY_LOAD, duration)
                logger.debug("Dummy load duration set to " + str(duration) + " !")
                return True
            else:
                logger.error('wrong input for dummy load duration ' + str(duration) + ' Please input from 0 to 254')
    except Exception as ex:
        logger.exception("Exception in set_dummy_load_duration" + str(ex))
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
                    bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_PULSE_INTERVAL, pi)
                logger.debug("Pulsing interval set to " + str(interval) + "seconds")
                return True
    except Exception as ex:
        logger.exception("Exception in set_pulsing_interval" + str(ex))
    return False

def get_pulsing_interval():
    try:
        if mc_connected:
            interval = None
            with SMBus(1) as bus:
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
        logger.exception("Exception in get_pulsing_interval" + str(ex))

def set_white_led_duration(duration):
    try:
        if mc_connected:
            if duration >=- 0 and duration <= 254:
                    with SMBus(1) as bus:
                        bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_BLINK_LED, duration)
                        print("White LED duration set to ", duration, " !")
            else:
                logger.error('wrong input for white LED duration ' + str(duration) + ' Please input from 0 to 254')
    except Exception as ex:
        logger.exception("Exception in set_white_led_duration" + str(ex))
    return False

def get_white_led_duration():
    try:
        if mc_connected:
            with SMBus(1) as bus:
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
                    bus.write_byte_data(I2C_MC_ADDRESS, I2C_CONF_DEFAULT_ON, hexstate)
                if hexstate == 0x01:
                    logger.debug('Default state when powered set to "ON"!')
                elif hexstate == 0x00:
                    logger.debug('Default state when powered set to "OFF"!')
                return True
            else:
                logger.error('wrong input for default state. Please use 1 for "Default ON" or 0 for "Default OFF"')
    except Exception as ex:
        logger.exception("Exception in get_white_led_duration" + str(ex))
    return False

def get_default_state(): #1=ON, 0=OFF
    try:
        if mc_connected:
            with SMBus(1) as bus:
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
        logger.exception("Exception in get_default_state")    

def getAll():
    wittypi = {}
    if is_rtc_connected():
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
    else:
        wittypi['is_rtc_connected'] = False
    if is_mc_connected():
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
    else:
        wittypi['is_mc_connected'] = False
    return wittypi
    

def main():
    try:
        logging.basicConfig(level=logging.DEBUG)
        wittypi = {}
        clear_shutdown_time()
        clear_startup_time()
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
        else:
            print("no WittyPi RTC is connected")
        if wittypi['is_mc_connected']:
            print(">>> Vout=" + str(wittypi['output_voltage']) + "V, Iout=" + str(wittypi['outputcurrent']) + "A")
            print(">>> Vin= " + str(wittypi['input_voltage']) + "V")
            print(">>> Firmware version: " + str(wittypi['firmwareversion']))
            if  wittypi['default_state'] == 0:
                print(">>> Default state when powered [OFF]")
            if  wittypi['default_state'] == 1:
                print(">>> Default state when powered [ON]")
            print(">>> Power cut delay after shutdown. " + str(wittypi['power_cut_delay']) + "seconds")
            print(">>> Pulsing interval during sleep " + str(wittypi['pulsing_interval']) + "seconds")
            print(">>> White LED duration " + str(wittypi['white_led_duration']) + "ms")
            print(">>> Dummy load duration " + str(wittypi['dummy_load_duration']) + "ms")
        else:
            print("no WittyPi MC is connected")
        #set_startup_time('?? ??:??:??')
        #set_shutdown_time('?? 21:00')
    except Exception as ex:
        logger.critical("Unhandled Exception in main: " + repr(ex))

if __name__ == '__main__':
    try:
        main()

    except (KeyboardInterrupt, SystemExit):
        close_script()

    except Exception as ex:
        logger.error("Unhandled Exception in __main__ " + repr(ex))