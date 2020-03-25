#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import json
import os
import io

from utilities import error_log



def diag():
    # dict with all fields and values which will be tranfered to ThingSpeak later
    ts_fields = {}
    try:
        # load settings
        os.system("sudo ifconfig > /tmp/ifconfig.txt")
        os.system("sudo route > /tmp/route.txt")
        with io.open("/tmp/ifconfig.txt", encoding="utf-8") as data_file:
            ifconfig = data_file.read()
        with io.open("/tmp/route.txt", encoding="utf-8") as data_file:
            route = data_file.read()
        return ifconfig + '\n\n\n' + route

    except Exception as e:
        error_log(e, "Unhandled Exception in diag")

    # Error occured
    return ""

if __name__ == '__main__':
    try:
        print(diag())

    except (KeyboardInterrupt, SystemExit):
        pass

    except Exception as e:
        error_log(e, "Unhandled Exception in diag")
