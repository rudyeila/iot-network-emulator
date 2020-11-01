#!/usr/bin/python

'''
	This is the entry point into the network emulator
'''

import sys
from datetime import datetime
import threading
import time
from threading import Timer, Thread
import subprocess
from subprocess import Popen, PIPE
import logging
import atexit


import argparse

import core
from core import load_logging_config
from core.emulator.coreemu import CoreEmu
from core.emulator.emudata import IpPrefixes, NodeOptions, LinkOptions, InterfaceData
from core.emulator.enumerations import NodeTypes, EventTypes, LinkTypes

from api import API
from TopologyConfigurator import Topology
from scheduler import Scheduler
from parser import Parser
import utils


logging.basicConfig(level=logging.DEBUG)


def coreSession(topology, scheduler):
    '''
            This is where the emulation sesseion is actually started. This is run on the seperate thread. See main() below.

    '''
    prefixes = topology.prefixes
    coreemu = topology.coreemu
    session = topology.session

    print(topology)


def run_api(topology, scheduler):
    # starts the API
    # The API takes the topology and scheduler as an input, in order to be able to modify them.
    api = API(topology, scheduler)
    api.run(debug=True)


def main():
    '''
    This is the entry point into the program. The topology, scheduler and API are all instantiated and started here.
    '''
    # Parse commandline arguments
    parser = argparse.ArgumentParser(description='''This is the entry point into the emulator.
	You can either intitalize an empty topology, or use a topology configuration file.
	Furthermore, if you wish, you can provide an event configuration file to schedule the execution of certain jobs at certain times.''')
    parser.add_argument('--topology', '-t', type=str,
                        help='Path to the topology configuration file (optional)')
    parser.add_argument('--events', '-e', type=str,
                        help='Path to the event configuration file (optional)')
    parser.add_argument('--start-scheduler', '-s', nargs="?", const=True, default=1, type=int,
                        help='1 for True (defaults), 0 for False  -  Determines whether the scheduler is immediately started with the program or not. If not, you can start it later from the API. Time zero would be right when the scheduler is started.')
    parser.print_help()
    args = parser.parse_args()

    topologyPath = args.topology
    eventsPath = args.events

    parser = Parser()
    # topology config is provided - Instantiate this topology
    if (topologyPath):
        yml_nodes, yml_links, netmask = parser.parse_topology(topologyPath)
        # netmask is provided - Set custom netmask
        if (netmask != None):
            topology = Topology(yml_nodes, yml_links, netmask)
        else:
            # Otherwise, use default netmask (10.0.0.0/24)
            topology = Topology(yml_nodes, yml_links)
    else:
        # empty topology (no config file)
        topology = Topology()

    # clean up tolopogy when script exists
    atexit.register(topology.shutdown, hard=True)

    events = None
    scheduler = None
    # If the events command line argument is provided, this block is executed
    if (eventsPath):
        print("events are available")
        events = parser.parse_events(eventsPath)  # LinkEvents parsed from file
        scheduler = Scheduler(events, topology)
        # If the flag to start the scheduler on the command line is set to True, then the scheduler is immediately started, otherwise, it isn't.
        if (args.start_scheduler == 1):
            scheduler.schedule_events(events, topology)
            print("\nstart schedule = {}\n".format(args.start_scheduler))
            scheduler.start()
        # Else, you need to start it from the API.

    # Start the the CORE session on a seperate thread.
    coreSessionThread = threading.Thread(
        target=coreSession, name=coreSession, args=[topology, scheduler])
    # , 'port': 5001}) # Custom port for the API, default is 5000
    api_thread = threading.Thread(
        target=run_api, name="api_thread", args=[topology, scheduler])
    api_thread.daemon = True
    api_thread.start()

    coreSessionThread.start()
    try:
        coreSessionThread.join()
    except KeyboardInterrupt:
        topology.shutdown(hard=True)

    print("\nsetup finished\n")

    # Infinite main loop
    while True:
        time.sleep(0.01)

    # shutdown


if __name__ in ["__main__", "__builtin__"]:
    main()
