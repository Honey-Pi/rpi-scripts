# Installiere alle benötigten Packages
# https://learn.pimoroni.com/tutorial/sandyj/getting-started-with-bme680-breakout
	# dieses package hatte bei mir bei raspbian-lite gefehlt:
	sudo apt-get install python-smbus
	# You'll need to have I2C enabled:
	curl https://get.pimoroni.com/i2c | bash
	
	# Next, in the terminal, type the following to clone the repository and install it
	git clone https://github.com/pimoroni/bme680
	cd bme680/library
	sudo python setup.py install
	
	#To run the example, type the following
	cd /home/pi/bme680/examples
	python read-all.py
	
# https://tutorials-raspberrypi.de/raspberry-pi-temperatur-mittels-sensor-messen/
	
	# Wenn alles entsprechend verkabelt ist, können wir das 1-Wire Protokoll damit aktivieren:
	sudo modprobe w1-gpio
	sudo modprobe w1-therm
	
# https://tutorials-raspberrypi.de/raspberry-pi-waage-bauen-gewichtssensor-hx711/
	# dieses package hatte bei mir auf raspbian-lite gefehlt:
	sudo apt-get install python-numpy
	sudo apt-get install python-rpi.gpio python3-rpi.gpio
	
	git clone https://github.com/tatobari/hx711py