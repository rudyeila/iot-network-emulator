import os
import subprocess
import threading
import time
from datetime import datetime

import pingparsing

import requests

from apscheduler.schedulers.background import BackgroundScheduler

import argparse

import logging
logging.basicConfig()

counter = 0 
times = []
outputs = []
first_run = True
ping_parser = pingparsing.PingParsing()
transmitter = pingparsing.PingTransmitter()
transmitter.destination = "10.0.0.20"
transmitter.count = 50
transmitter.timestamp = True
transmitter.ping_option  = "-i 0.013"


def get_cmd(commandString):
	return commandString.split(" ")

def parser_ping():
	global transmitter
	return transmitter.ping()


def ping():
	start_time = datetime.now()
	global counter, first_run
	if (first_run == True):
		start_scheduler_on_api()
		first_run = False
		#time.sleep(0.3)

	if (counter < 10):
		#out = subprocess.check_output(get_cmd("ping 10.0.0.20 -c 30 -i 0.020")) # > results/results{}.txt".format(counter)))
		out = parser_ping()
		print(out.stdout)
		global outputs
		outputs.append(out.stdout)
	counter += 1
	end_time = datetime.now()
	delta = end_time-start_time
	times.append([start_time,end_time,delta.total_seconds()])

def write_to_files(path):
	global outputs
	c = 0
	if not os.path.exists(path):
		os.makedirs(path)		

	for out in outputs:
		res_file = "{}/results{}.txt".format(path, c)
		with open(res_file, mode="w+") as f:
			f.write(out)
		c += 1


def start_scheduler_on_api():
	url = 'http://10.0.2.7:5000/scheduler'
	payload = {}
	headers = {}
	response = requests.request('POST', url, headers = headers, data = payload, allow_redirects=False)

def ping_control(number):
	transmitter = pingparsing.PingTransmitter()
	transmitter.destination = "10.0.0.20"
	#transmitter.count = 50
	transmitter.timestamp = True
	transmitter.ping_option  = "-i 0.020"#-i 0.010"
	transmitter.deadline = 1
	outputs = []
	for i in range(0, number):
		print("Control Second {}".format(i))
		result = transmitter.ping()
		outputs.append(result)

	for i in range(0,number):
		with open("control_results/{}.txt".format(i), mode='w+') as f:
			f.write(outputs[i].stdout)


def main(args):
	path = args.path

	scheduler = BackgroundScheduler()

	# run control 
	#ping_control(60)

	start_time = datetime.now()
	job = scheduler.add_job(ping, 'interval', seconds=1, start_date=datetime.now(), max_instances=2)
	scheduler.start()
	print("start: {}\n".format(start_time))

	global counter 
	while (counter < 10):
		time.sleep(0.01)

	job.pause()
	end_time = datetime.now()
	delta = end_time - start_time
	
	write_to_files(path)


	print("end: {}\n".format(end_time))
	print("total seconds: {}\n".format(delta.total_seconds()))

	c = 0
	global times
	for job in times:
		print("Job #{} - start_time={} \t end_time={} \t duration={}".format(c, job[0], job[1], job[2]))
		c += 1

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='name/path of results directory')
	parser.add_argument('--path', '-p', type=str, help='path to results directory')
	args = parser.parse_args()
	main(args)