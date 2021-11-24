import requests
from utilities import wait_for_internet_connection, clean_fields, get_default_gateway_interface_linux, get_ip_address
import logging
import struct
import math

logger = logging.getLogger('HoneyPi.lorawan')

def convert_lorawan(ts_fields):
    try:
        loraWANstring=""
        mumbytespervalue=3
        numfiledsmissingnew = 0
        numfiledsmissing = 0
        for (fieldIndex, field) in enumerate (sorted(ts_fields)):
            hexstr = ""
            fieldNumber = int(field.replace('field',''))
            numfiledsmissing = fieldNumber - (fieldIndex + 1 + numfiledsmissing)
            numfiledsmissingnew = numfiledsmissing
            while numfiledsmissingnew > 0 :
                numfiledsmissingnew = numfiledsmissingnew - 1
                for i in range (mumbytespervalue):
                    hexstr = hexstr + "00"
            loraWANstring = loraWANstring + hexstr
            value = ts_fields[field]*100
            if not isinstance(value, int):
                value = int(value)
            hexstr = str(value.to_bytes(mumbytespervalue, byteorder='big').hex())
            logger.debug(' field: ' + str(field) + ' content: '+ str(ts_fields[field]) + ' Hex: ' + hexstr)
            loraWANstring = loraWANstring + hexstr
        logger.debug('loraWANstring for this channel: '+ loraWANstring)
    except Exception as ex:
        logger.exception("Exception in convert_lorawan")
