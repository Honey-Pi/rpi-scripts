#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

# read settings.json which is saved by rpi-webinterface
import io
import json
from pathlib import Path

def get_settings():
    filename = "/var/www/html/backend/settings.json"
    my_file = Path(filename)
    settings = {}

    try:
        my_abs_path = my_file.resolve()
    except OSError: # FileNotFoundError
        # doesn"t exist => default values
        settings["button_pin"] = 17
        settings["interval"] = 300

    else:
        # exists => read values from file
        with io.open(filename, encoding="utf-8") as data_file:
            settings = json.loads(data_file.read())

    settings = check_vars(settings)
    return settings

def check_vars(settings):
    try:
        if not settings["button_pin"] or not isinstance(settings["button_pin"], int):
            settings["button_pin"] = 17
    except:
        settings["button_pin"] = 17

    try:
        settings["ts_channel_id"]
        settings["ts_write_key"]
    except KeyError:
        settings["ts_channel_id"] = None
        settings["ts_write_key"] = None

    return settings

# get sensors by type
def get_sensors(settings, type):
    try:
        all_sensors = settings["sensors"]
    except TypeError:
        # doesn"t exist => return empty array
        return []
    except KeyError:
        # doesn"t exist => return empty array
        return []

    sensors = [x for x in all_sensors if x["type"] == type]
    # not found => return empty array
    if len(sensors) < 1:
        return []
    else:
        return sensors