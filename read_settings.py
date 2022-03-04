#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import io
import json
import os
from pathlib import Path
from constant import settingsFile, logfile, wittypi_scheduleFile
import logging
from pwd import getpwuid
from grp import getgrgid

logger = logging.getLogger('HoneyPi.read_settings')

def get_defaults():
    settings = {}
    settings["button_pin"] = 16
    settings["led_pin"] = 21
    settings["w1gpio"] = 11
    settings["debuglevel"] = 20
    settings["debuglevel_logfile"] = 20
    settings["offline"] = 0
    router = {}
    router['enabled'] = False
    router['ssid'] = None
    router['password'] = None
    router['wpa_type'] = 0
    modem = {}
    modem['enabled'] = 0 # default: no surfstick, 1 = hilink, 2 = wvdial
    modem['ttyUSB'] = "ttyUSB0"
    modem['apn'] = "pinternet.interkom.de"
    honeypi = {}
    honeypi['ssid'] = "HoneyPi"
    honeypi['password'] = "HoneyPi!"
    internet = {}
    internet['router'] = router
    internet['honeypi'] = honeypi
    internet['modem'] = modem
    settings["internet"] = internet
    settings['ts_server_url'] = "https://api.thingspeak.com"
    settings["ts_channels"] = []
    ts_channel = {}
    ts_channel['ts_channel_id'] = None
    ts_channel['ts_write_key'] = None
    settings["ts_channels"].append(ts_channel)
    settings["sensors"] = []
    wittyPi = {}
    wittyPi["enabled"] = False
    wittyPi["version"] = 3
    wittyPi["dummyload"] = 0 # off by default
    wittyPi["voltagecheck_enabled"] = False
    # The following wittypi settings are avaiable since v1.3.7 for wittypi3
    wittyPi['default_state'] = 0 # off by default
    wittyPi['power_cut_delay'] = 8 # cuts power after 8seconds
    wittyPi['pulsing_interval'] = 4 # LED blinks every 4 second when powered off
    wittyPi['white_led_duration'] = 100 # LED blinks for 100ms
    lowVoltage = {}
    lowVoltage["enabled"] = True
    lowVoltage["schedule"] = "BEGIN 2022-01-01 06:00:00 \nEND   2035-07-31 23:59:59 \nON   M5 WAIT\nOFF   H23 M55"
    lowVoltage["voltage"] = 11.9
    lowVoltage["shutdownAfterTransfer"] = True
    lowVoltage["interval"] = 1
    wittyPi["low"] = lowVoltage
    normalVoltage = {}
    normalVoltage["enabled"] = False
    normalVoltage["schedule"] = "BEGIN 2022-01-01 00:00:00 \nEND   2035-07-31 23:59:59 \nON   M5 WAIT\nOFF   M10"
    normalVoltage["voltage"] = 12.8
    normalVoltage["shutdownAfterTransfer"] = False
    normalVoltage["interval"] = 600
    wittyPi["normal"] = normalVoltage
    settings['wittyPi'] = wittyPi
    display = {}
    display['enabled'] = False
    display['show_nondefault_password'] = False
    settings['display'] = display
    settings['enable_reset'] = False

    return settings

