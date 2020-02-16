#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import io
import json
from pathlib import Path
from utilities import settingsFile

# read settings.json which is created by rpi-webinterface
def get_settings():
    settings = {}

    try:
        my_file = Path(settingsFile)
        my_abs_path = my_file.resolve()
    except:
        # FileNotFoundError: doesn't exist => default values
        settings["button_pin"] = 16
        settings["w1gpio"] = 11
        settings["interval"] = 0
        settings["debug"] = True
        settings["offline"] = 0
        settings["shutdownAfterTransfer"] = False
        # Write these settings to file
        write_settings(settings)

    else:
        # File exists => read values from file
        try:
            with io.open(settingsFile, encoding="utf-8") as data_file:
                settings = json.loads(data_file.read())
        except:
        # FileReadError / json.loads Error  => default values
            settings["button_pin"] = 16
            settings["w1gpio"] = 11
            settings["interval"] = 0
            settings["debug"] = True
            settings["offline"] = 0
            settings["shutdownAfterTransfer"] = False
            # Write these settings to file
            write_settings(settings)
    settings = validate_settings(settings)
    return settings

# function to migrate settings and check the setting file
def validate_settings(settings):
    updateSettingsFile = False

    try:
        settings["button_pin"] = int(settings["button_pin"])
        if not settings["button_pin"]:
            raise Exception("button_pin is not defined.")
    except:
        settings["button_pin"] = 16
        updateSettingsFile = True

    try:
        if not 'debug' in settings:
            settings["debug"] = False
    except:
        settings["debug"] = False
        updateSettingsFile = True

    try:
        if not 'shutdownAfterTransfer' in settings:
            settings["shutdownAfterTransfer"] = 0
    except:
        settings["shutdownAfterTransfer"] = 0
        updateSettingsFile = True

    try:
        settings["offline"]
    except KeyError:
        settings["offline"] = 0
        updateSettingsFile = True

    # Migrate v0.1.1 to v1.0 (Multi-Channel)
    try:
        settings['ts_channels'][0]["ts_channel_id"]
        settings['ts_channels'][0]["ts_write_key"]
    except:
        try:
            settings["ts_channel_id"]
            print("Old Channel ID to be imported " + str(settings["ts_channel_id"]))
            settings["ts_write_key"]
            print("Old write key to be imported " + settings["ts_write_key"])
            ts_channel = {}
            ts_channel['ts_channel_id']= settings["ts_channel_id"]
            ts_channel['ts_write_key'] = settings["ts_write_key"]
            ts_channels = []
            ts_channels.append(ts_channel)
            settings['ts_channels'] = ts_channels
            updateSettingsFile = True
        except:
            settings["ts_channels"] = None

    if updateSettingsFile:
        print("Info: Settings have been changed because of version migration.")
        write_settings(settings)

    return settings

# get sensors by type
def get_sensors(settings, type):
    try:
        all_sensors = settings["sensors"]
    except:
        # Key doesn't exist => return empty array
        return []

    sensors = [x for x in all_sensors if x["type"] == type]
    # not found => return empty array
    if len(sensors) < 1:
        return []
    else:
        return sensors

def write_settings(settings):
    try:
        # write values to file
        outfile = open(settingsFile, "w")
        outfile.write(json.dumps(settings, indent=4, sort_keys=True))
        outfile.close()
        return True
    except Exception as ex:
        print("write_settings " + str(ex))

    return False
