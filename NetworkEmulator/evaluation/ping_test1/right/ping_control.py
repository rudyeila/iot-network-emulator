import pingparsing
import json



def ping():
	ping_parser = pingparsing.PingParsing()
	transmitter = pingparsing.PingTransmitter()
	transmitter.destination = "10.0.0.20"
	#transmitter.count = 50
	transmitter.timestamp = True
	transmitter.ping_option  = "-i 0.020"#-i 0.010"
	transmitter.deadline = 1
	outputs = []
	for i in range(0, 3):
		result = transmitter.ping()
		outputs.append(result)

	for i in range(0,3):
		with open("control_results/{}.txt".format(i), mode='w+') as f:
			f.write(outputs[i].stdout)


def main():
	ping()

if __name__ == "__main__":
	main()