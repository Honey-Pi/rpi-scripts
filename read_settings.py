# read settings.json which is saved by rpi-webinterface
import json
from pathlib import Path


def get_settings():
    filename = "./settings/settings.json"
    my_file = Path(filename)
    settings = {}

    try:
        my_abs_path = my_file.resolve()
    except FileNotFoundError:
        # doesn"t exist => default values
        settings["simApn"] = "pinternet.interkom.de"
        settings["simTime"] = 5
        settings["set_reference_unit"] = 92
        settings["sensoren"] = [{"type": 0,
                                 "tsField": "Temperatur",
                                 "time": 5},
                                {"type": 2,
                                 "tsField": "Gewicht",
                                 "time": 5
                                 }]
    else:
        # exists => read values from file
        with open(filename, encoding="utf-8") as data_file:
            settings = json.loads(data_file.read())

        return settings
