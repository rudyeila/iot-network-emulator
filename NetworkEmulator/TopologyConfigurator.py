'''
    This module is the main control point for the emulator.

    The nodes, links and Topology are all instantiated here as well as the underlying network emulation.

    The Topology class is the interface that can be used to add, remove and modify nodes and links.
    Among other things, the update_link method is used to fluctuate the connection quality of a link.

'''

import os
import logging
import subprocess
import utils
import collections

from core.emulator.coreemu import CoreEmu
from core.emulator.emudata import IpPrefixes, NodeOptions, LinkOptions, InterfaceData
from core.emulator.enumerations import NodeTypes, EventTypes, LinkTypes
import json

from cleanup import cleanup


# a list containing the names of the created virutal interfaces. Used for clean up at the end.
interface_names = []

class Topology(object):

    '''
        This class stores information about the current topology and offers interfaces for controlling it
    '''

    def __init__(self, yml_nodes=None, yml_links=None, netmask="10.0.0.0/24"):
        """
        Constructor for the Topology class - Creates a topology and starts the emulation, if no parameters were provided then an empty topolgy is created.

        :param yml_nodes: a list containing the nodes parsed from the topology configuration file, defaults to None
        :type yml_nodes: list(YML_node), optional

        :param yml_links: a list containing the links parsed from the topology configuration file, defaults to None
        :type yml_links: list(parser.YML_link), optional

        :param netmask: the netmask tells the emulator what sort of IP addresses the virtual nodes should be assigned, defaults to 10.0.0.0/24
        :type netmask: str
        """

        Topology.prefixes = IpPrefixes(ip4_prefix=netmask) #prefixes  # CORE prefixes
        self.coreemu =  globals().get("coreemu", CoreEmu()) # CORE container for sessions
        self.session = self.coreemu.create_session()       # CORE session
        self.flag_physical_node = False
        self.netmask = netmask
        self.interfaceDict = {}
        self.inter_nodes = [] # Nodes from coreNode types
        self.physical_links = {}
        self.list_physical_links = []

        self.session.set_state(EventTypes.CONFIGURATION_STATE)

        self.interNodeObjects = []
        self.interLinkObjects = []


        if (yml_nodes and yml_links):
            self._init_topology(yml_nodes, yml_links)
        else:
            self.session.instantiate()

    def _init_topology(self, yml_nodes, yml_links):
        '''
        Adds the nodes and links from the YML lists to the emulator

        :param yml_nodes: a list containing the nodes parsed from the topology configuration file, defaults to None
        :type yml_nodes: list(YML_node), optional

        :param yml_links: a list containing the links parsed from the topology configuration file, defaults to None
        :type yml_links: list(parser.YML_link), optional

        '''

        # sort the nodes such that the host nodes are initialized at the beginning, then the switches then the physical nodes at the end.
        #yml_nodes.sort(key=lambda x: x.type, reverse=True)
        # initialize nodes
        for yml_node in yml_nodes:
            self.add_node(yml_node.name, yml_node.type, yml_node.interface, yml_node.ip)

        # initialize links
        for yml_link in yml_links:
            first_node_name = yml_link.node1_name
            second_node_name = yml_link.node2_name
            self.add_link(first_node_name, second_node_name, init=True)

        self.session.instantiate()
        for interLinkObj in self.list_physical_links:
            self._set_up_physical_link(interLinkObj)

        for interLinkObj in self.interLinkObjects:
            interLinkObj.first_node.handle_switch_case()
            interLinkObj.second_node.handle_switch_case()



    def add_node(self, node_name, node_type, node_interface=None, node_ip=None):
        '''
        adds a node to the emulator

        :param node_name: the name of the name that needs to be created
        :type node_name: str

        :param node_type: the type of the node to be created. Possible types {rj45, switch, hub, host}
        :type node_type: str

        :param node_interface: the name of the physical interface that needs to be associated with this node. Only required incase of an RJ45 node, defaults to None
        :type node_interface: str, optional

        :param node_ip: the IP address that will be assigne to the node, only required incase of an RJ45 node, defaults to None
        :type node_ip: str, optional

        :return: returns the node that was created and added the emulator
        :rtype: TopologyConfigurator.InterNode
        '''
        if (self.get_node_by_name(node_name)):
            raise ValueError("A node with name \"{}\" already exists in the topology!".format(node_name))

        node = InterNode(node_name, node_type, node_interface, node_ip)
        node.add_node_to_topology(self)

        if (node.is_physical):
            self.flag_physical_node = True

        #self.interNodeObjects.append(node)
        return node



