#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import io
import json
from pathlib import Path
from utilities import settingsFile

def get_defaults():
    settings = {}
    settings["button_pin"] = 16
    settings["w1gpio"] = 11
    settings["interval"] = 0
    settings["debug"] = True
    settings["offline"] = 0
    settings["shutdownAfterTransfer"] = False
    router = {}
    router['enabled'] = False
    router['ssid'] = None
    router['password'] = None
    honeypi = {}
    honeypi['ssid'] = "HoneyPi"
    honeypi['password'] = "HoneyPi!"
    internet = {}
    internet['router'] = router
    internet['honeypi'] = honeypi
    settings["internet"] = internet
    settings["ts_channels"] = []
    ts_channel = {}
    ts_channel['ts_channel_id'] = None
    ts_channel['ts_write_key'] = None
    settings["ts_channels"].append(ts_channel)
    settings["sensors"] = []
    settings["wittyPi_enabled"] = False #To be removed once Webinterface is updated
    wittyPi = {}
    wittyPi["wittyPi_enabled"] = False
    wittyPi["wittyPi_voltagecheck_enabled"] = False
    wittyPi["wittyPi_enabled_normal"] = False
    wittyPi["wittyPi_script_normal"] = ""
    wittyPi["wittyPi_voltage_normal"] = 13.2
    wittyPi["wittyPi_enabled_undervoltage"] = False
    wittyPi["wittyPi_script_undervoltage"] = ""
    wittyPi["wittyPi_voltage_undervoltage"] = 11.9
    settings['wittyPi'] = wittyPi

    return settings

# read settings.json which is created by rpi-webinterface
def get_settings():
    settings = {}

    try:
        my_file = Path(settingsFile)
        my_abs_path = my_file.resolve()

        with io.open(settingsFile, encoding="utf-8") as data_file:
            settings = json.loads(data_file.read())
    except:
        # FileNotFoundError: doesn't exist => default values
        # FileReadError / json.loads Error => default values
        settings = get_defaults()
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
        settings["button_pin"] = get_defaults()["button_pin"]
        updateSettingsFile = True

    try:
        settings["debug"]
    except:
        settings["debug"] = get_defaults()["debug"]
        updateSettingsFile = True

    try:
        settings["shutdownAfterTransfer"]
    except:
        settings["shutdownAfterTransfer"] = get_defaults()["shutdownAfterTransfer"]
        updateSettingsFile = True

    try:
        settings["offline"]
    except:
        settings["offline"] = get_defaults()["offline"]
        updateSettingsFile = True

    # Migrate v0.1.1 to v1.0 (Multi-Channel)
    try:
        settings['ts_channels'][0]["ts_channel_id"]
        settings['ts_channels'][0]["ts_write_key"]
    except:
        updateSettingsFile = True
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
        except:
            settings['ts_channels'] = get_defaults()["ts_channels"]

    # Migrate v0.1.1 to v1.0 (WittyPi)
    try:
        settings['wittyPi']["wittyPi_enabled"]
        settings['wittyPi']["wittyPi_script_normal"]
    except:
        updateSettingsFile = True
        try:
            settings["wittyPi_enabled"]
            print("Old WittyPi Status to be imported: '" + str(settings["wittyPi_enabled"]) + "'")
            settings["wittyPi_script"]
            print("Old WittyPi Script to be imported: '" + settings["wittyPi_script"] + "'")
            wittyPi = {}
            wittyPi['wittyPi_enabled']= settings["wittyPi_enabled"]
            wittyPi['wittyPi_enabled_normal']= settings["wittyPi_enabled"]
            wittyPi['wittyPi_script_normal'] = settings["wittyPi_script"]
            wittyPi["wittyPi_voltage_normal"] = 13.2
            wittyPi["wittyPi_enabled_undervoltage"] = False
            wittyPi["wittyPi_script_undervoltage"] = ""
            wittyPi["wittyPi_voltage_undervoltage"] = 11.9
            wittyPi["wittyPi_voltagecheck_enabled"] = False
            settings['wittyPi'] = wittyPi
        except:
            settings['wittyPi'] = get_defaults()["wittyPi"]

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
