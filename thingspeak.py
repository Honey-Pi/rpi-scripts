import requests
from utilities import wait_for_internet_connection, clean_fields, get_default_gateway_interface_linux, get_ip_address
import thingspeak # Source: https://github.com/mchwalisz/thingspeak/
import logging

logger = logging.getLogger('HoneyPi.thingspeak')

def transfer_all_channels_to_ts(ts_channels, ts_fields, server_url, debug):
    try:
        defaultgatewayinterface = get_default_gateway_interface_linux()
        if defaultgatewayinterface == None:
            logger.error('No default gateway, thingspeak upload will end in error!')
            defaultgatewayinterfaceip = ""
        else:
            defaultgatewayinterfaceip = get_ip_address(str(defaultgatewayinterface))
            if defaultgatewayinterfaceip == None:
                defaultgatewayinterfaceip = ""
        connectionErrorWithinAnyChannel = []
        for (channelIndex, channel) in enumerate(ts_channels, 0):
            channel_id = channel["ts_channel_id"]
            write_key = channel["ts_write_key"]
            if channel_id and write_key:
                logger.info('Channel ' + str(channelIndex) + ' with ID ' + str(channel_id) + ' transfer with source IP ' + defaultgatewayinterfaceip + ' using default gateway on ' + str(defaultgatewayinterface))
                ts_fields_cleaned = clean_fields(ts_fields, channelIndex, False)
                if ts_fields_cleaned:
                    connectionError = upload_single_channel(write_key, ts_fields_cleaned, server_url, debug)
                    connectionErrorWithinAnyChannel.append(connectionError)
                else:
                    logger.warning('No ThingSpeak data transfer because no fields defined for Channel ' + str(channelIndex) + ' with ID ' + str(channel_id))
            else:
                logger.warning("No ThingSpeak upload for this channel (" + str(channelIndex) + ") because because channel_id or write_key is None.")

        return any(c == True for c in connectionErrorWithinAnyChannel)
    except Exception as ex:
        logger.exception("Exception in transfer_all_channels_to_ts")

def upload_single_channel(write_key, ts_fields_cleaned, server_url, debug):
    # do-while to retry failed transfer
    retries = 0
    MAX_RETRIES = 3
    isConnectionError = True
    while isConnectionError:
        try:
            thingspeak_update(write_key, ts_fields_cleaned, server_url)
            logger.info("Data succesfully transfered to ThingSpeak.")
            # break because transfer succeded
            isConnectionError = False
            break
        except requests.exceptions.HTTPError as errh:
            logger.warning('Propaply a wrong ThingSpeak WRITE API-Key.' + repr(errh))
        except requests.exceptions.ConnectionError as errc:
            pass
        except requests.exceptions.Timeout as errt:
            logger.error('Error: Timeout Error' + repr(errt))
        except requests.exceptions.RequestException as err:
            logger.error('Error: Something Else' + repr(err))
        except Exception as ex:
            logger.error('Error: Exception while sending Data '+ repr(ex))
        finally:
            if isConnectionError:
                retries+=1
                # Break after 3 retries
                if retries > MAX_RETRIES:
                    break
                logger.warning("Waiting 15 seconds for internet connection to try transfer again (" + str(retries) + "/" + str(MAX_RETRIES) + ")...")
                wait_for_internet_connection(15)

    return isConnectionError

def thingspeak_update(write_key, data, server_url='https://api.thingspeak.com', timeout=None, fmt='json'):
    """Update channel feed.

    Full reference:
    https://mathworks.com/help/thingspeak/update-channel-feed.html
    """
    if write_key is not None:
        data['api_key'] = write_key
    url = '{ts}/update.{fmt}'.format(
        ts=server_url,
        fmt=fmt,
    )
    r = requests.post(url, params=data, timeout=timeout)
    r.raise_for_status()
    if fmt == 'json':
        return r.json()
    else:
        return r.text
