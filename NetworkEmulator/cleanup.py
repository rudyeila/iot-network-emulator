#!/usr/bin/python

'''
This script is called when the emulation is interrupted. It cleansup any interfaces created by the program.
'''

import sys
import subprocess
import os
import logging


def cleanup(interfaces):
    #subprocess.call(["sudo", "rm", "-r", "/tmp/pycore.1"])

    # with open("physical_interfaces.txt","r") as f:
    # 	if f.mode == 'r':
    # 		contents = f.read()
    # 	f.close()
    #
    # interfaces = contents.split('\n')
    # interfaces = interfaces[0:-1]
    for interface in interfaces:
        # if its a bridge
        if ("bridge" in interface):
            ifname = interface
        else:
            ifname = "{}OUTveth".format(interface)
        # dont show input on console
        #p = subprocess.call(["sudo", "ip", "link", "del", "dev", ifname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            p = subprocess.check_output(
                ["sudo", "ip", "link", "del", "dev", ifname], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            logging.debug(e.returncode, e.output)

    logging.info("Cleanup finished...")


if __name__ == '__main__':
    cleanup()
