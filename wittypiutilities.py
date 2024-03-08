#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import subprocess
import shutil
import os
import pwd
import grp
import logging
from datetime import datetime
import sys
import argparse

logger = logging.getLogger('HoneyPi.wittypiutilities')

from wittypi import clear_startup_time, clear_shutdown_time, getAll, schedule_file_lines2schedule_file_data, verify_schedule_data, runscript, system_to_rtc, rtc_to_system, set_power_cut_delay, set_dummy_load_duration, set_default_state, set_pulsing_interval, set_white_led_duration, send_sysup, check_alarm_flags, clear_alarm_flags, do_shutdown, add_halt_pin_event
#from wittypi.runScript import runscript
from utilities import is_service_active, get_abs_timedifference, getStateFromStorage
from constant import homeFolder, backendFolder, wittypi_scheduleFileName, wittypi_scheduleFile, local_tz

def get_wittyPiPath():
    wittyPiPath = ''
    try:
        if os.path.exists(homeFolder + '/wittyPi'):
            wittyPiPath = homeFolder + '/wittyPi'
            logger.debug("WittyPi 2 or WittyPi Mini installation (or at least an schedule.wpi file) detected in: " + wittyPiPath)
        elif os.path.exists(homeFolder + '/wittypi'):
            wittyPiPath = homeFolder + '/wittypi'
            logger.debug("WittyPi 3 (Mini) or Witty Pi 4 (Mini) installation (or at least an schedule.wpi file) detected in: " + wittyPiPath)
    except Exception as ex:
        logger.exception("Error in function get_wittyPiPath")
    return wittyPiPath

def remove_wittypi_internet_timesync():
    already_done = False
    try:
        wittyPiPath = get_wittyPiPath()
        if os.path.isfile(wittyPiPath + "/syncTime.sh"):
            fp = open(wittyPiPath + "/syncTime.sh")
            for i, line in enumerate(fp):
                if i == 39 and line.strip().startswith("#"):
                    already_done = True
            if not already_done:
                os.system("sudo sed -i '40s/net_to_system/# net_to_system/' " + wittyPiPath + "/syncTime.sh")
                os.system("sudo sed -i '41s/system_to_rtc/# system_to_rtc/' " + wittyPiPath + "/syncTime.sh")
    except Exception as ex:
        logger.exception("Error in function remove_wittypi_internet_timesync")

def add_wittypi_internet_timesync():
    already_done = False
    try:
        wittyPiPath = get_wittyPiPath()
        if os.path.isfile(wittyPiPath + "/syncTime.sh"):
            fp = open(wittyPiPath + "/syncTime.sh")
            for i, line in enumerate(fp):
                if i == 39 and line.strip().startswith("net_to_system"):
                    already_done = True
            if not already_done:
                os.system("sudo sed -i '40s/# net_to_system/net_to_system/' " + wittyPiPath + "/syncTime.sh")
                os.system("sudo sed -i '41s/# system_to_rtc/system_to_rtc/' " + wittyPiPath + "/syncTime.sh")
    except Exception as ex:
        logger.exception("Error in function add_wittypi_internet_timesync")

def set_wittypi_rtc(settings, wittypi_status):
    try:
        if wittypi_status['is_rtc_connected']:
            timenow = datetime.now(local_tz)
            if system_to_rtc():
                logger.critical("Set RTC time to "+ timenow.strftime("%a %d %b %Y %H:%M:%S"))
            else:
                logger.critical("Failed to set RTC time")
    except:
        logger.exception("Error in function set_wittypi_rtc")

