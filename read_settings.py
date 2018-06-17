# read settings.json which is saved by rpi-webinterface
#!/usr/bin/env python3

import json
import io
from pathlib import Path


def get_settings():
    filename = "/var/www/html/backend/settings.json"
    my_file = Path(filename)
    settings = {}

    try:
        my_abs_path = my_file.resolve()
    except FileNotFoundError:
        # doesn"t exist => default values
        settings["button_pin"] = 17

    else:
        # exists => read values from file
        with io.open(filename, encoding="utf-8") as data_file:
            settings = json.loads(data_file.read())

        return settings

# get sensors by type
def get_sensors(type):
	settings = get_settings()
	try:
		all_sensors = settings["sensors"]
	except TypeError:
		# doesn"t exist => return empty array
		return []
		
	sensors = [x for x in all_sensors if x["type"] == type]
	# not found => return empty array
	if len(sensors) < 1:
		return []
	else:
		return sensors
