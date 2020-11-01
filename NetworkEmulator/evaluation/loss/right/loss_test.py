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
losses = []
ping_parser = pingparsing.PingParsing()



def write_to_files(path):
	c = 0
	for out in outputs:
		c += 1
		res_file = "{}/results{}.txt".format(path, c)
		with open(res_file, mode="w+") as f:
			f.write(out)

	global losses
	with open("losses.txt", mode='w+') as f:
		for loss in losses:
			f.write("{}\n".format(str(loss)))


def get_cmd(commandString):
	return commandString.split(" ")

def update_loss(value):
	url = 'http://10.0.2.7:5000/topology/links?node1=left&node2=switch&loss={}'.format(value)
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
	loss_values = [20, 40, 60, 80, 100]
	print(loss_values)

	for i in range (0,5): 		#len(loss_values)):
		update_loss(loss_values[i])
		loss = 0
		for i in range(0,30):
			result = ping()
			parsed = ping_parser.parse(result).as_dict()
			loss += float(parsed['packet_loss_rate'])
			#print(dupl_rate)
		loss_rate = loss / 30.0
		print(loss_rate)
		global losses
		losses.append(loss_rate)

	write_to_files("results")


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='name/path of results directory')
	parser.add_argument('--path', '-p', type=str, help='path to results directory')
	args = parser.parse_args()
	parser.print_help()
	main(args)