def log_verify_schedule_data(schedulename, settings, count, script_duration, found_off, found_on, found_irregular, found_irregular_order, found_off_wait, found_on_wait, beginissue, endissue):
    try:
        if beginissue != "":
            logger.critical(schedulename + ": " + beginissue)
        if endissue != "":
            logger.critical(schedulename + ": " + endissue)
        if found_off_wait > 0:
            logger.critical(schedulename + ": Found " + str(found_off_wait) + " times a 'WAIT' in an 'OFF' line, this will shutdown the HoneyPi without a scheduled start!")
        if found_irregular_order > 0:
            logger.critical(schedulename + ": Found " + str(found_irregular_order) + " lines in irregular oder, each schedule should start with 'ON' followed by 'OFF'!")
        if found_irregular > 0:
            logger.critical(schedulename + ": Found " + str(found_irregular) + " lines which could not be recognized!")
        if found_on_wait > 0 and found_on_wait != found_on:
            logger.critical(schedulename + ": Found " + str(found_on_wait) + " times a 'WAIT' in an 'ON' line, but there are ! " + str(found_on) + " 'ON' lines")
        if found_on == 0:
            logger.critical(schedulename + ": Found no 'ON' line ")
        if settings['wittyPi'][schedulename]['shutdownAfterTransfer'] and found_on_wait == 0:
            logger.critical(schedulename + ": Found no 'WAIT' in the 'ON' line, but shutdown after transfer' is enabled, you should add a 'WAIT' at the End of the 'ON' line")
    except Exception as ex:
        logger.exception("Error in function log_verify_schedule_data")

def check_wittypi_schedule(settings, wittypi_status):
    try:
        for schedule in ['normal', 'low']:
            if schedule in settings['wittyPi']:
                if settings['wittyPi'][schedule]['enabled']:
                    schedule_file_data = schedule_file_lines2schedule_file_data(settings['wittyPi'][schedule]['schedule'].split('\n'))
                    count, script_duration, found_off, found_on, found_irregular, found_irregular_order, found_off_wait, found_on_wait, beginissue, endissue = verify_schedule_data(schedule_file_data)
                    log_verify_schedule_data(schedule, settings, count, script_duration, found_off, found_on, found_irregular, found_irregular_order, found_off_wait, found_on_wait, beginissue, endissue)
                    #count, script_duration, found_off, found_on, found_irregular, found_irregular_order, found_off_wait, found_on_wait
                    isLowVoltage = getStateFromStorage('isLowVoltage', None)

                    if isLowVoltage is not None:
                        if schedule_file_data != wittypi_status['schedule_file_data']:
                            if isLowVoltage and schedule=="low":
                                logger.critical("WittyPi schedule file on filesystem is differnet from settings for power saving mode!")
                            elif not isLowVoltage and schedule=="normal":
                                logger.critical("WittyPi schedule file on filesystem is differnet from settings for normal mode!")
                    if settings['wittyPi'][schedule]['interval']!=1:
                        if schedule == 'normal':
                                logger.warning("WittyPi schedule is enabled in normal mode but Interval is not set to 'single measurement'!")
                        elif schedule == 'low' and settings['wittyPi']['voltagecheck_enabled']:
                                logger.warning("WittyPi schedule is enabled in power saving mode but Interval is not set to 'single measurement'!")
                    else:
                        if not settings['wittyPi'][schedule]['shutdownAfterTransfer']:
                            if schedule == 'normal':
                                logger.warning("WittyPi schedule is enabled in normal mode, Interval is set to 'single measurement' but 'shutdown after transfer' is not enabled!")
                            elif schedule == 'low' and settings['wittyPi']['voltagecheck_enabled']:
                                logger.warning("WittyPi schedule is enabled in power saving mode, Interval is set to 'single measurement' but 'shutdown after transfer' is not enabled!")
                else:
                    if settings['wittyPi'][schedule]['interval']==1:
                        if schedule == 'normal':
                            logger.critical("WittyPi schedule is not enabled in normal mode but Interval is set to 'single measurement'!")
                            if settings['wittyPi'][schedule]['shutdownAfterTransfer']:
                                logger.critical("WittyPi schedule is not enabled in normal mode but 'shutdown after transfer' is enabled!")
                        elif schedule == 'low' and settings['wittyPi']['voltagecheck_enabled']:
                            logger.critical("WittyPi schedule is not enabled in power saving mode but Interval is set to 'single measurement'!")
                            if settings['wittyPi'][schedule]['shutdownAfterTransfer']:
                                logger.critical("WittyPi schedule is not enabled in power saving mode but 'shutdown after transfer' is enabled!")

    except Exception as ex:
        logger.exception("Error in function check_wittypi_schedule")

