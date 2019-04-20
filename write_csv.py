#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import csv
import time
import os, sys
import io
from datetime import datetime
from utilities import scriptsFolder, check_file, error_log

def write_csv(ts_fields):
    try:
        csv_file = scriptsFolder + '/HoneyPi.csv'
        # Allowed ThingSpeak fields:
        csv_columns = ['datetime','field1','field2','field3','field4','field5','field6','field7','field8','latitude','longitude','elevation','status']
        check_file(csv_file, 5, 10)

        # Create row with data
        row = {}
        row['datetime']=datetime.now()
        for key, value in ts_fields.items():
            row[key]=str(value)

        # Write to CSV File
        write_header = (not os.path.isfile(csv_file) or os.stat(csv_file).st_size == 0) # exists or is empty
        with io.open(csv_file, 'a', newline='', encoding='utf8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns, extrasaction='ignore', delimiter = ',', lineterminator='\n')
            if write_header:
                writer.writeheader()  # file doesn't exist yet, write a header
            writer.writerow(row)

    except IOError as ex1:
        error_log(ex1, "Write-CSV IOError")
    except Exception as ex:
        error_log(ex, "Write-CSV Exception")
