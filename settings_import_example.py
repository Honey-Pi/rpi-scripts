#!/usr/bin/env python3

from pprint import pprint

from read_settings import get_settings, get_sensors

settings = get_settings()

# liefert sensoren vom Type 0 (DS18b20)
sensors = get_sensors(0)
pprint(sensors)

