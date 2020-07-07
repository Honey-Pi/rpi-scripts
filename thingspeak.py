import requests
from utilities import wait_for_internet_connection, error_log, clean_fields
import thingspeak # Source: https://github.com/mchwalisz/thingspeak/

def transfer_all_channels_to_ts(ts_channels, ts_fields, server_url, debug):
    connectionErrorWithinAnyChannel = []
    for (channelIndex, channel) in enumerate(ts_channels, 0):
        channel_id = channel["ts_channel_id"]
        write_key = channel["ts_write_key"]
        if channel_id and write_key:
            if debug :
                print('Channel ' + str(channelIndex) + ' with ID ' + str(channel_id))
            ts_fields_cleaned = clean_fields(ts_fields, channelIndex, debug)
            if ts_fields_cleaned:
                connectionError = upload_single_channel(write_key, ts_fields_cleaned, server_url, debug)
                connectionErrorWithinAnyChannel.append(connectionError)
            else:
                error_log("Warning: No ThingSpeak data transfer because no fields defined for Channel " + str(channelIndex))
        else:
            error_log("Warning: No ThingSpeak upload for this channel (" + str(channelIndex) + ") because because channel_id or write_key is None.")

    return any(c == True for c in connectionErrorWithinAnyChannel)

def upload_single_channel(write_key, ts_fields_cleaned, server_url, debug):
    # do-while to retry failed transfer
    retries = 0
    MAX_RETRIES = 3
    isConnectionError = True
    while isConnectionError:
        try:
            thingspeak_update(write_key, ts_fields_cleaned, server_url)
            if debug:
                error_log("Info: Data succesfully transfered to ThingSpeak.")
            # break because transfer succeded
            isConnectionError = False
            break
        except requests.exceptions.HTTPError as errh:
            error_log(errh, "Warning: Propaply a wrong ThingSpeak WRITE API-Key.")
        except requests.exceptions.ConnectionError as errc:
            pass
        except requests.exceptions.Timeout as errt:
            error_log(errt, "Error: Timeout Error")
        except requests.exceptions.RequestException as err:
            error_log(err, "Error: Something Else")
        except Exception as ex:
            error_log(ex, "Error: Exception while sending Data")
        finally:
            if isConnectionError:
                retries+=1
                # Break after 3 retries
                if retries > MAX_RETRIES:
                    break
                error_log("Warning: Waiting 15 seconds for internet connection to try transfer again (" + str(retries) + "/" + str(MAX_RETRIES) + ")...")
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
