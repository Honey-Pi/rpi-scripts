# read temperature from DS18b20 sensor

def get_temperature(device_id):
    # read 1-wire slave file
    file = open('/sys/bus/w1/devices/' + device_id + '/w1_slave')
    file_content = file.read()
    file.close()

    # read temperature and convert temperature
    string_value = file_content.split("\n")[1].split(" ")[9]
    temperature = float(string_value[2:]) / 1000

    return float('%6.2f' % temperature)
