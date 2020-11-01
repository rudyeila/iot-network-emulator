import sys
sys.path.insert(0,'../')

import unittest
from TopologyConfigurator import Topology, InterNode, InterLink
from parser import Parser
from cleanup import cleanup
from core.emulator.enumerations import NodeTypes
from core import CoreCommandError
from core import CoreError
import subprocess
import utils

def ping(source_node, destination_node, ip_prefixes):
    from_node = source_node.CORE_node
    to_node = destination_node.CORE_node
    if (destination_node.type == NodeTypes.RJ45):
        address = destination_node.ip_address
    else:
        address = ip_prefixes.ip4_address(to_node)
    return from_node.cmd(["ping", "-c", "3", address])

def ping_all(nodes, prefixes):
    # Try all possible ping combinations
    statuses = []
    for node in nodes:
        reachable = list(nodes)
        reachable.remove(node)
        for neighbor in reachable:
            if (node.type == NodeTypes.RJ45):
                status = subprocess.call(utils.get_cmd_command("ping -c 3 {}".format(neighbor.ip_address)))
            else:
                status = ping(node, neighbor, prefixes)
            print("{} ping {} returned status code {}".format(node.name, neighbor.name, status))
            statuses.append(status)
    return statuses

class testTopology(unittest.TestCase):
    counter = 0
    parser = Parser()
    nodes, links, netmask = parser.parse_topology("topology.yml")
    yml_nodes = nodes
    yml_links = links
    #topology = Topology(yml_nodes, yml_links)
    for node in yml_nodes:
        print(node.name, node.type)


    def setUp(self):
        # used for cleanup later
        print("#{}: setup method".format(testTopology.counter))
        # with open("physical_interfaces.txt","w+") as f:
        #     f.close()
        testTopology.topology = Topology(testTopology.yml_nodes, testTopology.yml_links)
        print("#{}: finish setup".format(testTopology.counter))

    def tearDown(self):
        print("#{}: tearDown up method".format(testTopology.counter))
        testTopology.topology.shutdown(hard=True)
        print("#{}: finish tearDown".format(testTopology.counter))
        testTopology.counter += 1

    def test_init(self):
        '''
            To test that the topology has been correctly instantiated, we will just try a few pings and make sure they work.
        '''
        print("running test_init")
        topology = testTopology.topology
        subscriber = topology.get_node_by_name("subscriber")
        publisher = topology.get_node_by_name("publisher")
        #phys = topology.get_node_by_name("bro")

        nodes = list(topology.interNodeObjects)
        for node in nodes:
            if node.type == NodeTypes.RJ45:
                print(node)
                nodes.remove(node)
        nodes.remove(topology.get_node_by_name("switch"))

        # Try all possible ping combinations
        statuses = ping_all(nodes, topology.prefixes)
        for status in statuses:
            self.assertEqual(status, 0)

    def test_manual_init(self):

        testTopology.topology.shutdown(hard=True)

        with open("physical_interfaces.txt","w+") as f:
             f.close()

        print("Starting testTopology.test_manual_init()")
        topology = Topology()
        subscriber = topology.add_node("subscriber", "host")
        publisher = topology.add_node("publisher", "host")
        switch = topology.add_node("switch", "switch")
        phys = topology.add_node("phys", "rj45")

        nodes = [subscriber, publisher, phys]

        for node in nodes:
            topology.add_link(node.name, switch.name)

        self.assertEqual(len(topology.interNodeObjects), 4)
        self.assertEqual(len(topology.interLinkObjects), 3)

        statuses = ping_all(nodes, topology.prefixes)
        for status in statuses:
            self.assertEqual(status, 0)

        nodes.append(switch)
        for node in nodes:
            self.assertIn(node.CORE_node.id, topology.session.nodes)

        for id in topology.session.nodes:
            print(topology.session.nodes[id].name)

    def test_add_node(self):
        print("running test_add_node")
        topology = testTopology.topology
        node_num = len(topology.interNodeObjects)
        c = 0

        host = topology.add_node("hostnode",  "host")
        self.assertEqual(host.name, "hostnode")
        self.assertEqual(host.type, NodeTypes.DEFAULT)
        self.assertIn(host, topology.interNodeObjects)
        # Make sure node is added to CORE session
        self.assertIn(host.CORE_node.id, topology.session.nodes)
        self.assertEqual(host.CORE_node, topology.session.get_node(host.CORE_node.id))
        c += 1

        switch = topology.add_node("switchnode", "switch")
        self.assertEqual(switch.name, "switchnode")
        self.assertEqual(switch.type, NodeTypes.SWITCH)
        self.assertIn(switch, topology.interNodeObjects)
        self.assertIn(switch.CORE_node.id, topology.session.nodes)
        self.assertEqual(switch.CORE_node, topology.session.get_node(switch.CORE_node.id))
        c += 1

        phys = topology.add_node("physnode", "rj45")
        self.assertEqual(phys.name, "physnode")
        self.assertEqual(phys.type, NodeTypes.RJ45)
        self.assertIn(phys, topology.interNodeObjects)
        self.assertIn(phys.CORE_node.id, topology.session.nodes)
        self.assertEqual(phys.CORE_node, topology.session.get_node(phys.CORE_node.id))
        c += 1

        # Make sure nodes are also added to the list of nodes in the topology
        self.assertEqual(node_num+c, len(topology.interNodeObjects))

        # try adding new node with same name
        with self.assertRaises(ValueError):
            topology.add_node("hostnode",  "host")
            topology.add_node("switchnode",  "switch")
            topology.add_node("physnode",  "rj45")


    def test_delete_node(self):
        print("running test_delete_node")
        topology = testTopology.topology
        node_num = len(topology.interNodeObjects)
        link_num = len(topology.interLinkObjects)

        subscriber = topology.get_node_by_name("subscriber")
        link_count = len(subscriber.links)
        topology.delete_node(subscriber.name)
        self.assertEqual(node_num-1, len(topology.interNodeObjects))
        self.assertEqual(link_num-link_count, len(topology.interLinkObjects))
        self.assertNotIn(subscriber, topology.interNodeObjects)

        # make sure node was removed from CORE session as well
        self.assertNotIn(subscriber.CORE_node.id, topology.session.nodes)
        with self.assertRaises(CoreError):
            core_node = topology.session.get_node(subscriber.CORE_node.id)

        publisher = topology.get_node_by_name("publisher")
        # Try pinging the subscriber node from  publisher - It should fail, thus returning status 1
        status = ping(publisher, subscriber, topology.prefixes)
        self.assertNotEqual(status, 0)

        broker = topology.get_node_by_name("broker")
        link_count1 = len(broker.links)
        topology.delete_node(broker.name)
        self.assertEqual(node_num-2, len(topology.interNodeObjects))
        self.assertEqual(link_num-link_count1-link_count, len(topology.interLinkObjects))
        self.assertNotIn(broker, topology.interNodeObjects)
        # make sure node was removed from CORE session as well
        self.assertNotIn(broker.CORE_node.id, topology.session.nodes)
        with self.assertRaises(CoreError), self.assertRaises(CoreCommandError):
            core_node = topology.session.get_node(subscriber.CORE_node.id)

    def test_add_link(self):
        print("Starting test_add_link")
        topology = testTopology.topology
        # add new node
        newnode = topology.add_node("newnode", "host")
        newnode1 = topology.add_node("newnode1", "phys")
        newnode2 = topology.add_node("newnode2", "host")

        nodes = [newnode,newnode1,newnode2]

        publisher = topology.get_node_by_name("publisher")
        subscriber = topology.get_node_by_name("subscriber")
        phys = topology.get_node_by_name("phys")
        switch = topology.get_node_by_name("switch")
        existing_nodes = [publisher, subscriber, phys]



        link_count = len(topology.interLinkObjects)
        c = 1
        for newnode in nodes:
            new_link = topology.add_link(newnode.name, switch.name)
            self.assertEqual(link_count+c, len(topology.interLinkObjects))
            self.assertIn(new_link, topology.interLinkObjects)
            first_node = new_link.first_node
            second_node = new_link.second_node

            self.assertIn(switch, first_node.interfaces)
            self.assertIn(switch, first_node.neighbours)
            self.assertIn(newnode, second_node.neighbours)
            self.assertIn(newnode, second_node.interfaces)
            existing_nodes.append(newnode)
            c += 1
            ## ping test
            status = ping(publisher, newnode, topology.prefixes)
            self.assertEqual(status, 0) # status 0 means success

            with self.assertRaises(ValueError):
                topology.add_link(newnode.name, switch.name)

        # try creating a node between a node and itself
        with self.assertRaises(ValueError):
            topology.add_link(newnode.name, newnode.name)

        # try creating a link between nodes that don't exist within the topology
        with self.assertRaises(ValueError):
            topology.add_link("DoesNotExist", "DoesNotExist2")

    def test_delete_link(self):
        print("running test_delete_link")
        topology = testTopology.topology
        subscriber = topology.get_node_by_name("subscriber")
        publisher = topology.get_node_by_name("publisher")
        switch = topology.get_node_by_name("switch")

        sub_switch = topology.get_link_by_node_names(subscriber.name, switch.name)
        topology.delete_link(subscriber.name, switch.name)

        self.assertNotIn(sub_switch, topology.interLinkObjects)

        # Try pinging the publisher node from the subscriber node - It should fail, thus returning status 1 or 2
        status = ping(subscriber, publisher, topology.prefixes)
        self.assertNotEqual(status, 0)

    def test_get_node_by_name(self):
        print("running test_get_node_by_name")
        topology = testTopology.topology

        subscriber = topology.get_node_by_name("subscriber")
        self.assertEqual(subscriber.name, "subscriber")

        # Upper case should be converted to lower case
        subscriber = topology.get_node_by_name("SUBSCRIBER")
        self.assertEqual(subscriber.name, "subscriber")


    def test_get_link_by_node_names(self):
        print("running test_get_link_by_node_names")
        topology = testTopology.topology

        subscriber = topology.get_node_by_name("subscriber")
        switch = topology.get_node_by_name("switch")

        link = topology.get_link_by_node_names(subscriber.name, switch.name)
        self.assertEqual(link.first_node, subscriber)
        self.assertEqual(link.second_node, switch)

    #    with self.assertRaises(ValueError):
    #        link = topology.get_link_by_node_names(switch.name, subscriber.name   )
            # self.assertEqual(link.first_node, switch)
            # self.assertEqual(link.second_node, subscriber)


