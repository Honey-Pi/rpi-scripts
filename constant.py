#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.


import logging
logger = logging.getLogger('HoneyPi.constant')

homeFolder = '/home/pi'
honeypiFolder = homeFolder + '/HoneyPi'
scriptsFolder = honeypiFolder + '/rpi-scripts'
backendFolder = '/var/www/html/backend'
settingsFile = backendFolder + '/settings.json'
logfile = scriptsFolder + '/error.log'
wittypi_scheduleFileName = "/schedule.wpi"
wittypi_scheduleFile = backendFolder + wittypi_scheduleFileName
timeToStopMaintenance = 4800
GPIO_BTN = 16
GPIO_LED = 21

import datetime
local_tz = datetime.datetime.utcnow().astimezone().tzinfo