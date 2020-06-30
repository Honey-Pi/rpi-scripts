#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import io
import json
import os
from pathlib import Path
from utilities import settingsFile, wittypi_scheduleFile, error_log
from pwd import getpwuid
from grp import getgrgid

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
    settings['ts_server_url'] = "http://api.thingspeak.com"
    settings["ts_channels"] = []
    ts_channel = {}
    ts_channel['ts_channel_id'] = None
    ts_channel['ts_write_key'] = None
    settings["ts_channels"].append(ts_channel)
    settings["sensors"] = []
    settings["wittyPi_enabled"] = False #To be removed once Webinterface is updated
    wittyPi = {}
    wittyPi["enabled"] = False
    wittyPi["voltagecheck_enabled"] = False
    lowVoltage = {}
    lowVoltage["enabled"] = False
    lowVoltage["schedule"] = "BEGIN 2015-08-01 06:00:00 \nEND   2025-07-31 23:59:59 \nON   M5 WAIT\nOFF   H23 M55"
    lowVoltage["voltage"] = 11.9
    lowVoltage["shutdownAfterTransfer"] = True
    lowVoltage["interval"] = 1
    wittyPi["low"] = lowVoltage
    normalVoltage = {}
    normalVoltage["enabled"] = False
    normalVoltage["schedule"] = "BEGIN 2015-08-01 00:00:00 \nEND   2025-07-31 23:59:59 \nON   M5 WAIT\nOFF   M10"
    normalVoltage["voltage"] = 12.8
    normalVoltage["shutdownAfterTransfer"] = False
    normalVoltage["interval"] = 0
    wittyPi["normal"] = normalVoltage
    settings['wittyPi'] = wittyPi

    return settings

# read settings.json which is created by rpi-webinterface
def get_settings():
    settings = {}

    try:
        my_file = Path(settingsFile)
        my_abs_path = my_file.resolve()

        if str(getpwuid(os.stat(settingsFile).st_uid).pw_name) != "www-data":
            os.system("sudo chown www-data " + str(settingsFile))
        if str(getgrgid(os.stat(settingsFile).st_gid).gr_name) != "www-data":
            os.system("sudo chgrp www-data " + str(settingsFile))


        # Check wittypi_scheduleFile
        if os.path.exists(wittypi_scheduleFile):
            if str(getpwuid(os.stat(wittypi_scheduleFile).st_uid).pw_name) != "www-data":
                os.system("sudo chown www-data " + str(wittypi_scheduleFile))
            if str(getgrgid(os.stat(wittypi_scheduleFile).st_gid).gr_name) != "www-data":
                os.system("sudo chgrp www-data " + str(wittypi_scheduleFile))

        with io.open(settingsFile, encoding="utf-8") as data_file:
            settings = json.loads(data_file.read())
    except Exception as ex:
        error_log("Warning: Loading default settings because of Error in get_settings " + str(ex))
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
        settings["offline"]
    except:
        settings["offline"] = get_defaults()["offline"]
        updateSettingsFile = True

    # Add since v1.0.8
    try:
        settings["ts_server_url"]
    except:
        settings["ts_server_url"] = get_defaults()["ts_server_url"]
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
        settings['wittyPi']["enabled"]
        settings['wittyPi']["normal"]
    except:
        updateSettingsFile = True
        try:
            settings["wittyPi_enabled"]
            print("Old wittyPi_enabled to be imported: '" + str(settings["wittyPi_enabled"]) + "'")
            settings["wittyPi_script"]
            print("Old wittyPi_script to be imported: '" + settings["wittyPi_script"] + "'")
            wittyPi = {}
            normalVoltage = {}
            wittyPi['enabled']= settings["wittyPi_enabled"]
            wittyPi["voltagecheck_enabled"] = False
            normalVoltage["enabled"] = settings["wittyPi_enabled"]
            normalVoltage["schedule"] = settings["wittyPi_script"]
            try:
                normalVoltage["shutdownAfterTransfer"] = settings["shutdownAfterTransfer"]
            except:
                normalVoltage["shutdownAfterTransfer"] = get_defaults()["wittyPi"]["normal"]["voltage"]["shutdownAfterTransfer"]
            try:
                normalVoltage["interval"] = settings["interval"]
            except:
                normalVoltage["interval"] = get_defaults()["wittyPi"]["normal"]["voltage"]["interval"]
            normalVoltage["voltage"] = get_defaults()["wittyPi"]["normal"]["voltage"]
            wittyPi["normal"] = normalVoltage
            wittyPi["low"] = get_defaults()["wittyPi"]["low"]
            settings['wittyPi'] = wittyPi
        except:
            settings['wittyPi'] = get_defaults()["wittyPi"]

    try:
        settings['wittyPi']["normal"]["shutdownAfterTransfer"]
    except:
        settings['wittyPi']["normal"]["shutdownAfterTransfer"]["shutdownAfterTransfer"] = get_defaults()["wittyPi"]["normal"]["voltage"]["shutdownAfterTransfer"]
    try:
        settings['wittyPi']["low"]["shutdownAfterTransfer"]
    except:
        settings['wittyPi']["low"]["shutdownAfterTransfer"]["shutdownAfterTransfer"] = get_defaults()["wittyPi"]["low"]["voltage"]["shutdownAfterTransfer"]
    try:
        settings['wittyPi']["normal"]["interval"]
    except:
        settings['wittyPi']["normal"]["interval"] = get_defaults()["wittyPi"]["normal"]["voltage"]["interval"]
    try:
        settings['wittyPi']["low"]["interval"]
    except:
        settings['wittyPi']["low"]["interval"] = get_defaults()["wittyPi"]["low"]["voltage"]["interval"]
    try:
        settings['wittyPi']['enabled']
    except:
        settings['wittyPi']['enabled'] = get_defaults()["wittyPi"]["enabled"]
    try:
        settings['wittyPi']["voltagecheck_enabled"]
    except:
        settings['wittyPi']["voltagecheck_enabled"] = get_defaults()['wittyPi']["voltagecheck_enabled"]
    try:
        settings['wittyPi']["normal"]["voltage"]
    except:
        settings['wittyPi']["normal"]["voltage"] = get_defaults()["wittyPi"]["normal"]["voltage"]
    try:
        settings['wittyPi']["low"]["voltage"]
    except:
        settings['wittyPi']["low"]["voltage"] = get_defaults()["wittyPi"]["low"]["voltage"]
    try:
        settings['wittyPi']["normal"]["enabled"]
    except:
        settings['wittyPi']["normal"]["enabled"] = get_defaults()["wittyPi"]["normal"]["enabled"]
    try:
        settings['wittyPi']["low"]["enabled"]
    except:
        settings['wittyPi']["low"]["enabled"] = get_defaults()["wittyPi"]["low"]["enabled"]
    try:
        settings['wittyPi']["normal"]["schedule"]
    except:
        settings['wittyPi']["normal"]["schedule"] = get_defaults()["wittyPi"]["normal"]["schedule"]
    try:
        settings['wittyPi']["low"]["schedule"]
    except:
        settings['wittyPi']["low"]["schedule"] = get_defaults()["wittyPi"]["low"]["schedule"]

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

    sensors = [x for x in all_sensors if "type" in x and x["type"] == type]
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