#    def _update_topology(self, interLinkObj):


    def delete_node(self, node_name):
        '''
        Deletes the node with the specified name from the emulator

        :param node_name: the name of the node to be deleted
        :type node_name: str

        :return: A dictionary containing the data of the node that was deleted, this is used by the API.
        :rtype: dict(str)
        '''
        node = self.get_node_by_name(node_name)
        if (not node):
            logging.debug("Node with name {} was not found.".format(node_name))
        else:
            node_links = node.links
            delete_res = node.delete()

            for link in self.interLinkObjects:
                if link in node_links:
                    self.interLinkObjects.remove(link)

            self.interNodeObjects.remove(node)
            self.session.delete_node(node.CORE_node.id)
            #print("{} successfully deleted!".format(node))
            return delete_res


    def add_link(self, first_node_name, second_node_name, init=False):
        '''
        Creates and adds a link between the two specified nodes to the emulator

        :param first_node_name: the name of the first node that is part of the link
        :type first_node_name: str

        :param second_node_name: the name of the second node that is part of the link
        :type second_node_name: str

        :return: the newly created InterLink object
        :rtype: TopologyConfigurator.InterLink
        '''
        if (first_node_name == second_node_name):
            logging.error("You can't create a link between the same node. Node one and node two must be different")
            raise ValueError("You can't create a link between the same node. Node one and node two must be different")
        first_node = self.get_node_by_name(first_node_name)
        second_node = self.get_node_by_name(second_node_name)
        if (first_node == None or second_node == None):
            logging.error("Either {0} or {1} doesn't match the nodes defined in the nodes part of the config file".format(first_node_name, second_node_name))
            raise ValueError("Either {0} or {1} doesn't match the nodes defined in the nodes part of the config file".format(first_node_name, second_node_name))


        # create a link object (This object stores important information about the links)
        interLinkObj = InterLink(first_node, second_node)
        if (interLinkObj in self.interLinkObjects):
            logging.error("A link already exists between {} and {} within the topology".format(first_node_name, second_node_name))
            raise ValueError("A link already exists between {} and {} within the topology".format(first_node_name, second_node_name))
        # Add link object to the topology
        self.interLinkObjects.append(interLinkObj)
        # add variables for easier reference
        first_inter_node = interLinkObj.first_node
        second_inter_node = interLinkObj.second_node
        first_interface = interLinkObj.first_interface
        second_interface = interLinkObj.second_interface


        if (interLinkObj.has_physical == True):
            self.list_physical_links.append(interLinkObj)
            #continue ## handle physical nodes at the end
        else: # No physical nodes in link - Handle directly
            self.session.add_link(first_inter_node.CORE_node.id, second_inter_node.CORE_node.id,
                                  interface_one=first_interface, interface_two=second_interface)
            interLinkObj.is_in_CORE = True
            first_inter_node.interfaces[second_inter_node] = first_interface
            second_inter_node.interfaces[first_inter_node] = second_interface
        # Add the link to each of the nodes
        interLinkObj.first_node.links.append(interLinkObj)
        interLinkObj.second_node.links.append(interLinkObj)

        if (init == False):
            self._update_topology()

        return interLinkObj

    def update_link(self, first_node_name, second_node_name, link_options=None):
        '''
        Updates the link options between the two specified nodes with the provided link_options to the emulator

        :param first_node_name: the name of the first node that is part of the link
        :type first_node_name: str

        :param second_node_name: the name of the second node that is part of the link
        :type second_node_name: str

        :param link_options: The link_options to update the link with. CORE provides a convenience LinkOptions class for this. Defaults to None
        :type link_options:  core.emulator.emudata.LinkOptions, optional

        :return: True if the link was updated succesfully, False otherwise
        :rtype: boolean
        '''

        # get nodes by name
        first_node = self.get_node_by_name(first_node_name)
        second_node = self.get_node_by_name(second_node_name)

        if (first_node == None or second_node == None):
            logging.error("{0} or {1} does not seem to match any known node within the topology".format(first_node_name, second_node_name))
            return False

        # get link between the two nodes (if it exists) - Link exists when the two nodes are directly connected (e.g. not through a switch)
        interLinkObj = self.get_link_by_node_names(first_node.name, second_node.name)
        if (interLinkObj == None):
            # This is the case when a switch connects the two nodes -
            # in this case we update the link between the first node and second but use the interface used to connect node1 with the switch to do so
            logging.debug("Link to be updated: {0} ---- {1}\n".format(first_node.name, second_node.name))

            # Figure out which switch is used to connect the first and the second nodes together
            switch = first_node.reachable_through_switch[second_node]

            # Rertrieve link object that connects the first node with the switch and therefore with the second node
            interLinkObj = first_node.get_inter_link(switch.name)
            if (interLinkObj == None):
                raise ValueError("The two nodes ({} - {}) you provided don't seem to be connected. Neither directly nor through a switch."
                                 .format(first_node.name, second_node.name))

            self.session.update_link(first_node.CORE_node.id, second_node.CORE_node.id,
                                     interface_one_id=interLinkObj.first_interface.id,  link_options=link_options)
            interLinkObj.link_options = link_options
            logging.debug("\nLINK UPDATED! 1\n")
        else:
            # this is the case when the two nodes are directly connected
            ## Case when second node is a switch (no second interface)
            if (interLinkObj.second_node.type == NodeTypes.SWITCH):
                self.session.update_link(interLinkObj.first_node.CORE_node.id, interLinkObj.second_node.CORE_node.id,
                              interface_one_id=interLinkObj.first_interface.id, link_options=link_options)
                interLinkObj.link_options = link_options
                logging.debug("\nLINK UPDATED! 2\n")
            else:
                self.session.update_link(interLinkObj.first_node.CORE_node.id, interLinkObj.second_node.CORE_node.id,
                                         interface_one_id=interLinkObj.first_interface.id, interface_two_id=interLinkObj.second_interface.id,
                                         link_options=linkEvent.linkOptions)
                interLinkObj.link_options = link_options
                logging.debug("\nLINK UPDATED! 3\n")
        logging.debug("Interlink Object = {}".format(interLinkObj))
        #print("Interlink Object = {}".format(interLinkObj))

        logging.info("\nLink between %s and %s is updated with new link options: %s\n" % (interLinkObj.first_node.name, interLinkObj.second_node.name, link_options))
        #print("Link between %s and %s is updated" % (interLinkObj.first_node.name, interLinkObj.second_node.name))
        print("link updated!")
        return True

    def delete_link(self, first_node_name, second_node_name):
        '''
        Deletes the link between the two specified nodes if it exists

        :param first_node_name: the name of the first node that is part of the link
        :type first_node_name: str

        :param second_node_name: the name of the second node that is part of the link
        :type second_node_name: str

        :return: the deleted InterLink object
        :rtype: TopologyConfigurator.InterLink
        '''


        link = self.get_link_by_node_names(first_node_name, second_node_name)
        if link:
            logging.debug("removing link\n {}".format(link))
            self.interLinkObjects.remove(link)

            if link.has_physical:
                self.list_physical_links.remove(link)

            first_interface = link.first_interface
            second_interface = link.second_interface
            if1_id = None
            if2_id = None
            if (first_interface):
                if1_id = first_interface.id
            if (second_interface):
                if2_id = second_interface.id
            self.session.delete_link(link.first_node.CORE_node.id, link.second_node.CORE_node.id, if1_id, if2_id)
            link.delete()
            logging.debug("Successfully removed link")

            # This line was commented when adding the blackbox functionality... i.e. external VMs are able to communicate with the emulator
            #self._update_topology()
        else:
            logging.debug("Link to be removed was not found ({} ----- {})".format(first_node_name, second_node_name))
        return link

    def _update_topology(self):
        # update reachablility
        for interLinkObj in self.interLinkObjects:
            interLinkObj.first_node.handle_switch_case()
            interLinkObj.second_node.handle_switch_case()
        for interLinkObj in self.list_physical_links:
            self._set_up_physical_link(interLinkObj, update=True)



    def _set_up_physical_link(self, interLinkObj, update=False):
    # Handle phyiscal links at the ends, because we want to make sure that all other links have already been created (This saves us trouble)
        if (interLinkObj.first_node.is_physical == True):
            physical_inter_node = interLinkObj.first_node
            second_inter_node = interLinkObj.second_node
            physicalNode  = physical_inter_node.CORE_node
            secondNode = second_inter_node.CORE_node
        else:
            physical_inter_node =  interLinkObj.second_node ## Inter_nodes are the nodes we create (coreNode), not the ones returned by CORE. They contain some useful info for creating links
            second_inter_node = interLinkObj.first_node ## The naming is confusing for now and seems redundant. This will all be refractored and cleaned up later.
            physicalNode = second_inter_node.CORE_node
            secondNode = physical_inter_node.CORE_node

        # handle case where second node is a switch (which has no IP address)
        if (second_inter_node.type == NodeTypes.SWITCH):
            physical_inter_node.handle_switch_case()
            switchConnections = second_inter_node.neighbours
            # add static route entries for all other nodes connected to the switch from our host
            for node in switchConnections:
                node_ip = node.ip_address
                # add route from physical host to node
                subprocess.call(utils.get_cmd_command("sudo ip route add {0}/32 dev {1}".format(node_ip, physical_inter_node.vethOutName)))
    #    else:
            # Add route from host to virtual node -- The other way around can only be added once the session has been instantiated
            # in case of a switch, link to switch will be added here

            subprocess.call(utils.get_cmd_command("sudo ip route add {0}/32 dev {1}".format(second_inter_node.ip_address, physical_inter_node.vethOutName)))
            self.physical_links[physical_inter_node] = second_inter_node
            first_interface = physical_inter_node.interfaces[second_inter_node]
            second_interface = second_inter_node.interfaces[physical_inter_node]

            # Avoid double adding a link when this method is called later.
            if (interLinkObj.is_in_CORE == False):
                self.session.add_link(physical_inter_node.CORE_node.id, second_inter_node.CORE_node.id,
                                  first_interface)#, second_interface)
                logging.debug(interLinkObj)
                interLinkObj.is_in_CORE = True
            # this part sets up the routing tables of the different nodes that are reachable from physical node.
            # This makes sure communication can happen.
        host_ip = utils.get_host_ip()
        nodes_connected_to_physical = []
        if (second_inter_node.type == NodeTypes.SWITCH):
            switch = second_inter_node
            switchConnections = switch.links
            for link in switchConnections: # of type interLinkObj
                first_node = link.first_node
                second_node = link.second_node
                ## Make sure the node isn't the switch itself, and isn't the actual phyiscal node that we are trying to handle
                # In other words, get all nodes that can be reached from the physical node through the switch
                if first_node is not switch and first_node is not physicalNode and first_node.type != NodeTypes.RJ45:
                    if first_node not in nodes_connected_to_physical:
                        nodes_connected_to_physical.append(first_node)
                if second_node is not switch and first_node is not physicalNode and second_node.type != NodeTypes.RJ45:
                    if second_node not in nodes_connected_to_physical:
                        nodes_connected_to_physical.append(second_node)


            for node in nodes_connected_to_physical:
                ## print("second Node {0} with type {1} has dict {2}".format(second))
                node.handle_switch_case()
                interface = node.interfaces[switch]
                command = utils.get_cmd_command("sudo ip route replace {0}/32 dev eth{1}".format(host_ip, interface.id))
                node.CORE_node.client.cmd(command)
    #    self._handle_physical_links()

    def _handle_physical_links(self):
        '''
            this method sets up the routing tables of the different nodes that are reachable from the
            physical node.
            This makes sure communication can happen.
        '''
        ## physicalNode and secondNode are from the inter-core type that I created (Class InterNode())
        for physicalNode, secondNode in self.physical_links.items():
            host_ip = utils.get_host_ip()
            nodes_connected_to_physical = []
            if (secondNode.type == NodeTypes.SWITCH):
                switch = secondNode
                switchConnections = switch.links
                for link in switchConnections: # of type interLinkObj
                    first_node = link.first_node
                    second_node = link.second_node
                    ## Make sure the node isn't the switch itself, and isn't the actual phyiscal node that we are trying to handle
                    # In other words, get all nodes that can be reached from the physical node through the switch
                    if first_node is not switch and first_node is not physicalNode and first_node.type != "rj45":
                        if first_node not in nodes_connected_to_physical:
                            nodes_connected_to_physical.append(first_node)
                    if second_node is not switch and first_node is not physicalNode and second_node.type != "rj45":
                        if second_node not in nodes_connected_to_physical:
                            nodes_connected_to_physical.append(second_node)


            for node in nodes_connected_to_physical:
                ## print("second Node {0} with type {1} has dict {2}".format(second))
                interface = node.interfaces[switch]
                command = utils.get_cmd_command("sudo ip route replace {0}/32 dev eth{1}".format(host_ip, interface.id))
                node.CORE_node.cmd(command)
                ## print("{0} ran following command: {1}".format(node.name, command))
                #ping = utils.get_cmd_command("ping -c 3 {0}".format(host_ip))
                #result = node.CORE_node.client.icmd(command)
                ## print("{0} ran following command: {1}".format(node.name, ping))
                ## print(result)

    def get_node_by_name(self, nodeName):
        '''
        Conveniece method that retrieves the InterNode object belonging to the node with the provided name

        :param nodeName: the name of the node that should be retrieved
        :type nodeName: str

        :return: InterNode object with the specified name
        :rtype: TopologyConfigurator.InterNode
        '''

        for node in self.interNodeObjects:
            if (nodeName.lower() == node.name.lower()):
                return node

    def get_link_by_node_names(self, first_node_name, second_node_name):
        '''
        Conveniece method that retrieves the InterLink object belonging to the link between the two specified node names

        :param first_node_name: the name of the first node that is part of the link
        :type first_node_name: str

        :param second_node_name: the name of the second node that is part of the link
        :type second_node_name: str

        :return: the InterLink object that is associated with the link between the two provided node names
        :rtype: TopologyConfigurator.InterLink
        '''
        for link in self.interLinkObjects:
            if (link.first_node.name.lower() == first_node_name.lower() and
                link.second_node.name.lower() == second_node_name.lower()):
                return link
        #raise ValueError("No link between {} and {} has been found. Make sure you provided the nodes in the right order.".format(first_node_name, second_node_name))

    def get_ip_by_name(self, nodeName):
        node = get_inter_node_by_name(nodeName)
        return node.ip_address


    def get_CORE_nodes(self):
        core_nodes = []
        for node in self.interNodeObjects:
            core_nodes.append(node.CORE_node)

        return core_nodes

    def get_data(self):
        '''
        creates and returns a dictionary containing all of the topology's important data, such as the nodes and the links.

        :return: a dictionary containing information about the topology. This is mainly used by the API.
        :rtype: dict
        '''
        data = collections.OrderedDict()
        nodes_data = []
        for node in self.interNodeObjects:
            node_data = node.get_data(verbose=False)
            nodes_data.append(node_data)
        data['nodes'] = nodes_data

        links_data = []
        for link in self.interLinkObjects:
            link_data = link.get_data()
            links_data.append(link_data)
        data['links'] = links_data
        return data

    def shutdown(self, hard=False):
        '''
        Shutsdown the topology, kills any underlying processes and removes any virtual interfaces and bridges that were created
        if hard is set to True, a hard shutdown is performed. All virtual devices created by the emulator are removed and all processes are killed.
        '''
