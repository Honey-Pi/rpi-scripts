import time
import smbus


import pynmea2

import logging
import inspect

loggername='PA1010D' #+ inspect.getfile(inspect.currentframe())
logger = logging.getLogger(loggername)

__version__ = '0.0.3.1'

PA1010D_ADDR = 0x10


class PA1010D():
    __slots__ = (
        "timestamp",
        "datestamp",
        "datetimestamp",
        "latitude",
        "longitude",
        "altitude",
        "altitude_units",
        "lat",
        "lat_dir",
        "lon",
        "lon_dir",
        "geo_sep",
        "geo_sep_units",
        "horizontal_dil",
        "num_sats",
        "gps_qual",
        "status",
        "faa_mode",
        "true_track",
        "true_track_sym",
        "mag_track",
        "mag_track_sym",
        "spd_over_grnd_kts",
        "spd_over_grnd_kts_sym",
        "spd_over_grnd_kmph",
        "spd_over_grnd_kmph_sym",
        "speed_over_ground",
        "mag_variation",
        "mag_var_dir",
        "mode_fix_type",
        "pdop",
        "hdop",
        "vdop",
        "age_gps_data",
        "ref_station_id",
        "_i2c_addr",
        "_i2c",
        "_debug"
    )


    def __init__(self, i2c_addr=PA1010D_ADDR, debug=False):
        self._i2c_addr = i2c_addr
        self._i2c = smbus.SMBus(1)

        self._debug = debug

        self.timestamp = None
        self.datetimestamp = None
        self.latitude = None
        self.longitude = None
        self.altitude = None
        self.altitude_units = None
        self.num_sats = None
        self.gps_qual = None
        self.status = None
        self.faa_mode = None
        self.true_track = None
        self.true_track_sym = None
        self.mag_track = None
        self.mag_track_sym = None
        self.spd_over_grnd_kts = None
        self.spd_over_grnd_kts_sym = None
        self.spd_over_grnd_kmph = None
        self.spd_over_grnd_kmph_sym = None
        self.horizontal_dil = None
        self.lat = None
        self.lat_dir = None
        self.lon = None
        self.lon_dir = None
        self.geo_sep = None
        self.geo_sep_units = None
        self.age_gps_data = None
        self.ref_station_id = None
        self.pdop = None
        self.hdop = None
        self.vdop = None

        self.speed_over_ground = None
        self.mag_variation = None
        self.mag_var_dir = None
        self.mode_fix_type = None

    @property

    def data(self):
        return dict((slot, getattr(self, slot)) for slot in self.__slots__)

    def _write_sentence(self, bytestring):
        """Write a sentence to the PA1010D device over i2c.

        We could- in theory- do this in one burst, but since smbus is limited to 32bytes,
        we would have to chunk the message and this is already one byte chunks anyway!

        """
        try:
            for char_index in bytestring:
                self._i2c.write_byte(self._i2c_addr, char_index)
        except IOError as ex:
            raise IOError(str(ex))
        except Exception as ex:
            logger.exception("Unhandled Exception :" + str(ex))

    def send_command(self, command, add_checksum=True):
        """Send a command string to the PA1010D.

        If add_checksum is True (the default) a NMEA checksum will automatically be computed and added.

        """
        try:
        # TODO replace with pynmea2 functionality
            if command.startswith(b"$"):
                command = command[1:]
            if command.endswith(b"*"):
                command = command[:-1]

            buf = bytearray()
            buf += b'$'
            buf += command
            if add_checksum:
                checksum = 0
                # bytes() is a real thing in Python 3
                # so `for char in commaud` iterates through char ordinals
                for char in command:
                    checksum ^= char
                buf += b'*'  # Delimits checksum value
                buf += "{checksum:02X}".format(checksum=checksum).encode("ascii")
            buf += b'\r\n'
            self._write_sentence(buf)
        except IOError as ex:
            raise IOError(str(ex))
        except Exception as ex:
            logger.exception("Unhandled Exception :" + str(ex))

    def read_sentence(self, timeout=5):
        """Attempt to read an NMEA sentence from the PA1010D."""
        try:
            buf = []
            timeout += time.time()

            while time.time() < timeout:
                char = self._i2c.read_byte_data(self._i2c_addr, 0x00)

                if len(buf) == 0 and char != ord("$"):
                    continue

                buf += [char]

                # Check for end of line
                # Should be a full \r\n since the GPS emits spurious newlines
                if buf[-2:] == [ord("\r"), ord("\n")]:
                    # Remove line ending and spurious newlines from the sentence
                    return bytearray(buf).decode("ascii").strip().replace("\n","")

            raise TimeoutError("Timeout waiting for readline")

        except IOError as ex:
            raise IOError(str(ex))
        except Exception as ex:
            logger.exception("Unhandled Exception :" + str(ex))


    def update(self, wait_for="GGA", timeout=5, waitforfix=False):
        """Attempt to update from PA1010D.

        Returns true if a sentence has been successfully parsed.

        Returns false if an error has occured.

        Will wait 5 seconds for a GGA message by default.

        :param wait_for: Message type to wait for.
        :param timeout: Wait timeout in seconds
        :param waitforfix: Will return true only once GPS signal has fix

        """
        try:
            timeout += time.time()

            while time.time() < timeout:
                try:
                    sentence = self.read_sentence()
                except TimeoutError:
                    logger.debug("Timeout error")
                    continue

                try:
                    result = pynmea2.parse(sentence)
                except pynmea2.nmea.ParseError:
                    if self._debug:
                        logger.debug("Parse error: {sentence}".format(sentence=sentence))
                    continue

                # Time, position and fix
                if type(result) == pynmea2.GGA: #$--GGA,hhmmss.ss,llll.ll,a,yyyyy.yy,a,x,xx,x.x,x.x,M,x.x,M,x.x,xxxx*hh<CR><LF>
                    logger.debug("GGA: " + str(result))
                    if result.gps_qual is not None:
                        if waitforfix and result.gps_qual > 0:
                            self.timestamp = result.timestamp
                            self.latitude = result.latitude
                            self.longitude = result.longitude
                            self.lat = result.lat
                            self.lat_dir = result.lat_dir
                            self.lon = result.lon
                            self.lon_dir = result.lon_dir
                            self.gps_qual = result.gps_qual
                            self.num_sats = result.num_sats
                            self.horizontal_dil = result.horizontal_dil
                            self.altitude = float(result.altitude or 0.0)
                            self.altitude_units = result.altitude_units
                            self.geo_sep = float(result.geo_sep or 0.0)
                            self.geo_sep_units = result.geo_sep_units
                            self.age_gps_data = result.age_gps_data
                            self.ref_station_id = result.ref_station_id
                            if wait_for == "GGA":
                                return True
                        elif not waitforfix:
                            self.timestamp = result.timestamp
                            self.latitude = result.latitude
                            self.longitude = result.longitude
                            self.lat = result.lat
                            self.lat_dir = result.lat_dir
                            self.lon = result.lon
                            self.lon_dir = result.lon_dir
                            self.gps_qual = result.gps_qual
                            self.num_sats = result.num_sats
                            self.horizontal_dil = result.horizontal_dil
                            self.altitude = float(result.altitude or 0.0)
                            self.altitude_units = result.altitude_units
                            self.geo_sep = float(result.geo_sep or 0.0)
                            self.geo_sep_units = result.geo_sep_units
                            self.age_gps_data = result.age_gps_data
                            self.ref_station_id = result.ref_station_id
                            if wait_for == "GGA":
                                return True

                # Geographic Lat/Lon (Loran holdover)
                elif type(result) == pynmea2.GLL: #$--GLL,llll.ll,a,yyyyy.yy,a,hhmmss.ss,A*hh<CR><LF>
                    logger.debug("GLL: " + str(result))
                    if result.status is not None:
                        if waitforfix and result.status == 'A':
                            self.latitude = result.latitude
                            self.longitude = result.longitude
                            self.lat = result.lat
                            self.lat_dir = result.lat_dir
                            self.lon = result.lon
                            self.lon_dir = result.lon_dir
                            self.timestamp = result.timestamp
                            self.status = result.status
                            self.faa_mode = result.faa_mode
                            if wait_for == "GLL":
                                return True
                        if not waitforfix:
                            self.latitude = result.latitude
                            self.longitude = result.longitude
                            self.lat = result.lat
                            self.lat_dir = result.lat_dir
                            self.lon = result.lon
                            self.lon_dir = result.lon_dir
                            self.timestamp = result.timestamp
                            self.status = result.status
                            self.faa_mode = result.faa_mode
                            if wait_for == "GLL":
                                return True

                # GPS DOP and active satellites
                elif type(result) == pynmea2.GSA: #$--GSA,a,a,x,x,x,x,x,x,x,x,x,x,x,x,x,x,x.x,x.x,x.x*hh<CR><LF>
                            logger.debug("GSA: " + str(result))
                            #self.mode_fix_type = result.mode_fix_type
                            self.pdop = result.pdop
                            self.hdop = result.hdop
                            self.vdop = result.vdop
                            if wait_for == "GSA":
                                return True

                # Position, velocity and time
                elif type(result) == pynmea2.RMC: #$--RMC,hhmmss.ss,A,llll.ll,a,yyyyy.yy,a,x.x,x.x,xxxx,x.x,a*hh<CR><LF>
                    logger.debug("RMC: " + str(result))
                    if result.status is not None:
                        if waitforfix and result.status == 'A':
                            self.timestamp = result.timestamp
                            self.status = result.status
                            self.latitude = result.latitude
                            self.longitude = result.longitude
                            self.lat = result.lat
                            self.lat_dir = result.lat_dir
                            self.lon = result.lon
                            self.lon_dir = result.lon_dir
                            self.speed_over_ground = result.spd_over_grnd
                            self.mag_variation = result.mag_variation
                            self.mag_var_dir = result.mag_var_dir
                            self.datetimestamp = result.datetime
                            if wait_for == "RMC":
                                return True
                        elif not waitforfix:
                            self.timestamp = result.timestamp
                            self.status = result.status
                            self.latitude = result.latitude
                            self.longitude = result.longitude
                            self.lat = result.lat
                            self.lat_dir = result.lat_dir
                            self.lon = result.lon
                            self.lon_dir = result.lon_dir
                            self.speed_over_ground = result.spd_over_grnd
                            self.mag_variation = result.mag_variation
                            self.mag_var_dir = result.mag_var_dir
                            self.datetimestamp = result.datetime
                            if wait_for == "RMC":
                                return True



                # Track made good and speed over ground
                elif type(result) == pynmea2.VTG: #$--VTG,x.x,T,x.x,M,x.x,N,x.x,K*hh<CR><LF>
                            logger.debug("VTG: " + str(result))
                            self.true_track = result.true_track
                            self.true_track_sym = result.true_track_sym
                            self.mag_track = result.mag_track
                            self.mag_track_sym = result.mag_track_sym
                            self.spd_over_grnd_kts = result.spd_over_grnd_kts
                            self.spd_over_grnd_kts_sym = result.spd_over_grnd_kts_sym
                            self.spd_over_grnd_kmph = result.spd_over_grnd_kmph
                            self.spd_over_grnd_kmph_sym = result.spd_over_grnd_kmph_sym
                            self.faa_mode = result.faa_mode
                            if wait_for == "VTG":
                                return True

                # SVs in view, PRN, elevation, azimuth and SNR
                elif type(result) == pynmea2.GSV: #$--GSV,x,x,x,x,x,x,x,...*hh<CR><LF>
                    logger.debug("GSV: " + str(result))
                    if wait_for == "GSV":
                        return True


                # ProprietarySentence handles boot up output such as "$PMTK011,MTKGPS*08"
                elif type(result) == pynmea2.ProprietarySentence:
                    # TODO If we implement sending commands *to* the GPS,
                    # they should not be permitted until after receiving this sequence
                    # $PMTK011,MTKGPS*08 Successful bootup
                    # $PMTK010,001*2E    Startup
                    # $PMTK010,002*2D    Wake from standby, normal operation
                    logger.debug("ProprietarySentence:" + str(result))
                    if wait_for == "":
                        return True

                else:
                    # If native MTK support exists, check for those message types
                    # requires merge and release of: https://github.com/Knio/pynmea2/pull/111
                    # TODO Drop this special case when #111 is merged & released
                    try:
                        if type(result) in (
                            pynmea2.types.proprietary.mtk.MTK011,
                            pynmea2.types.proprietary.mtk.MTK010
                        ):
                            print(sentence)
                            if wait_for == "":
                                return True
                    except AttributeError:
                        pass
                    raise RuntimeError("Unsupported message type {type} ({sentence})".format(type=type(result), sentence=sentence))

            raise TimeoutError("Timeout waiting for {wait_for} message.".format(wait_for=wait_for))
        except TimeoutError as ex:
            raise TimeoutError(str(ex))
        except IOError as ex:
            raise IOError(str(ex))
        except Exception as ex:
            logger.exception("Unhandled Exception :" + str(ex))


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.DEBUG)
        gps = PA1010D()
        # request firmware version
        gps.send_command(b'PMTK605')

        timeout=1
        waitforfix=True

        nema_type="GGA"


        # These are NMEA extensions for PMTK_314_SET_NMEA_OUTPUT 
        # Turn off everything:
        gps.send_command(b'PMTK314,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')

        if nema_type=="GGA" or nema_type=="RMC" or nema_type=="VTG":
            # Turn on the basic GGA, RMC and VTG info (what you typically want)
            gps.send_command(b'PMTK314,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
        # Turn on just minimum info (GLL only):
        #gps.send_command(b'PMTK314,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
        # Turn on just minimum info (RMC only):
        # gps.send_command(b'PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
        # Turn on just minimum info (VTG only):
        #gps.send_command(b'PMTK314,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
        # Turn on just minimum info (GGA only):
        # gps.send_command(b'PMTK314,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
        # Turn on just minimum info (GSA only):
        #gps.send_command(b'PMTK314,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
        #Turn on just minimum info (GSV only):
        #gps.send_command(b'PMTK314,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0')
        #Turn on everything
        #gps.send_command(b'PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0')

        
        result=False
        while True:
            try:
                result = gps.update(nema_type, timeout, waitforfix)
            except TimeoutError as ex:
                logger.debug(f"{ex}")
                continue
            except IOError as ex:
                logger.error("Could not access PA1010D on I2C bus")
                break
            if result:
                if nema_type == "RMC":
                    #logger.debug("Time: " + gps.timestamp.strftime("%H:%M:%S") + " DateTime: " + gps.datetimestamp.strftime("%d/%m/%Y %H:%M:%S") + " Status: " + gps.status + " Longitude: " + str(gps.longitude) + "long dir: " + gps.lon_dir + " Latitude: " + str(gps.latitude) + " latitude dir "+ gps.lat_dir + "Altitude: " + str(gps.altitude) + "Geoid_Sep: " + gps.geo_sep )
                    #+ "Geoid_Alt: " + str(float(gps.altitude)) + str(float(gps.geo_sep)))
                    print(f"""
        Time:      {gps.timestamp}
        DateTime:  {gps.datetimestamp}
        Status:    {gps.status}
        Longitude: {gps.lon} {gps.lon_dir}
        Latitude:  {gps.lat} {gps.lat_dir}
        Longitude: {gps.longitude: .5f}
        Latitude:  {gps.latitude: .5f}
        """)
                if nema_type == "GGA":
                    #logger.debug("Time: " + gps.timestamp.strftime("%H:%M:%S") + " Longitude: " + str(gps.longitude) + "long dir: " + gps.lon_dir + " Latitude: " + str(gps.latitude) + " latitude dir "+ gps.lat_dir + " Altitude: " + str(gps.altitude) + " Geoid_Sep: " + str(gps.geo_sep) + "Geoid_Alt: " + str(float(gps.altitude) + -float(gps.geo_sep)) + " Horiz_dil: " + str(gps.horizontal_dil) + " Used Sats: " + str(gps.num_sats)  + " Quality: " + str(gps.gps_qual))
                    print(f"""
        Time:      {gps.timestamp}
        Longitude: {gps.lon} {gps.lon_dir}
        Latitude:  {gps.lat} {gps.lat_dir}
        Longitude: {gps.longitude: .5f}
        Latitude:  {gps.latitude: .5f}
        Altitude:  {gps.altitude} {gps.altitude_units}
        Geoid_Sep: {gps.geo_sep} {gps.geo_sep_units}
        Geoid_Alt: {(float(gps.altitude) + -float(gps.geo_sep)): .1f}
        Horiz_dil: {gps.horizontal_dil}
        Used Sats: {gps.num_sats}
        Quality:   {gps.gps_qual}
        Aged:      {gps.age_gps_data}
        RefStation:{gps.ref_station_id}
        """)
                if nema_type == "VTG":
                    print(f"""
        true track:     {gps.true_track} {gps.true_track_sym}
        magnetic track: {gps.mag_track} {gps.mag_track_sym}
        Speed over ground
        knots:              {gps.spd_over_grnd_kts} {gps.spd_over_grnd_kts_sym}
        kilometer per hour: {gps.spd_over_grnd_kmph} {gps.spd_over_grnd_kmph_sym}
        faa_mode:  {gps.faa_mode}
        """)

            time.sleep(1.0)
    except IOError as ex:
        logger.error("Could not access PA1010D on I2C bus")
    except (KeyboardInterrupt, SystemExit):
        exit
    except Exception as ex:
        logger.exception("Unhandled Exception: " + str(ex))
