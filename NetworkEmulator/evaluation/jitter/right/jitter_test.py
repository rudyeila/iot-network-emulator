

'''
1. Create ping function 
2. Store all RTT values of ping 
3. make note of applied delay and jitter value 

In the graph 

x-axis denotes elapsed time 
y-axis denotes the RTT value 

Line for lower RTT value (delay - jitter)
Line for higher RTT value (delay + jitter)
Plot RTT values against the x-axis 
'''

import pingparsing 
import requests 
import json
import subprocess

def get_cmd(commandString):
	return commandString.split(" ")

def scp(source, destination, flag=None):
	if flag==None:
		subprocess.call(get_cmd("scp {} core@10.0.2.7:{}".format(source, destination)))
	else:
		subprocess.call(get_cmd("scp {} {} core@10.0.2.7:{}".format(flag, source, destination)))


def update_jitter(node1, node2, delay=None, jitter=None):
	if delay == None:
		url = 'http://10.0.2.7:5000/topology/links?node1={}&node2={}&jitter={}'.format(node1,node2,jitter)
	elif jitter == None:
		url = 'http://10.0.2.7:5000/topology/links?node1={}&node2={}&delay={}'.format(node1,node2,delay)
	else:
		url = 'http://10.0.2.7:5000/topology/links?node1={}&node2={}&delay={}&jitter={}'.format(node1, node2, delay, jitter)

	response = requests.request('PUT', url)

def main():
	delay = 10000 # 100 ms 
	jitter = 2000 # 50 ms
	left = "left"
	right = "right"
	switch = "switch"
	
	update_jitter(left, right, delay)
	update_jitter(right, switch, delay, jitter)

	parser = pingparsing.PingParsing()
	transmitter = pingparsing.PingTransmitter()
	transmitter.destination = "10.0.0.20"
	transmitter.timestamp = True
	transmitter.ping_option = '-i 0.5'
	transmitter.deadline = 60

	ping = transmitter.ping()
	stats = parser.parse(ping.stdout)
	print(json.dumps(stats.as_dict(), indent=4))

	destination_file = "ping_results2.txt"
	# write to file
	with open(destination_file, mode='w+') as f:
		stat_dict = stats.as_dict()
		count = stat_dict['packet_receive']
		mdev = stat_dict['rtt_mdev']
		
		f.write("{}\n{}\n{}\n{}\n{}\n".format(transmitter.deadline, count, mdev, delay/1000, jitter/1000))
		for icmp_reply in stats.icmp_replies:
			#print(icmp_reply)
			timestamp = icmp_reply['timestamp']
			seq = icmp_reply['icmp_seq']
			time = icmp_reply['time']
			#output = "{},{},{}\n".format(timestamp, seq, time)
			output = "{},{}\n".format(timestamp, time)
			f.write(output)

if __name__ == '__main__':
	main()