#        for node in self.interNodeObjects:
#            node.shutdown()
            # if (node.is_physical == True):
            #     ## Remove virtual interfaces
            #     subprocess.call(utils.get_cmd_command("sudo ip link del {0}".format(node.vethInName)))
            #     subprocess.call(utils.get_cmd_command("sudo ip link del {0}".format(node.vethOutName)))
        try:
            self.coreemu.shutdown()
        except CoreCommandError as e:
            print(e)
        global interface_names
        cleanup(interface_names)
        if hard:
            subprocess.call(['core-cleanup'])
        #global session
        #session = self.coreemu.create_session()
        # self.flag_physical_node = False
    	# self.prefixes = None # CORE prefixes
    	# self.coreemu = None # CORE container for sessions
    	# self.session = None       # CORE session
        # self.interfaceDict = {}
        # self.inter_nodes = [] # Nodes from coreNode types
        # self.physical_links = {}
        # self.list_physical_links = []
        # self.interNodeObjects = []
        # self.interLinkObjects = []

    def __str__(self):
        result = 'Netmask = {}\nTopology has the following nodes:\n'.format(self.netmask)
        for node in self.interNodeObjects:
            result += "\tName: {} \tIP: {} \tType: {}/{}\n".format(node.name, node.ip_address, node.type_name, node.type)
        result += "and the following links:\n"
        for link in self.interLinkObjects:
            first_node = link.first_node
            second_node = link.second_node
            result += "\tNode {} ({}) ---------- Node {} ({})\n".format(first_node.name, first_node.ip_address, second_node.name, second_node.ip_address)

        return result



