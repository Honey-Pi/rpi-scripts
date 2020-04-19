#!/usr/bin/env python3
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import json
import os
import io

from utilities import error_log



def diag():
    diag = ""
    try:
        os.system("echo 'ifconfig:\n' > /tmp/diag.txt")
        os.system("sudo ifconfig >> /tmp/diag.txt")
        os.system("echo '\n\nroute:\n' >> /tmp/diag.txt")
        os.system("sudo route >> /tmp/diag.txt")
        os.system("echo '\n\nWLAN0 status:\n' >> /tmp/diag.txt")
        os.system("sudo wpa_cli -i wlan0 status >> /tmp/diag.txt")
        os.system("echo '\n\nlsusb:\n' >> /tmp/diag.txt")
        os.system("sudo lsusb >> /tmp/diag.txt")
        os.system("echo '\n\ndmesg:\n' >> /tmp/diag.txt")
        os.system("sudo dmesg | grep USB >> /tmp/diag.txt")
        os.system("sudo dmesg | grep ttyUSB >> /tmp/diag.txt")
        os.system("echo '\n\nttyUSB*:\n' >> /tmp/diag.txt")
        os.system("sudo ls -la /dev/ttyUSB* >> /tmp/diag.txt")
        os.system("echo '\n\nlog:\n' >> /tmp/diag.txt")
        os.system("sudo grep -a -B 2 -A 2 'usb_modeswitch\|modem\|pppd\|PPP\|ppp0\|ttyUSB0\|wvdial' /var/log/messages >> /tmp/diag.txt")
        with io.open("/tmp/diag.txt", encoding="utf-8") as data_file:
            diag = data_file.read()
        return diag

    except Exception as e:
        error_log(e, "Unhandled Exception in diag")

    # Error occured
    return diag

if __name__ == '__main__':
    try:
        print(diag())

    except (KeyboardInterrupt, SystemExit):
        pass

    except Exception as e:
        error_log(e, "Unhandled Exception in diag")
