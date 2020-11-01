import sys, os, subprocess
sys.path.insert(0,'../')

import matplotlib.pyplot as plt
import numpy as np
import pingparsing
import json
import math
from datetime import datetime

from natsort import natsorted, natsort_keygen, ns

import argparse

from parser import Parser

def graph_duplicate(filePath):
	values = [20,40,60,80,100]
	loss = []
	# get data
	with open(filePath, mode='r') as f:
		for line in f:
			print(line)
			loss.append(float(line))

	fig, ax = plt.subplots()
	x = np.arange(1,6,1)
	#step =  ax.step(x, values, 'x'where='post', label='Artificial Packet Duplication Rate (Percent)')
	rects1 = ax.bar(x, values, align='edge', width=-0.45, label='Expected Packet Duplication Rate (Percent)')
	rects2 = ax.bar(x, loss, align='edge', width=0.45, color='coral', label='Measured Packet Duplication Rate (Percent)')
	rectangules = [rects1, rects2]
	# Attach a text label above each bar in *rects*, displaying its height.
	for rects in rectangules:
		for rect in rects:
			height = rect.get_height()
			ax.annotate('{}'.format('%.2f' % height),
						xy=(rect.get_x() + rect.get_width() / 2, height),
						xytext=(0, 3),  # 3 points vertical offset
						textcoords="offset points",
						ha='center', va='bottom')

	#ax.set_yticks(np.arange(0, max(values)+10, 20))

	plt.xlabel('Test Number', fontsize=20)
	plt.ylabel('Packet Duplication Rate in Percent', fontsize=54)
	plt.title("Packet Duplication Rate Test using Echo Request/Reply")
	plt.legend()
	fig.tight_layout()
	plt.show()


def graph_loss(filePath):
	values = [20,40,60,80,100]
	loss = []
	# get data
	with open(filePath, mode='r') as f:
		for line in f:
			print(line)
			loss.append(float(line))

	fig, ax = plt.subplots()
	x = np.arange(1,6,1)
	rects1 = ax.bar(x, values, align='edge', width=-0.4, label='Expected Packet Loss Rate (Percent)')
	rects2 = ax.bar(x, loss, align='edge', width=0.4, color='coral', label='Measured Packet Loss Rate (Percent)')
	rectangules = [rects1, rects2]
    # Attach a text label above each bar in *rects*, displaying its height.
	for rects in rectangules:
	    for rect in rects:
	        height = rect.get_height()
	        ax.annotate('{}'.format('%.2f' % height),
	                    xy=(rect.get_x() + rect.get_width() / 2, height),
	                    xytext=(0, 3),  # 3 points vertical offset
	                    textcoords="offset points",
	                    ha='center', va='bottom')

	#ax.set_yticks(np.arange(0, max(values)+10, 20))

	plt.xlabel('Test Number')
	plt.ylabel('Packet Loss Rate in Percent')
	plt.title("Packet Loss Rate Test using Echo Request/Reply")
	plt.legend()
	fig.tight_layout()
	plt.show()

def graph_bandwidth(filePath):
	values = []
	bandwidth = []
	# get data
	with open(filePath, mode='r') as f:
		for line in f:
			value, bw = line.split(':')
			values.append(float(value))
			bandwidth.append(float(bw))

	x = np.arange(1,9,1)
	fig, ax = plt.subplots()
	rects1 = ax.bar(x, values, align='edge', width=0.4, label='Artificial Bandwidth Limit (MB/s)')
	rects2 = ax.bar(x, bandwidth, align='edge', width=-0.4, color='coral', label='Measured Bandwidth (MB/s)')
	rectangules = [rects1, rects2]

    # Attach a text label above each bar in *rects*, displaying its height.
	for rects in rectangules:
	    for rect in rects:
	        height = rect.get_height()
	        ax.annotate('{}'.format(int(round(height))),
	                    xy=(rect.get_x() + rect.get_width() / 2, height),
	                    xytext=(0, 3),  # 3 points vertical offset
	                    textcoords="offset points",
	                    ha='center', va='bottom')

	ax.set_yticks(np.arange(0, max(values)+10, 5))

	plt.xlabel('Test Number')
	plt.ylabel('Bandwidth in MB/S')
	plt.title("Bandwidth Test using iperf3")
	plt.legend()
	fig.tight_layout()
	plt.show()


