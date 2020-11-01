import os
import subprocess
import threading
import time
from datetime import datetime
import numpy as np


import pingparsing
import json
import requests

from apscheduler.schedulers.background import BackgroundScheduler

import argparse

import logging
logging.basicConfig()

counter = 0 
outputs = []
duplicates = []
first_run = True

ping_parser = pingparsing.PingParsing()



def write_to_files(path):
	# c = 0
	# for out in outputs:
	# 	c += 1
	# 	res_file = "{}/results{}.txt".format(path, c)
	# 	with open(res_file, mode="w+") as f:
	# 		f.write(out)

	global duplicates
	with open("duplicates.txt", mode='w+') as f:
		for dup in duplicates:
			f.write("{}\n".format(str(dup)))


def get_cmd(commandString):
	return commandString.split(" ")

def update_loss(value):
	url = 'http://10.0.2.7:5000/topology/links?node1=left&node2=switch&dup={}'.format(value)
	payload = {}
	headers = {}
	response = requests.request('PUT', url)
	#print(response.text)


def ping():
	global counter, outputs
	print("run #{}".format(counter))
	counter += 1
	transmitter = pingparsing.PingTransmitter()
	transmitter.destination = "10.0.0.20"
	transmitter.count = 1000
	transmitter.timestamp = True
	transmitter.ping_option = '-f'

	out = transmitter.ping()

	print(out.stdout)
	outputs.append(out.stdout)
	return out


def main(args):
	global ping_parser
	dupl_values = [20, 40, 60, 80, 100]
	print(dupl_values)

	for i in range (0,5): 		#len(dupl_values)):
		update_loss(dupl_values[i])
		dupl_rate = 0
		for i in range(0,30):
			result = ping()
			parsed = ping_parser.parse(result).as_dict()
			dupl_rate += float(parsed['packet_duplicate_rate'])
			#print(dupl_rate)
		dupl_rate = dupl_rate / 30.0
		global duplicates
		duplicates.append(dupl_rate)

	write_to_files("results")


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='name/path of results directory')
	parser.add_argument('--path', '-p', type=str, help='path to results directory')
	args = parser.parse_args()
	parser.print_help()
	main(args)