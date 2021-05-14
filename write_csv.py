#!/usr/bin/env python
# This file is part of HoneyPi [honey-pi.de] which is released under Creative Commons License Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# See file LICENSE or go to http://creativecommons.org/licenses/by-nc-sa/3.0/ for full license details.

import csv
import time
import os, sys
import io
from datetime import datetime
from utilities import scriptsFolder, check_file, clean_fields
import logging

logger = logging.getLogger('HoneyPi.write_csv')



def write_csv(ts_fields, ts_channels, ts_datetime=None):
    try:
        success = True
        for (channelIndex, channel) in enumerate(ts_channels, 0):
            ts_fields_cleaned = clean_fields(ts_fields, channelIndex, False)
            success = write_singlechannel_csv(ts_fields_cleaned, channel['ts_channel_id'], ts_datetime)
        return success
    except Exception as ex:
        logger.exception("Unhandled exception in write_csv")

def write_singlechannel_csv(ts_fields_cleaned, channelId, ts_datetime=None):
    try:
        csv_file = scriptsFolder + '/offline-' + str(channelId) + '.csv'
        # Allowed ThingSpeak fields:
        csv_columns = ['datetime','field1','field2','field3','field4','field5','field6','field7','field8','latitude','longitude','elevation','status']
        check_file(csv_file, 5, 10, 1)

        # Create row with data
        row = {}
        if ts_datetime is not None:
            row['datetime']=ts_datetime
        else:
            row['datetime']=datetime.now()

        for key, value in ts_fields_cleaned.items():
            row[key]=str(value)

        # Write to CSV File
        write_header = (not os.path.isfile(csv_file) or os.stat(csv_file).st_size == 0) # exists or is empty
        with io.open(csv_file, 'a', newline='', encoding='utf8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns, extrasaction='ignore', delimiter = ',', lineterminator='\n')
            if write_header:
                writer.writeheader()  # file doesn't exist yet, write a header
            writer.writerow(row)

        return True
    except IOError as ex1:
        logger.error("IOError in write_singlechannel_csv: " + repr(ex1))
    except Exception as ex:
        logger.exception("Unhandled exception in write_singlechannel_csv")
    return False
