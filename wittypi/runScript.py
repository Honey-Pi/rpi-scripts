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
#from logging.handlers import RotatingFileHandler
logger = logging.getLogger('WittyPi.runScript')


from .wittyPi import local_tz, is_rtc_connected, wittyPiPath, is_schedule_file_in_use, schedule_file_lines2schedule_file_data, get_schedule_file, process_schedule_data, stringtime2timetuple, calcTime, set_shutdown_time, clear_shutdown_time, set_startup_time, clear_startup_time
import datetime as dt

def runscript():
    try:
        logging.basicConfig(level=logging.INFO)
        print("--------------- " + dt.datetime.now(local_tz).strftime("%a %d %b %Y %H:%M:%S") + "---------------")
        if is_rtc_connected:
            if is_schedule_file_in_use():
                print('schedule script "' + wittyPiPath + '/schedule.wpi"')
                logger.debug('Processing WittyPi schedule script "' + wittyPiPath + '/schedule.wpi"')
                schedule_file_data = schedule_file_lines2schedule_file_data(get_schedule_file())
                shutdown_time_utc, shutdown_time_local, shutdown_str_time, startup_time_utc, startup_time_local, startup_str_time = process_schedule_data(schedule_file_data)
                if shutdown_time_local is not None:
                    str_shutdown_time_local = shutdown_time_local.strftime("%a %d %b %Y %H:%M:%S") + " " +  str(local_tz)
                    set_shutdown_time(shutdown_str_time)
                    shutdown_test = stringtime2timetuple(shutdown_str_time)
                    test_shutdown_time_utc, test_shutdown_time_local, test_shutdown_str_time, test_shutdown_timedelta = calcTime(shutdown_test)
                    if test_shutdown_time_utc != shutdown_time_utc:
                        print('Real shutdown will occur : ' + test_shutdown_time_local.strftime("%a %d %b %Y %H:%M:%S") + " " +  str(local_tz))
                        logger.debug('Real shutdown will occur : ' + test_shutdown_time_local.strftime("%a %d %b %Y %H:%M:%S") + " " +  str(local_tz))
                else: 
                    str_shutdown_time_local = "Never"
                    clear_shutdown_time()
                print("Schedule next shutdown at: " + str_shutdown_time_local)
                logger.debug("Schedule next shutdown at: " + str_shutdown_time_local)
                if startup_time_local is not None: 
                    str_startup_time_local = startup_time_local.strftime("%a %d %b %Y %H:%M:%S") + " " +  str(local_tz)
                    set_startup_time(startup_str_time)
                    startup_test = stringtime2timetuple(startup_str_time)
                    test_startup_time_utc, test_startup_time_local, test_startup_str_time, test_startup_timedelta = calcTime(startup_test)
                    if test_startup_time_utc != startup_time_utc:
                        print('Real startup will occur :  ' + test_startup_time_local.strftime("%a %d %b %Y %H:%M:%S") + " " +  str(local_tz))
                        logger.debug('Real startup will occur :  ' + test_startup_time_local.strftime("%a %d %b %Y %H:%M:%S") + " " +  str(local_tz))
                else: 
                    str_startup_time_local = "Never"
                    clear_startup_time()
                print("Schedule next startup at:  " + str_startup_time_local)
                logger.debug("Schedule next startup at:  " + str_startup_time_local)
            else:
                print('File "' + wittyPiPath + '/schedule.wpi" not found, skip running schedule script.')
                logger.debug('File "' + wittyPiPath + '/schedule.wpi" not found, skip running schedule script.')
        else:
            print("no WittyPi RTC is connected")
            logger.debug("no WittyPi RTC is connected")
        print("-------------------------------------------------------")
    except Exception as ex:
        logger.critical("Unhandled Exception in runscript: " + repr(ex))

if __name__ == '__main__':
    try:
        runscript()

    except (KeyboardInterrupt, SystemExit):
        close_script()

    except Exception as ex:
        logger.error("Unhandled Exception in __main__ " + repr(ex))