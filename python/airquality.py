#!/usr/bin/env python

import logging
import logging.handlers
import sys
import serial
import time
import smtplib
import MySQLdb
from email.mime.text import MIMEText

LOG_FILENAME = "/var/log/sensors.log"
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

logger.info("Starting quality monitor service.")

ser = serial.Serial('/dev/ttyUSB0',115200)

conn = None

alive_counter = 0

while True:
	try:
		if ser is None:
			ser = serial.Serial('/dev/ttyUSB0',115200)

		if conn is None:
			logger.info("DB Connection is none, lets initialize");
			conn = MySQLdb.connect(host= "127.0.0.1",
                 			user="user",
	                		passwd="password",
        	        		db="table_name")
			x = conn.cursor()
		
		if alive_counter == 10:
			logger.info("I'm alive.");
			alive_counter = 0

		alive_counter = alive_counter + 1
		read_serial=ser.readline()
		full_line = str(read_serial)
		logger.debug(full_line)

		parts = full_line.split(';')

		sensor_id = parts[1]

		ppm = parts[4]
		ppm_float = float(ppm)

		light_intensity = parts[5]
		light_intensity_float = float(light_intensity)

		temperature = parts[7]
		temperature_float = float(temperature)

		humidity = parts[6]
		humidity_float = float(humidity)

		x.execute("""INSERT INTO measure (measureDate, sensor_id, airquality, humidity, temperature, light) VALUES (%s,%s,%s,%s,%s,%s)""",(time.strftime('%Y-%m-%d %H:%M:%S'),sensor_id,ppm_float,humidity_float,temperature_float,light_intensity_float))
	        conn.commit()

	except:
		logger.error("Unexpected error:", sys.exc_info()[0])
		ser = None
		conn = None

