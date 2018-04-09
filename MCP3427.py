#!/usr/bin/env/python

import time, io, fcntl
import struct, array

CHANNEL_0 = 0
CHANNEL_1 = 1

CMD_ZERO = b"\0x00"
CMD_RESET = b"\x06"
CMD_LATCH = b"\x04"

CMD_CONVERSATION = b"\x08"

CMD_READ_CH0_16BIT_PGA1 = b"\x88"
CMD_READ_CH0_16BIT_PGA2 = b"\x89"
CMD_READ_CH0_16BIT_PGA4 = b"\x8A"
CMD_READ_CH0_16BIT_PGA8 = b"\x8B"

CMD_READ_CH1_16BIT_PGA1 = b"\xA8"
CMD_READ_CH1_16BIT_PGA2 = b"\xA9"
CMD_READ_CH1_16BIT_PGA4 = b"\xAA"
CMD_READ_CH1_16BIT_PGA8 = b"\xAB"
I2C_SLAVE = 0x0703

#### ITS-90 bit

Rtpw0 = 100.0 #triple point of water in channel 0
a0 = 0.0 #calib coeffs for channel 0
b0 = 0.0
c0 =0.0
Rtpw1 = 100.0 #triple point of water in channel 1
a1 = 0.0 #calib coeffs for channel 1
b1 = 0.0
c1 =0.0

d0 = 439.932854
d1 = 472.41802
d2 = 37.684494
d3 = 7.472018
d4 = 2.920828
d5 = 0.005184
d6 = -0.963864
d7 = -0.188732
d8 = 0.191203
d9 = 0.049025

class i2c(object):
	def __init__(self, device, bus):
		self.fr = io.open("/dev/i2c-"+str(bus), "rb", buffering=0)
		self.fw = io.open("/dev/i2c-"+str(bus), "wb", buffering=0)
		fcntl.ioctl(self.fr, I2C_SLAVE, device)
		fcntl.ioctl(self.fw, I2C_SLAVE, device)
	def write(self, bytes):
		self.fw.write(bytes)
	def read(self, bytes):
		return self.fr.read(bytes)
	def close(self):
		self.fw.close()
		self.fr.close()



class MCP3427(object):
	def __init__(self, address = 0x68):
		self.dev = i2c(address, 1)
		self.max = 32768.0 ##15-bits
		self.vref = 2.048
		self.tolerance_percent = 0.5
		self.reset()
		
	def reset(self):
		self.dev.write(CMD_ZERO)
		self.dev.write(CMD_RESET)
		time.sleep(0.1)
	
	def latch(self):
		self.dev.write(CMD_ZERO)
		self.dev.write(CMD_LATCH)
		time.sleep(0.1)
	
	def conversation(self):
		self.dev.write(CMD_ZERO)
		self.dev.write(CMD_CONVERSATION)
		time.sleep(0.1)
		
	def configure(self, channel = 0):
		if channel == 1:
			self.dev.write(CMD_READ_CH1_16BIT_PGA8)
		else:
			self.dev.write(CMD_READ_CH0_16BIT_PGA8)
		time.sleep(0.1)
			
	def read(self, channel = None):
		if channel != None:
			self.configure(channel)
	
		data = self.dev.read(3)
		buf = array.array("B", data)
	
		status = buf[2]
		result = None
	
		if status & 128 != 128: ##checks ready bit == 0
			result = buf[0] << 8 | buf[1]
		else:
			print("Not ready")
		return result

	def LSBtoDegC(self, LSB = 0, channel = 0):
		if LSB == 0:
			return("Device not connected")
		elif LSB == 65536:
			return("NaN")
		else:
			res = ((4.096 * LSB / 65536)/8) * 1000
			if channel == 1:
				Rtpw = Rtpw1
				a = a1
				b = b1
				c = c1	
			else:
				Rtpw = Rtpw0
				a = a0
				b = b0
				c = c0
			w = res / Rtpw
			dw = a*(w-1)+b*((w-1)**2)+c*((w-1)**3)
			wr = w - dw
			dd1 = d1*((wr-2.64)/1.64)
			dd2 = d2*((wr-2.64)/1.64)**2
			dd3 = d3*((wr-2.64)/1.64)**3
			dd4 = d4*((wr-2.64)/1.64)**4
			dd5 = d5*((wr-2.64)/1.64)**5
			dd6 = d6*((wr-2.64)/1.64)**6
			dd7 = d7*((wr-2.64)/1.64)**7
			dd8 = d8*((wr-2.64)/1.64)**8
			dd9 = d9*((wr-2.64)/1.64)**9
			temp = d0+dd1+dd2+dd3+dd4+dd5+dd6+dd7+dd8+dd9
			return temp
		
		

if __name__ == "__main__":
	adc_main = MCP3427(address = 0x68)
	adc_main.reset()
	while True:
		#adc_main.conversation()
		ch0 = adc_main.read(CHANNEL_0)
		ch1 = adc_main.read(CHANNEL_1) 
		Tch0 = adc_main.LSBtoDegC(LSB = ch0, channel = 0)
		Tch1 = adc_main.LSBtoDegC(LSB = ch1, channel = 1)
		print("Channel 0: Temp: %.3f oC		LSB:%s" % (Tch0,ch0))
		print("Channel 1: Temp: %.3f oC		LSB:%s\n" % (Tch1,ch1))
		#print("Channel 1: %s" % adc_main.read(CHANNEL_1))
		time.sleep(1.0)




