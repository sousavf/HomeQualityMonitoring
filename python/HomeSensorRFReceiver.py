#!/usr/bin/env python

#
# Home Automation Master RF Receiver
#  

# AQ - AirQuality
# SM - Soil Moisture
# HM - Humidity
# TP - Temperature
# LI - Light Intensity
from __future__ import print_function
import logging
import logging.handlers
import sys
import time
from RF24 import *
import RPi.GPIO as GPIO
import MySQLdb

LOG_FILENAME = "sensors.log"
LOG_LEVEL = logging.INFO

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class MyLogger(object):
        def __init__(self, logger, level):
                """Needs a logger and a logger level."""
                self.logger = logger
                self.level = level

        def write(self, message):
                if message.rstrip() != "":
                        self.logger.log(self.level, message.rstrip())

sys.stdout = MyLogger(logger, logging.INFO)
sys.stderr = MyLogger(logger, logging.ERROR)

logger.info("Starting Soil Moisture Sensor Receiver")

irq_gpio_pin = None

########### USER CONFIGURATION ###########
# See https://github.com/TMRh20/RF24/blob/master/RPi/pyRF24/readme.md

# CE Pin, CSN Pin, SPI Speed

# Setup for GPIO 22 CE and CE0 CSN with SPI Speed @ 8Mhz
#radio = RF24(RPI_V2_GPIO_P1_15, BCM2835_SPI_CS0, BCM2835_SPI_SPEED_8MHZ)

#RPi B
# Setup for GPIO 15 CE and CE1 CSN with SPI Speed @ 8Mhz
#radio = RF24(RPI_V2_GPIO_P1_15, BCM2835_SPI_CS0, BCM2835_SPI_SPEED_8MHZ)

#RPi B+
# Setup for GPIO 22 CE and CE0 CSN for RPi B+ with SPI Speed @ 8Mhz
#radio = RF24(RPI_BPLUS_GPIO_J8_15, RPI_BPLUS_GPIO_J8_24, BCM2835_SPI_SPEED_8MHZ)

# RPi Alternate, with SPIDEV - Note: Edit RF24/arch/BBB/spi.cpp and  set 'this->device = "/dev/spidev0.0";;' or as listed in /dev
radio = RF24(22, 0);


# Setup for connected IRQ pin, GPIO 24 on RPi B+; uncomment to activate
#irq_gpio_pin = RPI_BPLUS_GPIO_J8_18
#irq_gpio_pin = 24

x = None
conn = None

##########################################
def try_read_data(channel=1):
	if radio.available():
		while radio.available():
			try:
				if conn is None:
					#logger.info("Initializing database connection");
					conn = MySQLdb.connect(host="127.0.0.1", user="root", passwd="1017Gv1154", db="sensors_lu")
					x = conn.cursor()
			except:
				logger.error("Unexpected error")
				conn = None

			len = radio.getDynamicPayloadSize()
			receive_payload = radio.read(len)
			print('Got payload size={} value="{}"'.format(len, receive_payload.decode('utf-8')))
            		# First, stop listening so we can talk
            		radio.stopListening()

			# Send the final one back.
			radio.write(receive_payload)
            		print('Sent response.')

	    		soil_moisture_received = receive_payload.decode('utf-8')
	    		soil_moisture = float(soil_moisture_received)
			logger.info(soil_moisture)
			if x is not None:
				x.execute("""INSERT INTO measure (measureDate, sensor_id, soil_moisture) VALUES (%s,%s,%s)""",(time.strftime('%Y-%m-%d %H:%M:%S'),'SM01',soil_moisture))
				conn.commit()

            		# Now, resume listening so we catch the next packets.
            		radio.startListening()

# Communication Pipes
pipes = [0xF0F0F0F0E1, 0xF0F0F0F0D2, 0xF0F0F0F0C2]
min_payload_size = 4
max_payload_size = 32

# Delete payload_size_increments_by = 1
next_payload_size = min_payload_size
inp_role = 'none'
millis = lambda: int(round(time.time() * 1000))

print('Starting Home Automation RF Receiver service')
radio.begin()
radio.enableDynamicPayloads()
radio.setRetries(5,15)
radio.printDetails()

print('Role: Pong Back, awaiting transmission')
# I don't think I need this portion of code here. But to investigate in the future for possible adjustment using IRQ.
if irq_gpio_pin is not None:
	# set up callback for irq pin
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(irq_gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.add_event_detect(irq_gpio_pin, GPIO.FALLING, callback=try_read_data)

radio.openWritingPipe(pipes[1])
radio.openReadingPipe(0,pipes[1])
radio.openReadingPipe(1,pipes[0])
radio.openReadingPipe(2,pipes[2])
radio.startListening()

# forever loop
while 1:
	if irq_gpio_pin is None:
		# no irq pin is set up -> poll it
		try_read_data()
	else:
		# callback routine set for irq pin takes care for reading -
		# do nothing, just sleeps in order not to burn cpu by looping
		time.sleep(1000)

