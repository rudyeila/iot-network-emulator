import os

import iperf3
import requests

def convert_MB_to_bit(numbers, reverse=False):
	ret_list = []

	for number in numbers:
		if reverse:
			n = number / 8000000
		else:
			n = number * 8000000  
	
		ret_list.append(n)
	
	return ret_list


def start_scheduler_on_api():
	url = 'http://10.0.2.7:5000/scheduler'
	payload = {}
	headers = {}
	response = requests.request('POST', url, headers = headers, data = payload, allow_redirects=False)

def write_to_file(path, bandwidth, results):
	with open(path, mode="w+") as f:
		for bw,res in zip(bandwidth,results):
			f.write("{}:{}\n".format(str(bw), str(res.received_MB_s)))

def update_bandwidth(bw):
	url = 'http://10.0.2.7:5000/topology/links?node1=left&node2=switch&bandwidth={}'.format(bw)
	payload = {}
	headers = {}
	response = requests.request('PUT', url)
	#print(response.text)

def run():
	client = iperf3.Client()
	client.duration = 10
	client.server_hostname = '10.0.0.20'
	client.port = 5201
	client.protocol = 'udp'
	

	print('\nConnecting to {0}:{1}'.format(client.server_hostname, client.port))
	result = client.run()
	if result.error:
		print(result.error)
	else:
		print('')
		print('Test completed:')
		#print('  started at         {0}'.format(result.time))
		print('  avg cpu load       {0}%\n'.format(result.local_cpu_total))

		print('Average recieved data in all sorts of networky formats:')
		print('  bits per second      (bps)   {0}'.format(result.bps))	
		print('  Megabits per second  (Mbps)  {0}'.format(result.Mbps))
		print('  Megabyzes per second  (MBps)  {0}'.format(result.MB_s))

	return result 

def main():

	# bandwidth in reverse order
	bandwidth = [1, 5, 10, 20, 30, 40, 50, 60]
	print(bandwidth)
	bandwidth = convert_MB_to_bit(bandwidth)
	#bandwidth.reverse()
	print(bandwidth)
	results = []

	bw_length = len(bandwidth)

	# Run test 8 times, updating the bandwidth each time using the API.
	#start_scheduler_on_api()
	for i in range(0,1):
		update_bandwidth(bandwidth[i])
		results.append(run())
	

	bandwidth.reverse()
	bandwidth = convert_MB_to_bit(bandwidth, reverse=True)
	results.reverse()	
	c = 0
	for res in results:
		print("Run #{}: Average Bandwidth={} MB/s".format(c, res.received_MB_s))
		c += 1

	write_to_file("jitter.iperf", bandwidth, results)	


if __name__ == '__main__':
	main()