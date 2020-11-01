'''
	This module is used to parse both the topology and event config files which are written in YaML.
'''

from core.emulator.emudata import LinkOptions
import logging
import yaml
import utils
from events import LinkEvent, RunCMDEvent, OpenTermEvent
from TopologyConfigurator import InterNode, InterLink


class Parser(object):

    def parse_topology(self, filePath):
        '''
                takes a .yml config file as input
                returns a list of events from type events.LinkEvent ...

                This list would then be given to the scheduler, which would then use the information within the Event to schedule and execute them.
        '''
        with open(filePath, 'r') as f:
            yml = yaml.load_all(f, Loader=yaml.FullLoader)
            netmask = None
            for data in yml:
                topology = data["topology"]
                if ("netmask" in topology):
                    netmask = topology["netmask"]
                nodes = topology["nodes"]  # list of node dictionaries
                links = topology["links"]

                # parse nodes
                yml_nodes = []
                for node in nodes:
                    node_name = node["name"]
                    node_type = node["type"]
                    node_interface = None
                    node_ip = None

                    if ("interface" in node):
                        node_interface = node["interface"]

                    if ("ip" in node):
                        node_ip = node["ip"]
                    yml_node = YML_node(
                        node_name, node_type, node_interface, node_ip)
                    yml_nodes.append(yml_node)

                # parse lins

                yml_links = []
                for link in links:
                    first_node_name = link["node1"]
                    second_node_name = link["node2"]
                    yml_link = YML_link(first_node_name, second_node_name)
                    yml_links.append(yml_link)

        return yml_nodes, yml_links, netmask

    def parse_events(self, filePath):
        '''
                takes a .yml config file as input
                returns a list of events from type events.LinkEvent ...

                This list would then be given to the scheduler, which would then use the information within the Event to schedule and execute them.
        '''
        with open(filePath, 'r') as f:
            yml = yaml.load_all(f, Loader=yaml.FullLoader)
            # print(type(yml))
            events = []
            for data in yml:
                event = data["event"]
                # print(event)
                event_type = event["type"]
                if (event_type == "LinkUpdate" or event_type == "LinkEvent"):
                    scheduler_event = self._get_link_update_event(event)
                elif (event_type == "RunCMD" or event_type == "RunCMDEvent"):
                    scheduler_event = self._get_cmd_event(event)
                elif (event_type == "OpenTerm" or event_type == "OpenTermEvent"):
                    scheduler_event = self._get_open_term_event(event)
                else:
                    raise ValueError(
                        "Event Type {} is unknown".format(event_type))

                events.append(scheduler_event)

        return events

    def _get_open_term_event(self, event):
        '''
                Parse an OpenTermEvent
        '''
        event_type = event["type"]
        time = event["time"]
        time_value, time_unit = self._parse_time(time)
        execution_delay = utils.convert_time_to_seconds(time_value, time_unit)
        parameters = event["parameters"]
        node_name = parameters["node"]
        shell = "/bin/bash"
        if "shell" in parameters:
            shell = parameters["shell"]

        openTermEvent = OpenTermEvent(node_name, execution_delay, shell)
        return openTermEvent

    def _get_cmd_event(self, event):
        '''
                Parse a CMDEvent
        '''
        event_type = event["type"]
        time = event["time"]
        time_value, time_unit = self._parse_time(time)
        execution_delay = utils.convert_time_to_seconds(time_value, time_unit)
        parameters = event["parameters"]
        wait = True
        if "wait" in parameters:
            wait = parameters["wait"]
        node_name = parameters["node"]
        command = parameters["cmd"]

        print("In parser: wait is {}".format(wait))
        runCMDEvent = RunCMDEvent(node_name, command, execution_delay,  wait)
        return runCMDEvent

    def _get_link_update_event(self, event):
        '''
                Parse a LinkEvent
        '''
        event_type = event["type"]
        time = event["time"]
        time_value, time_unit = self._parse_time(time)
        execution_delay = utils.convert_time_to_seconds(time_value, time_unit)
        parameters = event["parameters"]

        node1_name = parameters["node1"]
        node2_name = parameters["node2"]
        link_params = parameters["link_params"]

        linkUpdateEvent = LinkEvent(
            node1_name, node2_name, execution_delay, link_params)
        return linkUpdateEvent

    def _parse_time(self, yml_time):
        '''
                Parse the time parameter of a link. If no time unit is provided, it defaults to seconds.

                Raises a ValueError when invalid parameters are detected.
        '''
        if isinstance(yml_time, int):
            return yml_time, "seconds"
        split_time = yml_time.split(" ")
        if (len(split_time) != 2):
            raise ValueError('''Time input must be of the form: <TimeValue> <TimeUni>
			whereas TimeValue is a number and TimeUnit can be for example seconds, ms, us, ns, minutes, hours etc...
			''')
        time_value = split_time[0]
        time_unit = split_time[1]

        return time_value, time_unit


class YML_node(object):
    '''
            Container object for a node that is parsed from the topology configuration file

            :param name: the name of the node
            :type name: str

            :param type: The type of the node. Currently supported types are (host, physical/rj45, switch, hub and router).
            :type type: str

            :param interface: only required incase of physical nodes. The name of the physical interface to which the external phyiscal computer is connected with the emulator host (e.g. enp0s8)
            :type interface: str

            :param ip: The IP address of the external phyiscal computer. This only serves as a reference to the user and doesn't actually change the IP address.
            :type ip: str
    '''

    def __init__(self, name, type, interface=None, ip=None):
        self.name = name
        self.type = type
        self.interface = interface
        self.ip = ip


class YML_link(object):

    '''
            Container object for a link that is parsed from the topology config file
    '''

    def __init__(self, node1_name, node2_name):
        self.node1_name = node1_name
        self.node2_name = node2_name


if __name__ == "__main__":

    parser = Parser()
    interNodes, interLinks = parser.parse_topology("topology.yml")

    for node in interNodes:
        print(node)
    for link in interLinks:
        print(link)

# events = parseEvent("eventExample.txt")
# for event in events:
# 	event.getLinkOptions()
