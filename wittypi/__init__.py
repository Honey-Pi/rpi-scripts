# For relative imports to work in Python 3.6
import os, sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

#from .wittyPi import clear_startup_time, clear_shutdown_time, getAll, schedule_file_lines2schedule_file_data, verify_schedule_data
from .wittyPi import local_tz, is_rtc_connected, wittyPiPath, is_schedule_file_in_use, schedule_file_lines2schedule_file_data, get_schedule_file, process_schedule_data, stringtime2timetuple, calcTime, set_shutdown_time, clear_shutdown_time, set_startup_time, clear_startup_time, getAll, verify_schedule_data, system_to_rtc, rtc_to_system, set_power_cut_delay, set_dummy_load_duration, set_default_state, set_pulsing_interval, set_white_led_duration, send_sysup, get_alarm_flags, check_alarm_flags, clear_alarm_flags, do_shutdown, add_halt_pin_event
from .runScript import runscript
