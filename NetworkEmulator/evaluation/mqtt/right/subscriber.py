#!/usr/bin/python

import sys
import time
from datetime import datetime, timedelta

import paho.mqtt.client as mqtt
import json
import requests

''' 
        test idea1
Add a sequence to the messages 
Communciate with a public MQTT broker.
Calculate the time duration to the publisher
Average the times - Use this average as a delay value
Calculate the standard deviation
Use that as a jitter value
Emulate the connection

        test idea2 
Similar to test idea 1, but instead of simply applying the delay and jitter
Make note of the times for each measurement and create a tracefile
and emulate the connection quality using the scheduler by applying delays
Show the two plots next to each other as a comparison 

'''
sequences = []
durations = []

output_file = ""


def run_cmd(name, command, wait):

    command = command.replace(' ', '+')
    url = 'http://10.0.2.7:5000/topology/nodes/term?name={}&command={}&wait={}'.format(name, command, wait)
    response = requests.request('PUT', url)
    print(response)

def write_to_file(file):
    with open(file, 'w+') as f:
        for seq, dur in zip(sequences, durations):
            f.write("{} {}\n".format(seq,dur))    

def on_message(client, userdata, message):
    receipt_time = datetime.now()
    print("processing message")
    json_payload = str(message.payload.decode("utf-8"))
   # print(type(json_payload))

    payload = json.loads(json_payload)
    print(payload)

    seq = int(payload['seq'])
    #delay = payload['delay']
    sending_time = str(payload['sending_time'])
    sending_time = datetime.strptime(sending_time, "%Y-%m-%d %H:%M:%S.%f")
    duration = (receipt_time - sending_time).total_seconds()*1000


    print("sequence = {}".format(seq))
    print("transport duration = {} ms".format(duration))

    with open(output_file, 'a+') as f:
        f.write("{} {}\n".format(seq,duration))  

    print("message content=", str(message.payload.decode("utf-8")))

    print ''

def mqtt_emulated(args):
    global output_file
    output_file = "results7.txt"
    with open(output_file, 'w+') as f:
        f.close()
    client_name = "subscriber"
    broker_address = "10.0.0.1"
    broker_port = 1883

    command1 = "ping 10.0.0.20 -c 1"
    command2 = "ping 10.0.0.21 -c 1"
    command3 = "mosquitto"

    # ping left and right from broker and start mosquitto
    for cmd in [command1, command2]:
        run_cmd("broker", cmd, wait=True)

    run_cmd("broker", command3, wait=False)

    time.sleep(2)

    client = mqtt.Client(client_name)
    client.connect(broker_address)

    for topic in args:
        print("Subscribing to topic: {}".format(topic))
        client.subscribe(topic, qos=0)

    if not args:
        print("Subscribing to topic: time")
        client.subscribe("broker", qos=0) 

    client.on_message = on_message

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        client.disconnect
        client.loop_stop()


def mqtt_public(args):
    global output_file
    output_file = "results5.txt"
    with open(output_file, 'w+') as f:
        f.close()
    client_name = "subscriber"
    #broker_address = "test.mosquitto.org" # "10.0.0.1"
    broker_address = "broker.hivemq.com"
    broker_port = 1883


    client = mqtt.Client(client_name)
    client.connect(broker_address)

    for topic in args:
        print("Subscribing to topic: {}".format(topic))
        client.subscribe(topic, qos=0)

    if not args:
        print("Subscribing to topic: time")
        client.subscribe("time", qos=0) 

    client.on_message = on_message

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        client.disconnect
        client.loop_stop()

    #write_to_file("results.txt")


if __name__ == "__main__":
    args = sys.argv[1:]
    #mqtt_public(args)
    mqtt_emulated(args)