def check_wittypi_rtc(settings, wittypi_status):
    try:
        if wittypi_status['is_rtc_connected']:
            if not wittypi_status['rtc_time_is_valid']:
                if wittypi_status['rtc_time_local']:
                    logger.critical("RTC time (" + wittypi_status['rtc_time_local'].strftime("%a %d %b %Y %H:%M:%S") +") has not been set before (stays in year 1999/2000).")
                else:
                    logger.critical("Not able to read RTC time")
            else:
                timenow = datetime.now(local_tz)
                abs_timedelta_totalseconds = round(get_abs_timedifference(timenow, wittypi_status['rtc_time_local']))
                if abs_timedelta_totalseconds >= 300:
                    logger.critical("Difference between RTC time and sytstem time is " + str(abs_timedelta_totalseconds) + " seconds")
                    wittypi_status['time_out_of_snyc'] = True
                elif abs_timedelta_totalseconds >= 60:
                    logger.warning("Difference between RTC time and sytstem time is " + str(abs_timedelta_totalseconds) + " seconds")
                    wittypi_status['time_out_of_snyc'] = False
                else:
                    logger.debug("Difference between RTC time and sytstem time is " + str(abs_timedelta_totalseconds) + " seconds")
                    wittypi_status['time_out_of_snyc'] = False
            if wittypi_status['startup_time_local'] is not None:
                logger.debug("HoneyPi next scheduled wakeup is: "+ wittypi_status['startup_time_local'].strftime("%a %d %b %Y %H:%M:%S"))
            if wittypi_status['shutdown_time_local'] is not None:
                logger.debug("HoneyPi next scheduled shutdown is: "+ wittypi_status['shutdown_time_local'].strftime("%a %d %b %Y %H:%M:%S"))
            return wittypi_status
    except Exception as ex:
        logger.exception("Error in function check_wittypi_rtc")


