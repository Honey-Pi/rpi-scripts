#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

#https://www.haraldkreuzer.net/aktuelles/mit-gps-modul-die-uhrzeit-fuer-raspberry-pi-3-a-plus-setzen-ganz-ohne-netzwerk

import datetime as dt
import pytz

from sensors.PA1010D import *

import logging
import inspect

loggername='HoneyPi.gps' #+ inspect.getfile(inspect.currentframe())
logger = logging.getLogger(loggername)

gps = PA1010D()

timeout=30
waitforfix=True

local_tz = dt.datetime.utcnow().astimezone().tzinfo
utc_tz = pytz.timezone('UTC')

def get_gps_timestamp(): 
    logger = logging.getLogger(loggername + '.' + inspect.currentframe().f_code.co_name)
    nema_type="RMC"
    UTCtime,localtime,timestamp = None, None, None
    try:
        gpsfix = False
        try:
            gpsfix = gps.update(nema_type, timeout, waitforfix) 
        except TimeoutError:
            pass
        if gpsfix:
            UTCtime = gps.datetimestamp
            UTCtime = pytz.utc.localize(UTCtime).astimezone(utc_tz)
            localtime = UTCtime.astimezone(local_tz)
            timestamp = int(time.mktime(UTCtime.timetuple()))
            logger.debug("GPS time is " + str(localtime.strftime("%a %d %b %Y %H:%M:%S")) + " " + str(local_tz))
    except Exception as ex:
        logger.exception("Exception " + str(ex))
    return UTCtime,localtime,timestamp

def get_gps_location(): 
    logger = logging.getLogger(loggername + '.' + inspect.currentframe().f_code.co_name)
    nema_type="GGA"
    
    timestamp = None
    longitude = None
    lon_dir = None
    latitude = None
    lat_dir = None
    altitude = None
    geoid_sep = None
    geoid_alt = None
    num_sats = None
    gps_qual = None
    
    try:
        gpsfix = False
        try:
            gpsfix = gps.update(nema_type, timeout, waitforfix) 
        except TimeoutError:
            pass
        if gpsfix:
            timestamp = gps.timestamp
            longitude = gps.longitude
            lon_dir = gps.lon_dir
            latitude = gps.latitude
            lat_dir = gps.lat_dir
            altitude = gps.altitude
            geoid_sep = gps.geo_sep
            geoid_alt =(float(gps.altitude) + -float(gps.geo_sep))
            num_sats = gps.num_sats
            gps_qual = gps.gps_qual
            logger.debug(f""" Time: {timestamp} Longitude: {longitude: .5f} {lon_dir} Latitude: {latitude: .5f} {lat_dir} Altitude: {altitude} Geoid_Sep: {geoid_sep} Geoid_Alt: {geoid_alt: .5f} Used Sats: {num_sats} Quality: {gps_qual}""")
    except Exception as ex:
        logger.exception("Exception " + str(ex))
    return longitude, latitude, altitude

def main():
    #logger = logging.getLogger(loggername + '.' + __name__)
    logging.basicConfig(level=logging.DEBUG)
    try:
        get_gps_timestamp()
        get_gps_location()

    except Exception as ex:
        logger.exception("Unhandled Exception: " + str(ex))

if __name__ == '__main__':
    try:
        main()

    except (KeyboardInterrupt, SystemExit):
        logger.debug("exit")
        exit
    except Exception as ex:
        logger.error("Unhandled Exception in "+ __name__ + repr(ex))