#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

#https://www.haraldkreuzer.net/aktuelles/mit-gps-modul-die-uhrzeit-fuer-raspberry-pi-3-a-plus-setzen-ganz-ohne-netzwerk

import datetime as dt
import pytz
import os
from sensors.PA1010D import *
from timezonefinder import TimezoneFinder
from utilities import get_abs_timedifference
import logging
import inspect

logger = logging.getLogger('HoneyPi.gps')

gps = PA1010D()

timeout=30
waitforfix=True

local_tz = dt.datetime.utcnow().astimezone().tzinfo
utc_tz = pytz.timezone('UTC')

def init_gps(gpsSensor):
    global gps
    i2c_addr = 0x10
    try:
        if 'i2c_addr' in gpsSensor and gpsSensor["i2c_addr"] is not None:
            #i2c_addr = int(i2c_addr,16)
            i2c_addr = int(gpsSensor["i2c_addr"],0)
        logger.debug("Initializing GPS at '" + format(i2c_addr, "x") +"'")
        gps = PA1010D(i2c_addr)
        # Turn off everything
        gps.send_command(b'PMTK314,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
        # Turn on the basic GGA, RMC and VTG info (what you typically want)
        gps.send_command(b'PMTK314,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
    except IOError as ex:
        if str(ex) == "[Errno 121] Remote I/O error":
            logger.error("Could not access GPS at I2C Adress " + format(i2c_addr, "x") + "!")
        else:
            logger.exception("Other IOError ")
        return
    except Exception as ex:
        logger.exception("Exception in init_gps")
    return


def get_gps_timestamp(timeout=timeout):
    nema_type="RMC"
    UTCtime,localtime,timestamp = None, None, None
    try:
        gpsfix = False
        try:
            gpsfix = gps.update(nema_type, timeout, waitforfix)
        except TimeoutError:
            logger.warning("Could not get GPS time within " + str(timeout) + " seconds!")
            pass
        if gpsfix:
            UTCtime = gps.datetimestamp
            UTCtime = pytz.utc.localize(UTCtime).astimezone(utc_tz)
            localtime = UTCtime.astimezone(local_tz)
            timestamp = int(time.mktime(UTCtime.timetuple()))
            logger.debug("GPS time is " + str(localtime.strftime("%a %d %b %Y %H:%M:%S")) + " " + str(local_tz))
    except IOError as ex:
        if str(ex) == "[Errno 121] Remote I/O error":
            logger.error("Could not access GPS!")
        else:
            logger.exception("Other IOError in get_gps_timestamp")
    except Exception as ex:
        logger.exception("Exceptionin get_gps_timestamp")
    return UTCtime,localtime,timestamp

def get_gps_location(timeout=timeout):
    nema_type="GGA"

    latitude = None
    longitude = None
    altitude = None

    try:
        gpsfix = False
        try:
            gpsfix = gps.update(nema_type, timeout, waitforfix)
        except TimeoutError:
            logger.warning("Could not get GPS location within " + str(timeout) + " seconds!")
            pass
        if gpsfix:
            latitude = gps.latitude
            longitude = gps.longitude
            altitude = gps.altitude
            logger.debug(f""" Latitude: {latitude: .5f} Longitude: {longitude: .5f} Altitude: {altitude}""")
        else:
            logger.debug("No GPS fix!")
    except IOError as ex:
        if str(ex) == "[Errno 121] Remote I/O error":
            logger.error("Could not access GPS!")
        else:
            logger.exception("other IOError in get_gps_location")
    except Exception as ex:
        logger.exception("Exception in get_gps_location")
    return latitude, longitude, altitude

def set_timezonefromcoordinates(latitude, longitude):
    try:
        assert (latitude != None)
        assert (longitude != None)
        tf = TimezoneFinder()
        strtimezone = tf.timezone_at(lng=longitude, lat=latitude)
        logger.info("Set timezone to '" + strtimezone + "' based on latitude: " + str(latitude) + " longitude: " + str(longitude))
        os.system(f"sudo timedatectl set-timezone {strtimezone}")
    except AssertionError as ex:
        logger.error("Invalid Coordinates, could not set timezone!")
    except Exception as ex:
        logger.exception("Exception " + str(ex))
    return



def timesync_gps(gpsSensor):
    try:
        gps_values = {}
        UTCtime,localtime,timestamp = None, None, None
        if 'timeout' in gpsSensor and gpsSensor["timeout"] is not None:
            timeout = gpsSensor["timeout"]
        logger.debug("Start receiving GPS location and time, waiting "+ str(timeout) + " seconds for GPS fix!")
        latitude, longitude, altitude = get_gps_location(timeout)
        set_timezonefromcoordinates(latitude, longitude)
        UTCtime,localtime,timestamp = get_gps_timestamp(timeout)
        if UTCtime is not None and localtime is not None:
            nowUTC = dt.datetime.now(utc_tz)
            nowLOCAL = nowUTC.astimezone(local_tz)
            updatesystemtime = False
            abs_timedelta_totalseconds = round(get_abs_timedifference(nowUTC, UTCtime))
            if abs_timedelta_totalseconds >= 300:
                logger.critical("Difference between GPS time and sytstem time is " + str(abs_timedelta_totalseconds) + " seconds")
                updatesystemtime = True
            elif abs_timedelta_totalseconds >= 120:
                logger.warning("Difference between GPS time and sytstem time is " + str(abs_timedelta_totalseconds) + " seconds")
            else:
                logger.debug("Difference between GPS time and sytstem time is " + str(abs_timedelta_totalseconds) + " seconds (GPS time provided by NMEA is not accurate!)")
            if updatesystemtime:
                logger.info('Writing GPS time ' + localtime.strftime("%a %d %b %Y %H:%M:%S") + ' to system, old time was ' + nowLOCAL.strftime("%a %d %b %Y %H:%M:%S") + ' ...')
                value = os.system('sudo date -u -s "' + UTCtime.strftime("%d %b %Y %H:%M:%S") + '" >>/dev/null')
                if value == 0:
                    logger.debug('Successfully wrote GPS time to system...')
                else:
                    logger.error('Failure writing GPS time to system...')
    except Exception as ex:
        logger.exception("Exception in timesync_gps")
    return False


def measure_gps_time(gpsSensor):
    UTCtime,localtime,timestamp = None, None, None
    try:
        if 'timeout' in gpsSensor and gpsSensor["timeout"] is not None:
            timeout = gpsSensor["timeout"]
        logger.debug("Start receiving GPS time, waiting "+ str(timeout) + " seconds for GPS fix!")
        UTCtime,localtime,timestamp = get_gps_timestamp(timeout)
    except Exception as ex:
        logger.exception("Exception in measure_gps_time")
    return UTCtime,localtime,timestamp

def measure_gps(gpsSensor):
    gps_values = {}
    try:
        if 'timeout' in gpsSensor and gpsSensor["timeout"] is not None:
            timeout = gpsSensor["timeout"]
        logger.debug("Start measureing GPS, waiting "+ str(timeout) + " seconds for GPS fix!")
        gps_values['latitude'], gps_values['longitude'], gps_values['elevation'] = get_gps_location(timeout)
    except Exception as ex:
        logger.exception("Exception in measure_gps")
    return gps_values


def main():

    logging.basicConfig(level=logging.DEBUG)

    try:
        get_gps_timestamp()
        get_gps_location()

    except Exception as ex:
        logger.exception("Unhandled Exception in main")

if __name__ == '__main__':
    try:
        main()

    except (KeyboardInterrupt, SystemExit):
        logger.debug("exit")
        exit
    except Exception as ex:
        logger.error("Unhandled Exception in "+ __name__)