def check_wittypi(settings):
    wittypi_status = {}
    try:
        wittypi_status = get_wittypi_status(settings)
        wittypi_status['service_active']=is_service_active('wittypi.service')
        if wittypi_status['is_rtc_connected'] and not wittypi_status['service_active']:
            if wittypi_status['is_mc_connected']:
                logger.debug("WittyPi 3 is connected and WittyPi Service is not running!")
            else:
                logger.debug("WittyPi 2 (or other RTC) and WittyPi Service is not running!")
            #send sys_up signal to WittyPi on SYSUP (GPIO 17)
            send_sysup()
            #check alarmflags and clear
            if wittypi_status['alarm_flags'] is not None:
                logger.debug("WittyPi (or other RTC) alarm flags '" + format(wittypi_status['alarm_flags'], '0>8b') + "'")
                #ToDo handle alarm flags
                alarm_type = check_alarm_flags(wittypi_status['alarm_flags'])
                if alarm_type == 1:
                    if wittypi_status['startup_time_local'] is not None:
                        logger.debug("HoneyPi was woken up by Startup Alarm : " + wittypi_status['startup_time_local'].strftime("%a %d %b %Y %H:%M:%S"))
                    else:
                        logger.info("HoneyPi was woken up by Startup Alarm from RTC!")
                    logger.debug("Clearing WittyPi (or other RTC) alarm flags!")
                    clear_alarm_flags()
                elif alarm_type == 2:
                    logger.warning("HoneyPi was woken up by Shutdown Alarm from RTC, should go to sleep!")
                    do_shutdown()
            #create WittyPi folder if not existing to be able to save schedule file.
            if wittypi_status['wittyPiPath'] == "" or wittypi_status['wittyPiPath'] is None:
                path = homeFolder + '/wittypi'
                try:
                    os.mkdir(path)
                    os.system('sudo chown pi ' + path)
                    os.system('sudo chgrp pi ' + path)
                    os.system('sudo chmod ug+w ' + path)
                    logger.info("Created directory for WittyPi schedule file '%s'" % path)
                except OSError:
                    logger.critical("Creation of the directory for WittyPi schedule file '%s' failed" % path)
        if wittypi_status['service_active'] and wittypi_status['service_active'] != settings['wittyPi']['enabled']:
            logger.critical("WittyPi service is active but WittyPi is disabled in HoneyPi settings!")
        if wittypi_status['service_active'] and settings['wittyPi']['enabled']:
            logger.warning("WittyPi service is active and WittyPi is enabled in HoneyPi settings! WittyPi service is not required and could cause issues.")
        if settings['wittyPi']['enabled'] and wittypi_status['service_active'] != settings['wittyPi']['enabled']:
            logger.debug("WittyPi is enabled in HoneyPi settings and WittyPi service is not active!")
        if wittypi_status['is_mc_connected'] and str(wittypi_status['low_voltage_threshold']) != 'disabled':
            if settings['wittyPi']['voltagecheck_enabled'] and (wittypi_status['low_voltage_threshold'] >= settings['wittyPi']['low']['voltage']):
                logger.critical("WittyPi low voltage threshold '" + str(wittypi_status['low_voltage_threshold']) + " Volt' is set to a higher value than HoneyPi low voltage threshold '" + str(settings['wittyPi']['low']['voltage']) + " Volt'")
            elif settings['wittyPi']['voltagecheck_enabled'] and (wittypi_status['low_voltage_threshold'] < settings['wittyPi']['low']['voltage']):
                logger.debug("WittyPi low voltage threshold is set to '" + str(wittypi_status['low_voltage_threshold']) + " Volt', HoneyPi low voltage threshold is set to '" + str(settings['wittyPi']['low']['voltage']) + " Volt'")
            else:
                logger.debug("WittyPi low voltage threshold is set to " + str(wittypi_status['low_voltage_threshold']) + " Volt" )
        if wittypi_status['is_mc_connected'] and str(wittypi_status['recovery_voltage_threshold']) != 'disabled':
            if settings['wittyPi']['voltagecheck_enabled'] and (wittypi_status['recovery_voltage_threshold'] >= settings['wittyPi']['low']['voltage']):
                logger.critical("WittyPi recovery voltage threshold '" + str(wittypi_status['recovery_voltage_threshold']) + " Volt' is set to a higher value than HoneyPi low voltage threshold '" + str(settings['wittyPi']['low']['voltage']) + " Volt'")
            elif settings['wittyPi']['voltagecheck_enabled'] and (wittypi_status['recovery_voltage_threshold'] < settings['wittyPi']['low']['voltage']):
                logger.debug("WittyPi recovery voltage threshold is set to '" + str(wittypi_status['recovery_voltage_threshold']) + " Volt', HoneyPi low voltage threshold  is set to '" + str(settings['wittyPi']['low']['voltage']) + " Volt'")
            else:
                logger.debug("WittyPi recovery voltage threshold is set to " + str(wittypi_status['recovery_voltage_threshold']) + " Volt" )
        wittypi_status = check_wittypi_rtc(settings, wittypi_status) # TODO this will be called each time from main even if wittypi is disabled/ not connected - sure? Call it seperately after check_wittypi got called if required
        if settings['wittyPi']['enabled']:
            if wittypi_status['is_mc_connected']:
                if settings['wittyPi']['dummyload'] is not None and (wittypi_status['dummy_load_duration'] != settings['wittyPi']['dummyload']):
                    logger.warning("WittyPi dummy load duration defered from settings, updating setting on WittyPi to " + str(settings['wittyPi']['dummyload']) + " seconds")
                    set_dummy_load_duration(settings['wittyPi']['dummyload'])
                if settings['wittyPi']['default_state'] is not None and (wittypi_status['default_state'] != settings['wittyPi']['default_state']):
                    logger.warning("WittyPi default state defered from settings, updating setting on WittyPi to " + str(settings['wittyPi']['default_state']))
                    set_default_state(settings['wittyPi']['default_state'])
                if settings['wittyPi']['power_cut_delay'] is not None and (wittypi_status['power_cut_delay'] != settings['wittyPi']['power_cut_delay']):
                    logger.warning("WittyPi power_cut_delay defered from settings, updating setting on WittyPi to " + str(settings['wittyPi']['power_cut_delay']))
                    set_power_cut_delay(settings['wittyPi']['power_cut_delay'])
                if settings['wittyPi']['pulsing_interval'] is not None and (wittypi_status['pulsing_interval'] != settings['wittyPi']['pulsing_interval']):
                    logger.warning("WittyPi pulsing_interval defered from settings, updating setting on WittyPi to " + str(settings['wittyPi']['pulsing_interval']))
                    set_pulsing_interval(settings['wittyPi']['pulsing_interval'])
                if settings['wittyPi']['white_led_duration'] is not None and (wittypi_status['white_led_duration'] != settings['wittyPi']['white_led_duration']):
                    logger.warning("WittyPi white_led_duration defered from settings, updating setting on WittyPi to " + str(settings['wittyPi']['white_led_duration']))
                    set_white_led_duration(settings['wittyPi']['white_led_duration'])
            if wittypi_status['is_rtc_connected']:
                check_wittypi_schedule(settings, wittypi_status)
        if not settings['wittyPi']['enabled'] and wittypi_status['is_rtc_connected']:
            if wittypi_status['startup_time_local'] is not None or wittypi_status['shutdown_time_local'] is not None:
                logger.critical("WittyPi is disabled in settings but a startup / shutdown time is set on WittyPi")
    except Exception as ex:
        logger.exception("Error in function check_wittypi")
    return wittypi_status

