#!/usr/bin/env python3
# -*- Coding: utf-8 -*-
# from https://github.com/ShuDiamonds/PCF8591/blob/master/PCF8591.py
###### pin assign
#PCF8591 --------- Raspberry pi3
# SDA ------------ GPIO2/SDA1
# SCL ------------ GPIO3/SCL1
# VCC ------------- 3.3V
# GND ------------- GND
#
######



import wiringpi
import time

class PCF8591:
	def __init__(self, addr):
		wiringpi.wiringPiSetup() #setup wiringpi

		self.i2c = wiringpi.I2C() #get I2C
		self.dev = self.i2c.setup(addr) #setup I2C device

	def LED_ON(self):
		self.i2c.writeReg8(self.dev, 0x40, 0xFF)
		
	def LED_OFF(self):
		self.i2c.writeReg8(self.dev, 0x40, 0x00)
		
	def DAoutput(self,value):
		self.i2c.writeReg8(self.dev, 0x40, value)
		
	def analogRead0(self):
		self.i2c.writeReg8(self.dev, 0x48,0x40)
		self.i2c.readReg8(self.dev,0x48)	#read dummy
		return self.i2c.readReg8(self.dev,0x48)
		
	def analogRead1(self):
		self.i2c.writeReg8(self.dev, 0x48,0x41)
		self.i2c.readReg8(self.dev,0x48)	#read dummy
		return self.i2c.readReg8(self.dev,0x48)
		
	def analogRead2(self):
		self.i2c.writeReg8(self.dev, 0x48,0x42)
		self.i2c.readReg8(self.dev,0x48)	#read dummy
		return self.i2c.readReg8(self.dev,0x48)
	def analogRead3(self):
		self.i2c.writeReg8(self.dev, 0x48,0x43)
		self.i2c.readReg8(self.dev,0x48)	#read dummy
		return self.i2c.readReg8(self.dev,0x48)
	def analogRead(self,pin):
		self.i2c.writeReg8(self.dev, 0x48,0x40+pin)
		self.i2c.readReg8(self.dev,0x48)	#read dummy
		return self.i2c.readReg8(self.dev,0x48)

if __name__ == "__main__":
	pcf8591 = PCF8591(0x48)
	while 1:
		
		print(pcf8591.analogRead0()) #read the Variable register

