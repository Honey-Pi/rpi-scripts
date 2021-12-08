import requests
from utilities import wait_for_internet_connection, clean_fields, get_default_gateway_interface_linux, get_ip_address
import logging
import struct
import math

from time import sleep
from timeit import default_timer as timer
from traceback import print_exc

from rak811.rak811_v3 import Rak811, Rak811ResponseError, Rak811TimeoutError
from LoRaWAN.ttn_secrets import APP_EUI, APP_KEY

logger = logging.getLogger('HoneyPi.lorawan')

from random import randint

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
        return loraWANstring
    except Exception as ex:
        logger.exception("Exception in convert_lorawan" + repr(ex))

def init_lorawan():
    try:
        lora = Rak811()

        # Most of the setup should happen only once...
        logger.debug('Setup')
        # Ensure we are in LoRaWan mode
        lora.set_config('lora:work_mode:0')
        # Select OTAA
        lora.set_config('lora:join_mode:0')
        # Select region
        lora.set_config('lora:region:EU868')
        # Set keys
        lora.set_config(f'lora:app_eui:{APP_EUI}')
        lora.set_config(f'lora:app_key:{APP_KEY}')
        # Set data rate
        # Note that DR is different from SF and depends on the region
        # See: https://docs.exploratory.engineering/lora/dr_sf/
        # Set Data Rate to 5 which is SF7/125kHz for EU868
        lora.set_config('lora:dr:5')

        # Print config
        for line in lora.get_config('lora:status'):
            logger.debug(f'    {line}')

        logger.debug('Joining')
        start_time = timer()
        join_lorawan(lora)
        logger.debug('Joined in {:.2f} secs'.format(timer() - start_time))
        return lora
    except Rak811TimeoutError as ex:
        logger.error(repr(ex))
    except Rak811ResponseError as ex:
        logger.error(repr(ex))
    except Exception as ex:
        logger.error("Unhandled Exception in init_lorawan" + repr(ex))

def join_lorawan(lora):
    try:
        joined = False
        while not joined:
            try:
                lora.join()
                joined= True
            except Rak811TimeoutError as ex:
                logger.error(repr(ex))
            except Rak811ResponseError as ex:
                logger.error(repr(ex))
    except Exception as ex:
        logger.error("Unhandled Exception in join_lorawan" + repr(ex))

def update_lorawan(lora, port, write_key, ts_fields_cleaned):
    try:
        logger.debug('Sending packet')
        start_time = timer()
        lorastr=convert_lorawan(ts_fields_cleaned)
        #logger.debug(str(lorastr))
        lora.send(lorastr)
        logger.debug('Packet sent in {:.2f} secs'.format(timer() - start_time))

        while lora.nb_downlinks:
            logger.debug('Downlink received', lora.get_downlink()['data'].hex())
    except Rak811TimeoutError as ex:
        logger.error(repr(ex))
    except Rak811ResponseError as ex:
        logger.error(repr(ex))
    except Exception as ex:
        logger.error("Unhandled Exception in update_lorawan" + repr(ex))

if __name__ == '__main__':
    try:
        logging.basicConfig(level=logging.DEBUG)
        lora = init_lorawan()
        
        # Cayenne lpp random value as analog
        port = 1
        write_key="Test"
        
        ts_fields = {}
        ts_fields['field1'] = randint(0, 0x7FFF)
        ts_fields['field2'] = randint(0, 0x7FFF)
        #ts_fields = bytes.fromhex('0102{:04x}'.format(randint(0, 0x7FFF)))
        update_lorawan(lora, port, write_key, ts_fields)

    except (KeyboardInterrupt, SystemExit):
        logger.error("close_script")

    except Exception as ex:
        logger.error("Unhandled Exception in __main__ " + repr(ex))