def get_wittypi_status(settings):
    try:
        wittyPi_status = {}
        wittyPi_status = getAll()
        return wittyPi_status
    except Exception as ex:
        logger.exception("Error in function get_wittyPi_status")

def pause_wittypi_schedule(loggername='HoneyPi.wittypiutilities'):
    try:
        logger = logging.getLogger(loggername)
        if os.path.isfile(wittypi_scheduleFile) and os.stat(wittypi_scheduleFile).st_size > 1: #existiert '/var/www/html/backend/schedule.wpi' und ist größer wie 1 Bit
            os.rename(wittypi_scheduleFile, wittypi_scheduleFile + ".bak")
            update_wittypi_schedule("")
            logger.debug("Pausing wittyPi schedule...")
    except Exception as ex:
        logger.exception("Error in function pause_wittypi_schedule")

def check_wittypi_scheduleFile_backup():
    found_scheduleFile_backup = False
    try:
            if os.path.isfile(wittypi_scheduleFile + ".bak") and not os.path.isfile(wittypi_scheduleFile):
                os.rename(wittypi_scheduleFile + ".bak", wittypi_scheduleFile)
                logger.debug("Found only wittyPi schedule backup. Renaming '" + wittypi_scheduleFile + ".bak' to '" + wittypi_scheduleFile + "' and set schedules!" )
                found_scheduleFile_backup = True
            elif os.path.isfile(wittypi_scheduleFile + ".bak") and os.path.isfile(wittypi_scheduleFile) and os.stat(wittypi_scheduleFile).st_size > 1 and os.stat(wittypi_scheduleFile + ".bak").st_size != os.stat(wittypi_scheduleFile).st_size:
                # if schedule is not empty and schedule changed in the meantime (=> someone saved a new schedule in maintenance)
                logger.debug("Found wittyPi schedule '" + wittypi_scheduleFile + "' and backup. Removing '" + wittypi_scheduleFile + ".bak'")
                found_scheduleFile_backup = True
                os.remove(wittypi_scheduleFile + ".bak")
            elif os.path.isfile(wittypi_scheduleFile + ".bak") and os.path.isfile(wittypi_scheduleFile) and os.stat(wittypi_scheduleFile).st_size == 0 and os.stat(wittypi_scheduleFile + ".bak").st_size != os.stat(wittypi_scheduleFile).st_size:
                # if schedule is empty and schedule changed in the meantime (=> someone ended maintenance without saving)
                logger.debug("Found empty wittyPi schedule '" + wittypi_scheduleFile + "' and schedule backup. Restoring '" + wittypi_scheduleFile + ".bak'")
                found_scheduleFile_backup = True
                os.replace( wittypi_scheduleFile + ".bak", wittypi_scheduleFile)
    except Exception as ex:
        logger.exception("Error in function check_wittypi_scheduleFile_backup")
    return found_scheduleFile_backup

