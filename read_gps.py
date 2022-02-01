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
# Turn off everything
gps.send_command(b'PMTK314,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
# Turn on the basic GGA, RMC and VTG info (what you typically want)
gps.send_command(b'PMTK314,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')

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
            logger.error("Could not get GPS time within " + str(timeout) + " seconds!")
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
    
    longitude = None
    latitude = None
    altitude = None
    
    try:
        gpsfix = False
        try:
            gpsfix = gps.update(nema_type, timeout, waitforfix) 
        except TimeoutError:
            logger.error("Could not get GPS location within " + str(timeout) + " seconds!")
            pass
        if gpsfix:
            longitude = gps.longitude
            latitude = gps.latitude
            altitude = gps.altitude
            logger.debug(f""" Longitude: {longitude: .5f} Latitude: {latitude: .5f} Altitude: {altitude}""")
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