def graph_ping(left_y, left_x, right_y, right_x, factor):
	# plot
	fig, ax1 = plt.subplots()
	ax2 = ax1.twinx()
	print("times = {}".format(left_x))
	print("delay_values = {}".format(left_y))
	lns1 = ax1.step(left_x, left_y, '-rx', label='Artificial Delay', where='post')
	print("ping_times = {}".format(right_x))
	print("rtt_averages = {}".format(right_y))
	lns2 = ax2.plot(right_x, right_y, 'bo', label='Ping Round Trip Time (RTT)')
	plt.title("Echo Request/Reply after Adding Artificial Delay")

	# axis labels
	ax1.set_ylabel('Artificial Delay (ms)', color='r')
	ax1.set_xlabel("Time (seconds)")
	ax1.tick_params(axis='y', colors='red')

	ax2.set_ylabel('Ping Round Trip Time RTT (ms)', color='b')
	ax2.tick_params(axis='y', colors='blue')

	# legend
	lns = lns1+lns2
	labs = [l.get_label() for l in lns]
	plt.legend(lns, labs, loc=0)

	# scale ticks
	T_f = lambda T_c: T_c*2
	# get left axis limits
	ymin, ymax = ax1.get_ylim()

	# right y scale tick values
	ax2.set_yticks(np.arange(0, max(right_y), factor*2/100))
	# apply function and set transformed values to right axis limits
	ax2.set_ylim((T_f(ymin),T_f(ymax)))
	# left y scale values
	ax1.set_yticks(np.arange(min(left_y), max(left_y)+1, factor/100))
	# x scale tick values
	ax1.xaxis.set_ticks(np.arange(0, 11, 1))

	fig.tight_layout()
	plt.show()

def set_up_ping(path_dir, num, factor):
	event_parser = Parser()
	events = event_parser.parse_events('ping_test1/ping_test1_events.yml')

	delay_values = []
	times = []

	for event in events:
		execution_time = event.execution_delay
		link_ops = event.linkOptions
		delay_value = link_ops.delay

		times.append(float(execution_time))
		delay_values.append(float(delay_value/factor))

	ping_times = []
	for time, delay in zip(times, delay_values):
		ping_times.append(float(time)+0.5)
		print("Execution at {} seconds --- delay = {}".format(time, delay))

	parser = pingparsing.PingParsing()
	rtt_averages = []
	#path = os.getcwd() + '/results'
	temp = False
	for filename in sorted(os.listdir('ping_test1/results_ping1')):
		#open_path = path + '/' + filename
		open_path = 'ping_test1/results_ping1' + '/' + filename
		with open(open_path, 'r') as f:
			file_string = f.read()
			stats = parser.parse(file_string)
			if (temp == False):
				temp = True
				for icmp_reply in stats.icmp_replies:
					print(icmp_reply["timestamp"])
			rtt_avg = stats.rtt_avg
			rtt_averages.append(rtt_avg)

	for rtt in rtt_averages:
		print(rtt)
	graph_ping(delay_values, times, rtt_averages, ping_times, factor)

def graph_ping_control():
	seconds = []
	rtt = []

	parser = pingparsing.PingParsing()

	# get data
	natsort_key1 = natsort_keygen(key=lambda y: y.lower())
	directory = os.listdir('ping_test1/control_results')
	directory.sort(key=natsort_key1)
	for filename in directory:
		open_path = 'ping_test1/control_results' + '/' + filename
		with open(open_path, mode='r') as f:
			seconds.append(int(os.path.basename(f.name).split('.')[0])) # get rid of .txt and add the number to the list
			content = f.read()
			stats = parser.parse(content)
			rtt_avg = stats.rtt_avg
			rtt.append(rtt_avg)

	for s, r in zip(seconds,rtt):
		print("{}: {}".format(s,r))

	# calc average
	sum = 0
	for x in rtt:
		sum += x
	avg = sum/len(rtt)
	print("average = {}".format(avg))
	total_average = [avg for i in range(0, len(rtt))]

	fig, ax = plt.subplots()
	plot = ax.plot(seconds, rtt, label='Average Round Trip Time Every Second(ms)')
	ax.plot(seconds, total_average, label='Average Across all RTTs')
	ax.set_yticks(np.arange(0.5, max(rtt)+0.5, 0.1))

	plt.xlabel('Second')
	plt.ylabel('Average Round Trip Time (ms)')
	plt.title("Average Delay without Artificial Disturbances")
	plt.legend()
	fig.tight_layout()
	plt.show()