def continue_wittypi_schedule(loggername='HoneyPi.wittypiutilities'):
    try:
        logger = logging.getLogger(loggername)
        check_wittypi_scheduleFile_backup()
        set_wittypi_schedule(loggername)
    except Exception as ex:
        logger.exception("Error in function continue_wittypi_schedule")

def clear_wittypi_schedule(loggername='HoneyPi.wittypiutilities'):
    try:
        logger = logging.getLogger(loggername)
        startup_time_cleared = clear_startup_time()
        shutdown_time_cleared = clear_shutdown_time()
        if startup_time_cleared and shutdown_time_cleared:
            logger.debug("Cleared wittyPi startup / shutdown...")
        else:
            logger.error("Error while clearing wittyPi startup / shutdown...")
    except Exception as ex:
        logger.exception("Error in function clear_wittypi_schedule")

def set_wittypi_schedule(loggername='HoneyPi.wittypiutilities'):
    try:
        logger = logging.getLogger(loggername)
        schedulefile_exists = os.path.isfile(wittypi_scheduleFile) and os.stat(wittypi_scheduleFile).st_size > 1 #existiert '/var/www/html/backend/schedule.wpi' und ist größer wie 1 Bit
        wittyPiPath = get_wittyPiPath()
        if schedulefile_exists:
            logger.debug("Found schedule file in " + wittypi_scheduleFile)
            copy_wittypi_schedulefile(wittypi_scheduleFile, wittyPiPath + wittypi_scheduleFileName) #Kopieren von '/var/www/html/backend/schedule.wpi' nach 'home/pi/wittipi/schedule.wpi'
            runscript(loggername) #setzen von wittyPi Startup / Shutdown
        else:
            logger.debug("No schedule file in " + wittypi_scheduleFile + " found, pausing wittyPi schedule by removing scheduled startup / shutdown...")
            clear_wittypi_schedule(loggername) #Löschen von wittyPi Startup / Shutdown
        return True
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

def copy_wittypi_schedulefile(source, target):
    try:
        assert os.path.isfile(source)
        shutil.copyfile(source, target)
        logger.debug("WittyPi schedulefile copied from '" + source + "' to '" + target + "'")
        uid = pwd.getpwnam("pi").pw_uid
        gid = grp.getgrnam("pi").gr_gid
        os.chown(target, uid, gid)
    except IOError:
        logger.error("IOError while WittyPi schedulefile copied from '" + source + "' to '" + target + "'")
    except AssertionError:
        logger.error("WittyPi schedulefile '" + source + "' is not existing")
    except shutil.SameFileError as e:
        logger.debug("WittyPi schedulefile '" + source + "' is already same as '" + target + "'")






