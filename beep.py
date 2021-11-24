#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

"""
value_key   value   definition unit formula before storing remark
time    Unix timestamp in seconds number converted to integer value optional, if not defined: server unix timestamp at moment of reception is used
t   temperature °C
t_i temperature inside °C
h   humidity %RH
p   air pressure mbar
w   weight sum kg
l   light lux
bv  bat volt milli Volt
w_fl    weight front left arbitrary value weight_kg += (w_fl - w_fl_offset)*w_fl_kg_per_val The calibration function in the app sets the offset and kg_per_val
w_fr    weight front right arbitrary value weight_kg += (w_fr - w_fr_offset)*w_fr_kg_per_val The calibration function in the app sets the offset and kg_per_val
w_bl    weight back left arbitrary value weight_kg += (w_bl - w_bl_offset)*w_bl_kg_per_val The calibration function in the app sets the offset and kg_per_val
w_br    weight back right arbitrary value weight_kg += (w_br - w_br_offset)*w_br_kg_per_val The calibration function in the app sets the offset and kg_per_val
w_v weight combined kg kg weight_kg = (w_v - sensor_offset)*kg_per_value Use four variables above, or w_v (not both)
s_fan_4 sound fanning 4days arbitrary value
s_fan_6 sound fanning 6days arbitrary value
s_fan_9 sound fanning 9days arbitrary value
s_fly_a sound flying adult arbitrary value
s_tot   sound total arbitrary value
s_bin098_146Hz  frequency bin count arbitrary value
s_bin146_195Hz  frequency bin count arbitrary value
s_bin195_244Hz  frequency bin count arbitrary value
s_bin244_293Hz  frequency bin count arbitrary value
s_bin293_342Hz  frequency bin count arbitrary value
s_bin342_391Hz  frequency bin count arbitrary value
s_bin391_439Hz  frequency bin count arbitrary value
s_bin439_488Hz  frequency bin count arbitrary value
s_bin488_537Hz  frequency bin count arbitrary value
s_bin537_586Hz  frequency bin count arbitrary value
calibrating_weight  weight value to calibrate raw sensor values kg Weight value in kg 'waiting' for the next measurement values to calibrate (if set)
w_fl_kg_per_val raw weight sensor calibration factor kg / arbitrary value
w_fr_kg_per_val raw weight sensor calibration factor kg / arbitrary value
w_bl_kg_per_val raw weight sensor calibration factor kg / arbitrary value
w_br_kg_per_val raw weight sensor calibration factor kg / arbitrary value
w_fl_offset raw weight sensor zero-offset value arbitrary value
w_fr_offset raw weight sensor zero-offset value arbitrary value
w_bl_offset raw weight sensor zero-offset value arbitrary value
w_br_offset raw weight sensor zero-offset value arbitrary value
bc_i bee    count in amount of bees
bc_o bee    count out amount of bees
bc_tot bee  count total amount of bees
weight_kg   weight kg kg see above calculations
weight_kg_corrected weight kg corrected kg = weight_kg - factor * temperature factor is to be defined, based on each sensors' temperature dependency
rssi    received signal strength dBm
snr signal to noise ratio dB
"""

import requests
import logging
import json
from utilities import wait_for_internet_connection

logger = logging.getLogger('HoneyPi.beep')


headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'User-Agent': 'HoneyPi'}

def upload_single_sensor(key, data, server_url='https://api.beep.nl'):
    # do-while to retry failed transfer
    retries = 0
    MAX_RETRIES = 3
    isConnectionError = True
    isKeyOrDataError = False
    while isConnectionError:
        try:
            sensor_update(key, data, server_url)
            logger.info("Data succesfully transfered to ThingSpeak.")
            # break because transfer succeded
            isConnectionError = False
            break
        except requests.exceptions.HTTPError as errh:
            status_code = errh.response.status_code
            if status_code == 401:
                logger.warning('Propaply a wrong Beep Sensor-Key. ' + repr(errh))
                isKeyOrDataError = True
            elif status_code == 400:
                logger.warning('No Beep Sensor-Key provided. ' + repr(errh))
                isKeyOrDataError = True
            elif status_code == 500:
                logger.warning('Error in Data to be transfered. ' + repr(errh))
                isKeyOrDataError = True
            else:
                logger.warning('HTTPError in Data transfer to Beep. ' + repr(errh))
            break
        except requests.exceptions.ConnectionError as errc:
            pass
        except requests.exceptions.Timeout as errt:
            logger.error('Error: Timeout Error' + repr(errt))
        except requests.exceptions.RequestException as err:
            logger.error('Error: Something Else' + repr(err))
        except Exception as ex:
            logger.error('Error: Exception while sending Data '+ repr(ex))
        finally:
            if isConnectionError and not isKeyOrDataError:
                retries+=1
                # Break after 3 retries
                if retries > MAX_RETRIES:
                    break
                logger.warning("Waiting 15 seconds for internet connection to try transfer again (" + str(retries) + "/" + str(MAX_RETRIES) + ")...")
                wait_for_internet_connection(15)

    return isConnectionError

def sensor_update(key, data, server_url='https://api.beep.nl', timeout=None, fmt='json'):
    url = server_url + '/api/sensors'
    if data is not None and len(data) > 0:
        if key is not None and len(key) > 0:
            data['key'] = key
            r = requests.post(url, data=json.dumps(data), headers=headers)
            r.raise_for_status()
            if fmt == 'json':
                return r.json()
            else:
                return r.text
        else:
            print('No sensor key provided!')
    else:
        print('No Data to transfer!')
