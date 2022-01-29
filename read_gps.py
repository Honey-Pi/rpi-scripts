# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Simple GPS module demonstration.
# Will print NMEA sentences received from the GPS, great for testing connection
# Uses the GPS to send some commands, then reads directly from the GPS
import time
import board
import busio

import adafruit_gps
import pynmea2

import logging
import inspect

loggername='HoneyPi.gps' #+ inspect.getfile(inspect.currentframe())
logger = logging.getLogger(loggername)

'''
# Create a serial connection for the GPS connection using default speed and
# a slightly higher timeout (GPS modules typically update once a second).
# These are the defaults you should use for the GPS FeatherWing.
# For other boards set RX = GPS module TX, and TX = GPS module RX pins.
#uart = busio.UART(board.TX, board.RX, baudrate=9600, timeout=10)

# for a computer, use the pyserial library for uart access
# import serial
# uart = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=10)

# If using I2C, we'll create an I2C interface to talk to using default pins
i2c = board.I2C()

# Create a GPS module instance.
#gps = adafruit_gps.GPS(uart)  # Use UART/pyserial
gps = adafruit_gps.GPS_GtopI2C(i2c)  # Use I2C interface

# Initialize the GPS module by changing what data it sends and at what rate.
# These are NMEA extensions for PMTK_314_SET_NMEA_OUTPUT and
# PMTK_220_SET_NMEA_UPDATERATE but you can send anything from here to adjust
# the GPS module behavior:
#   https://cdn-shop.adafruit.com/datasheets/PMTK_A11.pdf

# Turn on the basic GGA and RMC info (what you typically want)
gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
# Turn on just minimum info (RMC only, location):
# gps.send_command(b'PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
# Turn off everything:
# Tuen on everything (not all of it is parsed!)
# gps.send_command(b'PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0')

# Set update rate to once a second (1hz) which is what you typically want.
gps.send_command(b"PMTK220,1000")
# Or decrease to once every two seconds by doubling the millisecond value.
# Be sure to also increase your UART timeout above!
# gps.send_command(b'PMTK220,2000')
# You can also speed up the rate, but don't go too fast or else you can lose
# data during parsing.  This would be twice a second (2hz, 500ms delay):
# gps.send_command(b'PMTK220,500')

# Main loop runs forever printing data as it comes in

timestamp = time.monotonic()
while True:
    data = gps.read(32)  # read up to 32 bytes

    if data is not None:
        #print(data)  # this is a bytearray type
        # convert bytearray to string
        data_string = "".join([chr(b) for b in data])
        print(data_string, end="")
        try:
            result = pynmea2.parse(data_string)
            print("Result: "+ str(result))
        except pynmea2.nmea.ParseError:
                print("Parse error: ")#{sentence}".format(sentence=sentence))
            #continue
        # Time, position and fix
"""
    if time.monotonic() - timestamp > 5:
        # every 5 seconds...
        gps.send_command(b"PMTK605")  # request firmware version
        timestamp = time.monotonic()
"""

'''
i2c = board.I2C()
gps1 = adafruit_gps.GPS_GtopI2C(i2c)  # Use I2C interface
gps1.send_command(b'PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0')

from pa1010d import PA1010D


gps = PA1010D()


def main():
    #logger = logging.getLogger(loggername + '.' + __name__)
    logging.basicConfig(level=logging.DEBUG)
    try:

        while True:
            #logger.debug("Start Loop")

            try:
                sentence = gps.read_sentence()
            except TimeoutError:
                logger.debug("TimeoutError")
                continue
            except IOError:
                logger.debug("IOError")
                continue

            try:
                result = pynmea2.parse(sentence)
            except pynmea2.nmea.ParseError:
                logger.debug("ParseError: " + str(sentence))
                continue
                
            #logger.debug("Start Loop2")
            if result is None:
                logger.debug("no result")
            
            if type(result) == pynmea2.GGA:
                #logger.debug("GGA: " + str(result))
                if result.gps_qual is None:
                    num_sats = 0
                    gps_qual = 0
                elif result.gps_qual != 0:
                    timestamp = result.timestamp
                    logger.info("GGA Time: " + timestamp.strftime("%a %d %b %Y %H:%M:%S"))
                    latitude = result.latitude
                    longitude = result.longitude
                    lat_dir = result.lat_dir
                    lon_dir = result.lon_dir
                    altitude = result.altitude
                    geo_sep = result.geo_sep
                    num_sats = result.num_sats
                    gps_qual = result.gps_qual
                elif result.gps_qual == 0:
                    logger.debug('No GPS fix! ' + str(result))
                else:
                    logger.debug('GGA Else! ' + str(result))

            # Geographic Lat/Lon (Loran holdover)
            elif type(result) == pynmea2.GLL:
                logger.debug("GLL: " + str(result))
                #print(sentence)

            # GPS DOP and active satellites
            elif type(result) == pynmea2.GSA:
                logger.debug("GSA: " + str(result))
                mode_fix_type = result.mode_fix_type
                pdop = result.pdop
                hdop = result.hdop
                vdop = result.vdop

            # Position, velocity and time
            elif type(result) == pynmea2.RMC:
                #logger.debug("RMC: "+ str(result))
                if result.status == 'A':
                    logger.debug("RMC: " + str(result))
                    timestamp = result.timestamp
                    logger.info("RMC Time: " + timestamp.strftime("%a %d %b %Y %H:%M:%S"))
                    speed_over_ground = result.spd_over_grnd
                    
                    #https://www.haraldkreuzer.net/aktuelles/mit-gps-modul-die-uhrzeit-fuer-raspberry-pi-3-a-plus-setzen-ganz-ohne-netzwerk
                else:
                    logger.debug('No GPS fix! ' + str(result))


            # Track made good and speed over ground
            elif type(result) == pynmea2.VTG:
                logger.debug("VTG: " + str(result))
                #print(sentence)

            # SVs in view, PRN, elevation, azimuth and SNR
            elif type(result) == pynmea2.GSV:
                logger.debug("GSV: " + str(result))
                #print(sentence)

            # ProprietarySentence handles boot up output such as "$PMTK011,MTKGPS*08"
            elif type(result) == pynmea2.ProprietarySentence:
                # TODO If we implement sending commands *to* the GPS,
                # they should not be permitted until after receiving this sequence
                # $PMTK011,MTKGPS*08 Successful bootup
                # $PMTK010,001*2E    Startup
                # $PMTK010,002*2D    Wake from standby, normal operation
                logger.debug("ProprietarySentence: " + str(result))
                #print(sentence)

            else:
                # If native MTK support exists, check for those message types
                # requires merge and release of: https://github.com/Knio/pynmea2/pull/111
                # TODO Drop this special case when #111 is merged & released
                try:
                    if type(result) in (
                        pynmea2.types.proprietary.mtk.MTK011,
                        pynmea2.types.proprietary.mtk.MTK010
                    ):
                        logger.debug("proprietary: " + str(result))
                        #print(sentence)

                except AttributeError:
                    pass
                raise RuntimeError("Unsupported message type {type} ({sentence})".format(type=type(result), sentence=sentence))


            
            
            
            #print(str(result.gps_qual))
            time.sleep(1.0)
            
            


    except Exception as ex:
        logger.exception("Unhandled Exception1: " + str(ex))

if __name__ == '__main__':
    try:
        main()

    except (KeyboardInterrupt, SystemExit):
        logger.debug("exit")
        exit
    except Exception as ex:
        logger.error("Unhandled Exception in "+ __name__ + repr(ex))