if __name__ == '__main__':
    try:
        from constant import scriptsFolder, logfile, settingsFile, local_tz
        from read_settings import get_settings
        from main import timesync
        import threading
        from logging.handlers import RotatingFileHandler
        loggername='HoneyPi.wittypiutilities.fromWebIf'
        logger = logging.getLogger(loggername)
        logger.setLevel(logging.DEBUG)
        try:
            fh = RotatingFileHandler(logfile, maxBytes=5*1024*1024, backupCount=60)
        except PermissionError:
            #set file access
            #fix_fileaccess(scriptsFolder + '/err*.*')
            fh = RotatingFileHandler(logfile, maxBytes=5*1024*1024, backupCount=60)

        #fh.setLevel(logging.getLevelName(debuglevel_logfile))
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        #ch.setLevel(logging.getLevelName(debuglevel))
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(fh)
        logger.addHandler(ch)

        settings = get_settings()
        debuglevel=int(settings["debuglevel"])
        debuglevel_logfile=int(settings["debuglevel_logfile"])

        logger.setLevel(logging.DEBUG)
        fh.setLevel(logging.getLevelName(debuglevel_logfile))
        ch.setLevel(logging.getLevelName(debuglevel))
        source = wittypi_scheduleFile
        target = get_wittyPiPath() + wittypi_scheduleFileName
        parser = argparse.ArgumentParser()
        parser.add_argument("argument", help="Use an integer value as argument.\r\n 0 - clear schedule\r\n 1 - set schedule\r\n 2 - load settings and set RTC time\r\n 3 - load settings and set RTC time;", type=int)
        args = parser.parse_args()
        if args.argument == 0:
            logger.info('Clearing WittyPi schedule.')
            clear_wittypi_schedule(loggername)
        elif args.argument == 1:
            logger.info('Synchronizing time and setting WittyPi schedule.')
            wittypi_status = check_wittypi(settings)
            ttimesync = threading.Thread(target=timesync, args=(settings, wittypi_status, loggername))
            ttimesync.start()
            ttimesync.join(timeout=45)
            if ttimesync.is_alive():
                logger.warning("Thread to syncronize time with NTP Server is still not finished!")
            continue_wittypi_schedule(loggername)
        elif args.argument == 2:
            logger.info('Updating WittyPi settings and synchronizing time if required.')
            wittypi_status = check_wittypi(settings)
            if ('rtc_time_is_valid' in wittypi_status) and not wittypi_status['rtc_time_is_valid'] or 'time_out_of_snyc' in wittypi_status and wittypi_status['time_out_of_snyc']:
                logger.debug('rtc_time_is_valid: ' + str(wittypi_status['rtc_time_is_valid']) + ' time_out_of_snyc: ' + str(wittypi_status['time_out_of_snyc']))
                ttimesync = threading.Thread(target=timesync, args=(settings, wittypi_status))
                ttimesync.start()
                ttimesync.join(timeout=45)
                if ttimesync.is_alive():
                    logger.warning("Thread to syncronize time with NTP Server is still not finished!")
        elif args.argument == 3:
            logger.info('Updating WittyPi settings and synchronizing time if required.')
            wittypi_status = check_wittypi(settings)
            if ('rtc_time_is_valid' in wittypi_status) and not wittypi_status['rtc_time_is_valid'] or 'time_out_of_snyc' in wittypi_status and wittypi_status['time_out_of_snyc']:
                logger.debug('rtc_time_is_valid: ' + str(wittypi_status['rtc_time_is_valid']) + ' time_out_of_snyc: ' + str(wittypi_status['time_out_of_snyc']))
                ttimesync = threading.Thread(target=timesync, args=(settings, wittypi_status))
                ttimesync.start()
                ttimesync.join(timeout=45)
                if ttimesync.is_alive():
                    logger.warning("Thread to syncronize time with NTP Server is still not finished!")
        else:
            print ('Unsupported')
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
    except Exception as ex:
        logger.error("Unhandled Exception in __main__ " + repr(ex))