class InterLink(object):
    ''' Container Class for parsed "links" from config file '''
    def __init__(self, first_node, second_node):
        # first node and second are from InterNode type
        self.first_node = first_node
        self.first_interface = None
        self.second_node = second_node
        self.second_interface = None
        self.link_options = LinkOptions()
        self.is_in_CORE = False ## Flag gets set to true when the link is added to the actual underlying CORE session
                                # This is useful later when adding new links from the API and having to update all of the physical connections.
                                # Is used in the _set_up_physical_link method.

        # If either of the nodes is a physical node then set phyiscal flag of the node
        if (self.first_node.is_physical == True or self.second_node.is_physical == True):
            self.has_physical = True
        else:
            self.has_physical = False

        # Add each of the nodes to the others "neighbours" list
        first_node.neighbours.append(second_node)
        second_node.neighbours.append(first_node)


        ## create interface for FIRST node
        if (first_node.type == NodeTypes.RJ45):
            interface_data = InterfaceData(*[None] * 7)
            self.first_interface = interface_data
        elif (first_node.type == NodeTypes.SWITCH):
            self.first_interface = None
            second_node.has_switch_connection = True
        else:
            interface = Topology.prefixes.create_interface(first_node.CORE_node)
            self.first_interface = interface

        # Add interface to the nodes "interface" dictionary - This helps track which interface was used for which link
        first_node.interfaces[second_node] = self.first_interface

        # Repeat for SECOND node
        if (second_node.type == NodeTypes.RJ45):
            interface_data = InterfaceData(*[None] * 7)
            self.second_interface = interface_data
        elif (second_node.type == NodeTypes.SWITCH):
            first_node.has_switch_connection = True
            self.second_interface = None
        else:
            interface = Topology.prefixes.create_interface(second_node.CORE_node)
            self.second_interface = interface

        second_node.interfaces[first_node] = self.second_interface

        # first_node.handle_switch_case()
        # second_node.handle_switch_case()

    def _get_link_options_dict(self):
        data = collections.OrderedDict()
        if (self.link_options.delay):
            data['delay'] = '{} microseconds'.format(self.link_options.delay)
        if (self.link_options.bandwidth):
            data['bandwidth'] = '{} bits per second'.format(self.link_options.bandwidth)
        if (self.link_options.per):
            data['packet_loss_rate'] = '{}%'.format(self.link_options.per)
        if (self.link_options.dup):
            data['packet_duplication_rate'] = '{}%'.format(self.link_options.dup)
        if (self.link_options.jitter):
            data['jitter'] = self.link_options.jitter

        return data

    def get_data(self):
        data = collections.OrderedDict()
        data['first_node'] = self.first_node.name
        data['first_node_ip'] = self.first_node.ip_address
        data['second_node'] = self.second_node.name
        data['second_node_ip'] = self.second_node.ip_address
        data['link_options'] = self._get_link_options_dict()
        return data


    def delete(self):
        logging.debug("removing link\n{}".format(self))
        self.first_node.neighbours.remove(self.second_node)
        del self.first_node.interfaces[self.second_node]
        self.second_node.neighbours.remove(self.first_node)
        del self.second_node.interfaces[self.first_node]

        '''
            remove form node links list!
        '''

        # update reachability based on new setting now.
        if (self.first_node.type == NodeTypes.SWITCH or self.second_node.type == NodeTypes.SWITCH):
            self.first_node.reachable_through_switch = {}
            self.first_node.indirect_neighbours = []
            self.first_node.handle_switch_case()

            self.second_node.reachable_through_switch = {}
            self.second_node.indirect_neighbours = []
            self.second_node.handle_switch_case()
        # if (self.second_node.type == NodeTypes.SWITCH):
        #     reachable_through_switch = self.first_node.reachable_through_switch[self.second_node]
        #     for node in reachable_through_switch:
        #         if node in self.first_node.indirect_neighbours
        #             self.first_node.indirect_neighbours.remove(node)
        logging.debug("Successfully removed link\n{}".format(self))


    def get_first_node(self):
        return self.first_node

    def get_second_node(self):
        return self.second_node

    def __eq__(self, obj):
        return isinstance(obj, InterLink) and obj.first_node == self.first_node and obj.second_node == self.second_node

    def __str__(self):
        return ('''
{0} -------- {1}
Has physical: {2}
First Interface {3} ------ Second Interface {4}
Already in Session? {5}
                    ''').format(self.first_node.name, self.second_node.name, self.has_physical, self.first_interface, self.second_interface, self.is_in_CORE)


