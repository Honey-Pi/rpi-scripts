# For relative imports to work in Python 3.6
import os, sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

#from .wittyPi import clear_startup_time, clear_shutdown_time, getAll, schedule_file_lines2schedule_file_data, verify_schedule_data
from .wittyPi import local_tz, is_rtc_connected, wittyPiPath, is_schedule_file_in_use, schedule_file_lines2schedule_file_data, get_schedule_file, process_schedule_data, stringtime2timetuple, calcTime, set_shutdown_time, clear_shutdown_time, set_startup_time, clear_startup_time, getAll, verify_schedule_data, system_to_rtc
from .runScript import runscript
