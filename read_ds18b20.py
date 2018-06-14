def get_temperature():
    # read 1-wire slave file
    file = open('/sys/bus/w1/devices/28-000005d2e508/w1_slave')
    file_content = file.read()
    file.close()

    # read temperature and convert temperature
    string_value = file_content.split("\n")[1].split(" ")[9]
    temperature = float(string_value[2:]) / 1000

    return '%6.2f' % temperature