class InterNode(object):
    ''' Container Class for parsed "nodes" from config file

        Also initializes virtual ethernet interfaces incase the node is physical, and store the interfaces in the class

    '''
    def __init__(self, name, type, interface=None, ip_address=None):
        self.name = name
        self.type_name = type ## type name is a string that is taken directly from the config file
        self.type = utils.getCoreNodeType(type) # NodeTypes from CORE
        self.is_physical = True if (type == "rj45") or self.type == NodeTypes.RJ45 else False # Is physical node?

        ## used only for phyiscal interfaces - handled by method init_veth()
        self.vethInName = None
        self.vethOutName = None


        ## Interface on the physical host that is connected to this physical node
        self.interface = interface
        self.ip_address = ip_address
        if self.is_physical == True:
            logging.debug("initializing virtual interfaces for {}".format(name))
            self.init_veth()
            logging.debug("Finished initializing virtual interfaces for {}".format(name))

        self.links = []  ## interLinkObjects - Handled in Topology._parseLinkConfig()
        self.neighbours = []   # nodes that are directly connected to self

        # key is the second node in a link, value is the actual CORE_interface return by IpPrefixes.create_interface()
        self.interfaces = {}

        # if node is connected to a switch, then further nodes that are connected to that switch should be reachable
        self.has_switch_connection = False ## Handled when adding the links
        self.reachable_through_switch = {}
        self.indirect_neighbours = []



    def get_data(self, verbose=False):
        '''
            Method used by api to get data and display them
        '''
        data = collections.OrderedDict()
        data['name'] = self.name
        data['type'] = self.type_name
        data['ip_address'] = self.ip_address

        if verbose:
            neighbours = []
            for node in self.neighbours:
                neighbour_data = collections.OrderedDict()
                neighbour_data['name'] = node.name
                neighbour_data['type'] = node.type_name
                neighbour_data['ip_address'] = node.ip_address
                neighbour_data['direct_connection'] = True
                neighbours.append(neighbour_data)
            for node in self.indirect_neighbours:
                neighbour_data = collections.OrderedDict()
                neighbour_data['name'] = node.name
                neighbour_data['type'] = node.type_name
                neighbour_data['ip_address'] = node.ip_address
                neighbour_data['direct_connection'] = False
                neighbours.append(neighbour_data)
            data['neighbours'] = neighbours

        return data

    def open_term(self, sh=None):
        logging.debug("opening {} terminal from {}".format(sh, self.name))
        if (self.type == NodeTypes.DEFAULT):
            return self.CORE_node.client.term(sh)
        else:
            return self.CORE_node.term(sh)

    def icmd(self, command):
        '''
            runs command from the node and displays result in the main console
            return the status code of the execution
        '''
        return self.CORE_node.client.icmd(utils.get_cmd_command(command))

    def run_cmd(self, command, wait=True):
        if wait==True:
            return self.CORE_node.client.cmd(utils.get_cmd_command(command), wait=True)
        else:
            return self.CORE_node.client.cmd(utils.get_cmd_command(command), wait=False)


    def add_node_to_topology(self, topology):
        '''
            Adds this node to the provided topology, and updates the necessary internal information
        '''
        if (self.is_physical == True):
            id = None
            if (self.ip_address):
                ip_split = self.ip_address.split('.')
                id = ip_split[-1] # id should be equal host identifier from ip address. This is to avoid CORE assigning an identical IP address to another virtual node
            #print("id={}".format(id))
            coreNode = topology.session.add_node(_type=self.type, _id=id, node_options=NodeOptions(name=self.vethInName, model="rj45"))

            if (self.ip_address == None):
                self.ip_address = utils.get_host_ip()
            self.CORE_node = coreNode
        else: # all other nodes
            coreNode = topology.session.add_node(_type=self.type, node_options=NodeOptions(name=self.name, model=self.type_name))
            self.ip_address = topology.prefixes.ip4_address(coreNode)
            self.CORE_node = coreNode

        #print("Node: {} has internal ID {}".format(self.name, self.CORE_node.id))

        if self not in topology.interNodeObjects:
            topology.interNodeObjects.append(self)

    def handle_switch_case(self):
        if (self.has_switch_connection):
            for neighbour in self.neighbours:
                if neighbour.type == NodeTypes.SWITCH:
                    switch  = neighbour
                    for node in switch.neighbours:
                        if (node is not self):
                            self.reachable_through_switch[node] = switch
                            self.indirect_neighbours.append(node)

    #        print("node is {0}".format(self.name))
        #    for k,v in self.reachable_through_switch.iteritems():
            #    print("Key = {0} \t Value = {1}".format(k.name,v.name))
                # print("Switch dictionary: {0}".format(self.reachable_through_switch[switch]))


    def get_switch_connected_to_node(self, node_name):
        for switch, node in self.reachable_through_switch.items():    # for name, age in dictionary.iteritems():  (for Python 2.x)
            if node.name == node_name:
                return node

    def create_CORE_interface(self):
        if (self.is_physical):
            ## create interface with empty InterfaceData
            interface = InterfaceData(*[None] * 7)
        else:
            interface = Topology.prefixes.create_interface(currentNode)

        return interface

    def get_inter_link(self, node_two_name):
        for link in self.links:
            if ((link.first_node.name == self.name and link.second_node.name == node_two_name)
                or (link.second_node.name ==  self.name and link.first_node.name == node_two_name)):
                return link

    def init_veth(self):
        '''
            in case of a physical node, create the necessary virtual ethernet devices and bridges, to achieve connectivity between the physical and virtual nodes. 
        '''
        if self.is_physical == True:
            # create virtual Ethernet pair  on host computer
            self.vethInName = "{0}INveth".format(self.name)
            self.vethOutName = "{0}OUTveth".format(self.name)

            subprocess.call(["sudo", "ip", "link", "add", self.vethInName, "type", "veth", "peer", "name", self.vethOutName])

            ## Set up the veth pair
            subprocess.call(["sudo", "ip", "link", "set", self.vethInName, "up"])
            subprocess.call(["sudo", "ip", "link", "set", self.vethOutName, "up"])


            # If interface was provided, then we have to set up a bridge between the veth and the actual interface that is runnig on the host_ip
            self.bridge_name = self.name + "bridge"
            if (self.interface):
                subprocess.call(utils.get_cmd_command("sudo brctl addbr {}".format(self.bridge_name)))
                subprocess.call(utils.get_cmd_command("sudo brctl setfd {} 0".format(self.bridge_name))) # Set forward delay = 0
                subprocess.call(utils.get_cmd_command("sudo brctl addif {} {}".format(self.bridge_name, self.vethOutName))) # Add veth peer that is in the host namespace to bridge
                subprocess.call(utils.get_cmd_command("sudo brctl addif {} {}".format(self.bridge_name, self.interface))) # do the same for the actual network device in the host
                subprocess.call(utils.get_cmd_command("sudo ip link set {} up".format(self.bridge_name))) # do the same for the actual network device in the host


            global interface_names
            interface_names.append(self.name)
            interface_names.append(self.bridge_name)
            #
            # with open("physical_interfaces.txt","a+") as f:
            #     f.write(self.name)
            #     f.write('\n')
            #     f.write(self.bridge_name)
            #     f.write('\n')


    def delete(self):
        for link in self.links:
            link.delete()
        del self.links
        self.shutdown()
        return self.get_data()

    def shutdown(self):
        ''' deletes virtual interfaces at the end of a session '''
        if (self.is_physical == True):

            # don't show output
            with open(os.devnull, "w") as f:
                statuses = []
                statuses.append(subprocess.call(utils.get_cmd_command("sudo ip link del {0}".format(self.vethInName))))
                statuses.append(subprocess.call(utils.get_cmd_command("sudo ip link del {0}".format(self.vethOutName))))
                statuses.append(subprocess.call(utils.get_cmd_command("sudo ip link del {}".format(self.bridge_name))))

            # Return is used for testing and debugging purposes - The status should be 0 on success.
            return statuses

    def __str__(self):
        return ('''
name = {0}
type = {1}
ip_address = {2}
physical = {3}
VethIn = {4}
VethOut = {5}
Core_Node = {6}
Links = {7}
Interfaces = {8}

                ''').format(self.name, self.type, self.ip_address, self.is_physical, self.vethInName, self.vethOutName
                            , self.CORE_node, self.links, self.interfaces)


def main():
    topology = Topology("topologyConfig.txt")
    nodes = topology.nodes
    subscriber = nodes[0]
    switch = nodes[1]
    publisher = nodes[2]
    subscriber.client.icmd(["ping", "-c", "3", topology.prefixes.ip4_address(publisher)])



if __name__ == '__main__':
    main()