def graph_jitter(path=None):
	# get RTT values
	rtt = []
	elapsed_times = []
	duration = 0
	count = 0
	mdev = 0
	lines = None
	file_path = ""
	if path == None:
		file_path = "jitter/ping_results.txt"
	else:
		file_path = path

	with open(file_path, 'r') as f:
		lines = f.readlines()

	duration = lines[0]
	count = float(lines[1])
	mdev = float(lines[2])
	delay = float(lines[3])
	jitter = float(lines[4])
	first_timestamp = lines[5].split(',')[0]
	first_timestamp = datetime.strptime(first_timestamp, "%Y-%m-%d %H:%M:%S.%f")
	for i in range(5, len(lines)):
		timestamp, rtt_value = lines[i].split(',')
		timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
		elapsed_time = timestamp-first_timestamp
		#print(elapsed_time.total_seconds())
		elapsed_times.append(elapsed_time.total_seconds())
		rtt.append(float(rtt_value))

	latency = [(delay*2) for i in range(0, len(rtt))]
	RTT_max = [(delay*2 + jitter) for i in range(0, len(rtt))]
	RTT_min = [(delay*2 - jitter) for i in range(0, len(rtt))]

	# count outliers
	counter = 0
	for v in rtt:
		if (v > (delay*2 + jitter) or v < (delay*2 - jitter)):
			counter += 1
	ratio = counter/count
	print(counter)
	print(ratio)


	fig, ax = plt.subplots()
	plot = ax.plot(elapsed_times, rtt, label='Measured Round Trip Time (RTT)')
	ax.plot(elapsed_times, latency, label='Latency')
	ax.plot(elapsed_times, RTT_max, label='Maximum Theoretical RTT value')
	ax.plot(elapsed_times, RTT_min, label='Minimum Theoretical RTT value')
	#ax.plot(x, total_average, label='Avera')
	ax.set_xticks(np.arange(0, math.ceil(max(elapsed_times))+5, 5))
	#ax.set_yticks(np.arange(min(rtt)-(min(rtt)%10-25), max(rtt)-max(rtt)%10+25, 25))
	ax.set_yticks(np.arange(round(min(rtt)), round(max(rtt)), 5))

	plt.xlabel('Elapsed Time (seconds)', fontsize=14)
	plt.ylabel('Round Trip Time (ms)', fontsize=14)
	plt.title('Jitter Measurement with Delay={}ms and Jitter={}ms'.format(int(delay), int(jitter)), fontsize=15)
	plt.legend()
	fig.tight_layout()
	plt.show()

def graph_mqtt(path=None):
	elapsed_times = []
	RTT1 = []
	RTT2 = []



	with open("mqtt/test2/results3.txt", 'r') as f:
		lines = f.readlines()
		for line in lines:
			time, rtt = line.split(" ")
			elapsed_times.append(float(time.strip()))
			RTT1.append(float(rtt.strip()))
	with open("mqtt/test2/results4.txt", 'r') as f:
		lines = f.readlines()
		for line in lines:
			time, rtt = line.split(" ")
			RTT2.append(float(rtt.strip()))

	fig, ax = plt.subplots()
	ax.plot(elapsed_times, RTT2, label='Emulated Scenario')#'Message Transport Duration using an Emulated Broker with Event Scheduling')
	plot = ax.plot(elapsed_times, RTT1, 'x', label='Real-World Scenario')#'Message Transport Duration using a Public Broker')

	#ax.plot(x, total_average, label='Avera')
	ax.set_xticks(np.arange(0, math.ceil(max(elapsed_times))+5, 10))
	#ax.set_yticks(np.arange(min(rtt)-(min(rtt)%10-25), max(rtt)-max(rtt)%10+25, 25))
	min_y = round(min(RTT2))-(round(min(RTT2))%100)+75
	max_y = round(max(RTT2))-(round(max(RTT2))%100)-75
	#plt.yticks(np.arange(float(min_y), float(max_y), 25))

	plt.xlabel('Elapsed Time (seconds)', fontsize=11)
	plt.ylabel('Message Transport Duration (ms)', fontsize=11)
	plt.title('MQTT Measurement #2', fontsize=14)
	plt.legend()
	fig.tight_layout()
	plt.show()



def main(args):
	test_type = args.test
	path_dir = args.path
	num = args.number
	factor = args.factor

	if test_type == "ping":
		set_up_ping(path_dir, num, factor)
	elif test_type == 'ping_control':
		graph_ping_control()
	elif test_type == "bandwidth":
		graph_bandwidth(path_dir)
	elif test_type == "loss":
		graph_loss(path_dir)
	elif test_type == "dup" or test_type == "dupl" or test_type == "duplicate" or test_type == "duplication":
		graph_duplicate(path_dir)
	elif test_type == "jitter":
		graph_jitter(path_dir)
	elif test_type == "mqtt":
		graph_mqtt(path_dir)
	else:
		print("Invalid graph type! Make sure the test type you provided is valid")


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Creates graphs based on tests ran for the evaluation')
	parser.add_argument('--test', '-t', type=str, help='test type which tells the program which graph function to call (ping, bandwidth, etc...)')
	parser.add_argument('--path', '-p', type=str, help='path to results directory')
	parser.add_argument('--number', '-n', type=int, help='ping test number')
	parser.add_argument('--factor', '-f', type=int, default=1000, help='factor to divide values by (e.g. if you want the delay values in the graph to be displayed in millliseconds, provide factor of 1000, since the units are originally in microseconds)')
	parser.print_help()
	args = parser.parse_args()
	main(args)
