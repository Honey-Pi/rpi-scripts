from pprint import pprint

from read_settings import get_settings

settings = pprint(get_settings())

channel_id = settings["ts_channel_id"]
write_key = settings["ts_write_key"]
pin_dt = settings["sensors"][2]["pin_dt"]
pin_sck = settings["sensors"][2]["pin_sck"]
interval = settings["sensors"][2]
