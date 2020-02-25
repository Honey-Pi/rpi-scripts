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
    settings["led_pin"] = 21
    settings["w1gpio"] = 11
    # settings["interval"] = 0
    settings["debug"] = True
    settings["offline"] = 0
    # settings["shutdownAfterTransfer"] = False
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
    wittyPilowvoltagesettings = {}
    wittyPilowvoltagesettings["wittyPi_enabled"] = False
    wittyPilowvoltagesettings["wittyPi_script"] = "BEGIN 2015-08-01 06:00:00 \nEND   2025-07-31 23:59:59 \nON   M5\nOFF   H23 M55"
    wittyPilowvoltagesettings["voltage"] = 11.9
    wittyPilowvoltagesettings["shutdownAfterTransfer"] = True
    wittyPilowvoltagesettings["interval"] = 1
    wittyPi["low"] = wittyPilowvoltagesettings
    wittyPinormalvoltagesettings = {}
    wittyPinormalvoltagesettings["wittyPi_enabled"] = False
    wittyPinormalvoltagesettings["wittyPi_script"] = "BEGIN 2015-08-01 00:00:00 \nEND   2025-07-31 23:59:59 \nON   M5\nOFF   M10"
    wittyPinormalvoltagesettings["voltage"] = 13.2
    wittyPinormalvoltagesettings["shutdownAfterTransfer"] = False
    wittyPinormalvoltagesettings["interval"] = 0
    wittyPi["normal"] = wittyPinormalvoltagesettings
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
        settings["led_pin"] = int(settings["led_pin"])
        if not settings["led_pin"]:
            raise Exception("led_pin is not defined.")
    except:
        settings["led_pin"] = get_defaults()["led_pin"]
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
            wittyPinormalvoltagesettings = {}
            wittyPi['wittyPi_enabled']= settings["wittyPi_enabled"]
            wittyPi["wittyPi_voltagecheck_enabled"] = False
            wittyPinormalvoltagesettings["wittyPi_enabled"] = settings["wittyPi_enabled"]
            wittyPinormalvoltagesettings["wittyPi_script"] = settings["wittyPi_script"]
            wittyPinormalvoltagesettings["shutdownAfterTransfer"] = settings["shutdownAfterTransfer"]
            wittyPinormalvoltagesettings["interval"] = settings["interval"]
            wittyPinormalvoltagesettings["voltage"] = get_defaults()["wittyPi"]["normal"]["voltage"]
            wittyPi["normal"] = wittyPinormalvoltagesettings
            wittyPi["low"] = get_defaults()["wittyPi"]["low"]
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