# read settings.json which is created by rpi-webinterface
def get_settings():
    settings = {}

    try:
        my_file = Path(settingsFile)
        my_abs_path = my_file.resolve()

        if os.path.exists(settingsFile):
            if str(getpwuid(os.stat(settingsFile).st_uid).pw_name) != "www-data":
                os.system("sudo chown www-data " + str(settingsFile))
            if str(getgrgid(os.stat(settingsFile).st_gid).gr_name) != "www-data":
                os.system("sudo chgrp www-data " + str(settingsFile))

        if os.path.exists(wittypi_scheduleFile):
            if str(getpwuid(os.stat(wittypi_scheduleFile).st_uid).pw_name) != "www-data":
                os.system("sudo chown www-data " + str(wittypi_scheduleFile))
            if str(getgrgid(os.stat(wittypi_scheduleFile).st_gid).gr_name) != "www-data":
                os.system("sudo chgrp www-data " + str(wittypi_scheduleFile))

        with io.open(settingsFile, encoding="utf-8") as data_file:
            settings = json.loads(data_file.read())

    except Exception as ex:
        logger.info("Loading default settings because settings.json file does not exist.")
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
        settings["debuglevel_logfile"]
    except:
        # Migrate debuglevellogfile to debuglevel_logfile
        try:
            settings["debuglevel_logfile"] = settings["debuglevellogfile"]
            # Migrate debug to debuglevel
        except:
            try:
                settings["debug"]
                if settings["debug"]:
                    settings["debuglevel_logfile"] = 10
                else:
                    settings["debuglevel_logfile"] = get_defaults()["debuglevel_logfile"]
                updateSettingsFile = True
                #settings.remove("debug")
            except:
                settings["debuglevel_logfile"] = get_defaults()["debuglevel_logfile"]
                updateSettingsFile = True

    try:
        settings["debuglevel"]
    except:
        # Migrate debug to debuglevel
        try:
            settings["debug"]
            if settings["debug"]:
                settings["debuglevel"] = 10
            else:
                settings["debuglevel"] = get_defaults()["debuglevel"]
            updateSettingsFile = True
            #settings.remove("debug")
        except:
            settings["debuglevel"] = get_defaults()["debuglevel"]
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

    # Migrate from v1.0.8-beta
    try:
        settings["internet"]["modem"]
    except:
        settings["internet"]["modem"] = get_defaults()["internet"]["modem"]
        updateSettingsFile = True

    # Migrate v0.1.1 to v1.0 (Multi-Channel)
    try:
        settings['ts_channels'][0]["ts_channel_id"]
        settings['ts_channels'][0]["ts_write_key"]
    except:
        updateSettingsFile = True
        try:
            settings["ts_channel_id"]
            logger.debug("Old Channel ID to be imported " + str(settings["ts_channel_id"]))
            settings["ts_write_key"]
            logger.debug("Old write key to be imported " + settings["ts_write_key"])
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
            logger.debug("Old wittyPi_enabled to be imported: '" + str(settings["wittyPi_enabled"]) + "'")
            settings["wittyPi_script"]
            logger.debug("Old wittyPi_script to be imported: '" + settings["wittyPi_script"] + "'")
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

    # Migrate to version v1.3.7
    try:
        settings["display"]["enabled"]
    except:
        updateSettingsFile = True
        settings["display"] = get_defaults()["display"]
    try:
        settings["enable_reset"]
    except:
        updateSettingsFile = True
        settings["enable_reset"] = get_defaults()["enable_reset"]
    try:
        settings['wittyPi']["dummyload"]
        if settings['wittyPi']["dummyload"] == None:
            updateSettingsFile = True
            settings['wittyPi']["dummyload"] = get_defaults()['wittyPi']["dummyload"]
    except:
        updateSettingsFile = True
        settings['wittyPi']["dummyload"] = get_defaults()['wittyPi']["dummyload"]
    try:
        settings['wittyPi']['default_state']
        if settings['wittyPi']['default_state'] == None:
            updateSettingsFile = True
            settings['wittyPi']['default_state'] = get_defaults()['wittyPi']['default_state']
    except:
        updateSettingsFile = True
        settings['wittyPi']['default_state'] = get_defaults()['wittyPi']['default_state']
    try:
        settings['wittyPi']['power_cut_delay']
        if settings['wittyPi']['power_cut_delay'] == None:
            updateSettingsFile = True
            settings['wittyPi']['power_cut_delay'] = get_defaults()['wittyPi']['power_cut_delay']
    except:
        updateSettingsFile = True
        settings['wittyPi']['power_cut_delay'] = get_defaults()['wittyPi']['power_cut_delay']
    try:
        settings['wittyPi']['pulsing_interval']
        if settings['wittyPi']['pulsing_interval'] == None:
            updateSettingsFile = True
            settings['wittyPi']['pulsing_interval'] = get_defaults()['wittyPi']['pulsing_interval']
    except:
        updateSettingsFile = True
        settings['wittyPi']['pulsing_interval'] = get_defaults()['wittyPi']['pulsing_interval']
    try:
        settings['wittyPi']['white_led_duration']
        if settings['wittyPi']['white_led_duration'] == None:
            updateSettingsFile = True
            settings['wittyPi']['white_led_duration'] = get_defaults()['wittyPi']['white_led_duration']
    except:
        updateSettingsFile = True
        settings['wittyPi']['white_led_duration'] = get_defaults()['wittyPi']['white_led_duration']

    if updateSettingsFile:
        logger.warning("Settings have been changed because of version migration.")
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
        outfile = open(settingsFile, "w+")
        outfile.write(json.dumps(settings, indent=4, sort_keys=True))
        outfile.close()
        return True
    except Exception as ex:
        logger.exception("Exception in function write_settings")

    return False
