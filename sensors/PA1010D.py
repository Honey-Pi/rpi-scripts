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
        "lat_dir",
        "lon_dir",
        "geo_sep",
        "num_sats",
        "gps_qual",
        "status",
        "speed_over_ground",
        "mode_fix_type",
        "pdop",
        "hdop",
        "vdop",
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
        self.num_sats = None
        self.gps_qual = None
        self.status = None

        self.lat_dir = None
        self.lon_dir = None
        self.geo_sep = None

        self.pdop = None
        self.hdop = None
        self.vdop = None

        self.speed_over_ground = None
        self.mode_fix_type = None

    @property

    def data(self):
        return dict((slot, getattr(self, slot)) for slot in self.__slots__)

    def _write_sentence(self, bytestring):
        """Write a sentence to the PA1010D device over i2c.

        We could- in theory- do this in one burst, but since smbus is limited to 32bytes,
        we would have to chunk the message and this is already one byte chunks anyway!

        """
        for char_index in bytestring:
            self._i2c.write_byte(self._i2c_addr, ord(char_index))

    def send_command(self, command, add_checksum=True):
        """Send a command string to the PA1010D.

        If add_checksum is True (the default) a NMEA checksum will automatically be computed and added.

        """
        # TODO replace with pynmea2 functionality
        if command.startswith("$"):
            command = command[1:]
        if command.endswith("*"):
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

    def read_sentence(self, timeout=5):
        """Attempt to read an NMEA sentence from the PA1010D."""
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

    def update(self, wait_for="GGA", timeout=5, waitforfix=False):
        """Attempt to update from PA1010D.

        Returns true if a sentence has been successfully parsed.

        Returns false if an error has occured.

        Will wait 5 seconds for a GGA message by default.

        :param wait_for: Message type to wait for.
        :param timeout: Wait timeout in seconds

        """
        timeout += time.time()

        while time.time() < timeout:
            try:
                sentence = self.read_sentence()
            except TimeoutError:
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
                logger.debug("GGA Quality: " + str(result.gps_qual))
                if result.gps_qual is not None:
                    if waitforfix and result.gps_qual > 0:
                        self.timestamp = result.timestamp
                        self.latitude = result.latitude
                        self.lat_dir = result.lat_dir
                        self.longitude = result.longitude
                        self.lon_dir = result.lon_dir
                        self.gps_qual = result.gps_qual
                        self.num_sats = result.num_sats
                        #Horizontal Dilution of precision
                        self.altitude = result.altitude
                        #Units of antenna altitude, meters
                        self.geo_sep = result.geo_sep
                        #Units of geoidal separation, meters
                        #Age of differential GPS data, time in seconds since last SC104 type 1 or 9 update, null field when DGPS is not used
                        #Differential reference station ID, 0000-1023
                        if wait_for == "GGA":
                            return True
                    elif not waitforfix:
                        self.timestamp = result.timestamp
                        self.latitude = result.latitude
                        self.lat_dir = result.lat_dir
                        self.longitude = result.longitude
                        self.lon_dir = result.lon_dir
                        self.gps_qual = result.gps_qual
                        self.num_sats = result.num_sats
                        #Horizontal Dilution of precision
                        self.altitude = result.altitude
                        #Units of antenna altitude, meters
                        self.geo_sep = result.geo_sep
                        #Units of geoidal separation, meters
                        #Age of differential GPS data, time in seconds since last SC104 type 1 or 9 update, null field when DGPS is not used
                        #Differential reference station ID, 0000-1023
                        if wait_for == "GGA":
                            return True

            # Geographic Lat/Lon (Loran holdover)
            elif type(result) == pynmea2.GLL: #$--GLL,llll.ll,a,yyyyy.yy,a,hhmmss.ss,A*hh<CR><LF>
                logger.debug("GLL: " + str(result))
                logger.debug("GLL Status: " + str(result.status))
                if result.status is not None:
                    if waitforfix and result.status == 'A':
                        self.latitude = result.latitude
                        self.lat_dir = result.lat_dir
                        self.longitude = result.longitude
                        self.lon_dir = result.lon_dir
                        self.timestamp = result.timestamp
                        self.status = result.status
                        #Magnetic Variation, degrees
                        #Magnetic Variation, direction
                        #self.datetimestamp = result.datetime
                        if wait_for == "GLL":
                            return True
                    if not waitforfix:
                        self.latitude = result.latitude
                        self.lat_dir = result.lat_dir
                        self.longitude = result.longitude
                        self.lon_dir = result.lon_dir
                        self.timestamp = result.timestamp
                        self.status = result.status
                        #Magnetic Variation, degrees
                        #Magnetic Variation, direction
                        #self.datetimestamp = result.datetime
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
                logger.debug("RMC Status: " + str(result.status))
                if result.status is not None:
                    if waitforfix and result.status == 'A':
                        self.timestamp = result.timestamp
                        self.status = result.status
                        self.latitude = result.latitude
                        self.lat_dir = result.lat_dir
                        self.longitude = result.longitude
                        self.lon_dir = result.lon_dir
                        self.speed_over_ground = result.spd_over_grnd
                        #Magnetic Variation, degrees
                        #Magnetic Variation, direction
                        self.datetimestamp = result.datetime
                        if wait_for == "RMC":
                            return True
                    elif not waitforfix:
                        self.timestamp = result.timestamp
                        self.status = result.status
                        self.latitude = result.latitude
                        self.lat_dir = result.lat_dir
                        self.longitude = result.longitude
                        self.lon_dir = result.lon_dir
                        self.speed_over_ground = result.spd_over_grnd
                        #Magnetic Variation, degrees
                        #Magnetic Variation, direction
                        self.datetimestamp = result.datetime
                        if wait_for == "RMC":
                            return True



            # Track made good and speed over ground
            elif type(result) == pynmea2.VTG: #$--VTG,x.x,T,x.x,M,x.x,N,x.x,K*hh<CR><LF>
                logger.debug("VTG: " + str(result))
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
                print(sentence)
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
                        return True
                except AttributeError:
                    pass
                raise RuntimeError("Unsupported message type {type} ({sentence})".format(type=type(result), sentence=sentence))

        raise TimeoutError("Timeout waiting for {wait_for} message.".format(wait_for=wait_for))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    gps = PA1010D()
    nema_type="RMC"
    timeout=10
    waitforfix=True
    while True:
        try:
            result = gps.update(nema_type, timeout, waitforfix)
        except TimeoutError:
            continue

        if result:
            if nema_type == "RMC":
                #logger.debug("Time: " + gps.timestamp.strftime("%H:%M:%S") + " DateTime: " + gps.datetimestamp.strftime("%d/%m/%Y %H:%M:%S") + " Status: " + gps.status + " Longitude: " + str(gps.longitude) + "long dir: " + gps.lon_dir + " Latitude: " + str(gps.latitude) + " latitude dir "+ gps.lat_dir + "Altitude: " + str(gps.altitude) + "Geoid_Sep: " + gps.geo_sep )
                #+ "Geoid_Alt: " + str(float(gps.altitude)) + str(float(gps.geo_sep)))
                print(f"""
    Time:      {gps.timestamp}
    DateTime:  {gps.datetimestamp}
    Status:    {gps.status}
    Longitude: {gps.longitude: .5f} {gps.lon_dir}
    Latitude:  {gps.latitude: .5f} {gps.lat_dir}
    """)
            if nema_type == "GGA":
                print(f"""
    Time:      {gps.timestamp}
    Longitude: {gps.longitude: .5f} {gps.lon_dir}
    Latitude:  {gps.latitude: .5f} {gps.lat_dir}
    Altitude:  {gps.altitude}
    Geoid_Sep: {gps.geo_sep}
    Geoid_Alt: {(float(gps.altitude) + -float(gps.geo_sep)): .5f}
    Used Sats: {gps.num_sats}
    Quality:   {gps.gps_qual}""")
        time.sleep(1.0)