class testInterLink(unittest.TestCase):
    def test_init_link(self):
            print("starting testInterLink.test_init_link()")
            topology = Topology()

            node1 = InterNode("testNode", "host")
            node1.add_node_to_topology(topology)

            # phys = InterNode("phys", "rj45")
            # phys.add_node_to_topology(topology)

            switch = InterNode("switch", "switch")
            switch.add_node_to_topology(topology)

            link1 = InterLink(node1, switch)
            # link2 = InterLink(phys, switch)
            #
            # nodes1 = [node1, switch]
            self.assertEqual(link1.first_node, node1)
            self.assertEqual(link1. second_node, switch)
            self.assertFalse(link1.has_physical)
            self.assertIn(switch, link1.first_node.neighbours)
            self.assertIn(node1, link1.second_node.neighbours)
            self.assertEqual(link1.first_interface, link1.first_node.interfaces[link1.second_node])
            self.assertEqual(link1.second_interface, link1.second_node.interfaces[link1.first_node])

            topology.shutdown(hard=True)

    def test_delete_link(self):
        pass

class testInterNode(unittest.TestCase):

    def test_init_node(self):
        physical_node = InterNode("phys", "rj45")
        self.assertEqual(physical_node.name, "phys")
        self.assertEqual(physical_node.type, NodeTypes.RJ45)
        self.assertTrue(physical_node.is_physical)
        self.assertEqual(physical_node.vethInName, "physINveth")
        self.assertEqual(physical_node.vethOutName, "physOUTveth")


    def test_handle_switch_case(self):
        print("starting test_handle_switch_case")
        topology = Topology()

        test_node = InterNode("testNode1", "host")
        test_node.add_node_to_topology(topology)

        node2 = InterNode("node2", "host")
        node2.add_node_to_topology(topology)

        node3 = InterNode("node3", "host")
        node3.add_node_to_topology(topology)

        switch = InterNode("switch", "switch")
        switch.add_node_to_topology(topology)

        node4 = InterNode("node4", "host")
        node4.add_node_to_topology(topology)

        switch2 = InterNode("switch2", "switch")
        switch2.add_node_to_topology(topology)


        link1 = InterLink(test_node, switch)
        link2 = InterLink(node2, switch)
        link3 = InterLink(node3, switch)
        link4 = InterLink(node4, switch2)
        link5 = InterLink(node3, switch2)


        test_node.handle_switch_case()

        indirect_neighbours = [node2, node3] #, node4]
        for indirect_neighbour in indirect_neighbours:
            self.assertEqual(test_node.reachable_through_switch[indirect_neighbour], switch)
            self.assertIn(indirect_neighbour, test_node.indirect_neighbours)

        topology.shutdown(hard=True)

    def test_add_node_to_topology(self):
        # set up a topology
        topology = Topology()

        newnode = InterNode("TestAddToTopology", "host")
        newnode.add_node_to_topology(topology)

        #self.assertIn(newnode, topology.interNodeObjects)
        self.assertIsNotNone(newnode.CORE_node)
        self.assertIn(newnode.CORE_node.id, topology.session.nodes)
        if (newnode.is_physical):
            self.assertEqual(newnode.ip_address, utils.get_host_ip())
        else:
            self.assertEqual(newnode.ip_address, topology.prefixes.ip4_address(newnode.CORE_node))

        topology.shutdown(hard=True)


    def test_delete(self):
        topology = Topology()
        node1 = InterNode("test1", "host")
        node1.add_node_to_topology(topology)
        node2 = InterNode("test2", "host")
        node2.add_node_to_topology(topology)

        topology.add_link(node1.name, node2.name)
        node1.delete()

        with self.assertRaises(AttributeError):
            node1.links

        phys = InterNode("phys", "rj45")
        phys.add_node_to_topology(topology)
        switch = InterNode("switch", "switch")
        switch.add_node_to_topology(topology)

        statuses = phys.delete()
        with self.assertRaises(AttributeError):
            phys.links
            #self.assertEqual(len(phys.links), 0)
        topology.shutdown(hard=True)
        # for status in statuses:
        #     print("status = {}".format(status))
        #     self.assertEqual(status, 0)

if __name__ == '__main__':
    #try:
    unittest.main()
    #except CoreCommandError:
        #cleanup()
