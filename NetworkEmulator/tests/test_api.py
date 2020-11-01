import sys
sys.path.insert(0,'../')

import unittest
import threading

import requests

from core.__init__ import CoreCommandError


from TopologyConfigurator import Topology
from api import API
from cleanup import cleanup
from parser import Parser
import utils


url = "http://localhost:5000/"

def url_helper(resource):
    global url
    if (resource == "topology"):
        return url + "topology"
    elif (resource == "node"):
        return url + "topology/nodes"
    elif (resource == "link"):
        return url + "topology/links"
    elif (resource == "term"):
        return url + "topology/nodes/term"
    else:
         return url

class testAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        parser = Parser()
        nodes, links, netmask = parser.parse_topology("topology.yml")
        cls.yml_nodes = nodes
        cls.yml_links = links
        cls.api = API()

        # run API on different thread in order to continue execution
        cls.server_thread = threading.Thread(target=cls.api.run)
        cls.server_thread.daemon=True
        cls.server_thread.start()

    def setUp(self):
        new_topology = Topology(self.yml_nodes, self.yml_links)
        self.api.set_topology(new_topology)
        topology = API.topology

    def tearDown(self):
        self.api.topology.shutdown()
        #self.server_thread.shutdown()

    def test_get_topology(self):
        print("start test_get_topology")
        url = url_helper("topology")
        #PARAMS = {'name': 'subscriber'}
        r = requests.get(url = url) #, params = {})

        status_code = r.status_code
        self.assertEqual(status_code, 200)

        expected_response = '''{"nodes": [{"name": "switch", "type": "switch", "ip_address": "10.0.0.1"}, {"name": "phys", "type": "rj45", "ip_address": "10.0.2.15"}, {"name": "publisher", "type": "host", "ip_address": "10.0.0.3"}, {"name": "subscriber", "type": "host", "ip_address": "10.0.0.4"}, {"name": "broker", "type": "host", "ip_address": "10.0.0.5"}], "links": [{"first_node": "subscriber", "first_node_ip": "10.0.0.4", "second_node": "switch", "second_node_ip": "10.0.0.1", "link_options": {}}, {"first_node": "publisher", "first_node_ip": "10.0.0.3", "second_node": "switch", "second_node_ip": "10.0.0.1", "link_options": {}}, {"first_node": "phys", "first_node_ip": "10.0.2.15", "second_node": "switch", "second_node_ip": "10.0.0.1", "link_options": {}}, {"first_node": "broker", "first_node_ip": "10.0.0.5", "second_node": "switch", "second_node_ip": "10.0.0.1", "link_options": {}}]}\n'''
        self.assertEqual(r.text, expected_response)
        print("finish test_get_topology")

    def test_get_node_no_params(self):
        '''
            When no parameters are given, all nodes should be returned.
        '''
        print("start test_get_node_no_params")
        url = url_helper("node")
        #PARAMS = {'name': 'subscriber'}
        r = requests.get(url = url) #, params = {})

        status_code = r.status_code
        self.assertEqual(status_code, 200)
        expected_response = '''[{"name": "switch", "type": "switch", "ip_address": "10.0.0.1"}, {"name": "phys", "type": "rj45", "ip_address": "10.0.2.15"}, {"name": "publisher", "type": "host", "ip_address": "10.0.0.3"}, {"name": "subscriber", "type": "host", "ip_address": "10.0.0.4"}, {"name": "broker", "type": "host", "ip_address": "10.0.0.5"}]\n'''
        self.assertEqual(r.text, expected_response)
        print("finish test_get_node_no_params")

    def test_get_node(self):
        print("start test_get_node")
        url = url_helper("node")
        PARAMS = {'name': 'subscriber'}
        r = requests.get(url = url, params = PARAMS)

        self.assertEqual(r.status_code, 200)
        data = r.json()
        name = data["name"]
        self.assertEqual(name, "subscriber")
        print("finish test_get_node")

    def test_get_node_returns_404(self):
        '''
            when trying to retrieve a node that doesnt exist, 404 should be returned
        '''
        print("start test_get_node_returns_404")
        url = url_helper("node")
        PARAMS = {'name': 'nodeDoesNotExist'}
        r = requests.get(url = url, params = PARAMS)
        self.assertEqual(r.status_code, 404)

        print("finish test_get_node_returns_404")


    def test_post_node_returns_200(self):
        print("start test_post_node_returns_200")

        url = url_helper("node")
        PARAMS = {'name': 'newnode',
                  'type':'host'}

        node_count = len(API.topology.interNodeObjects)

        # sending post request and saving the response as response object
        r = requests.post(url = url, params = PARAMS)
        newnode = API.topology.get_node_by_name("newnode")
        self.assertEqual(node_count+1, len(API.topology.interNodeObjects))
        self.assertIsNotNone(newnode)
        self.assertIn(newnode.CORE_node.id, API.topology.session.nodes)
        self.assertEqual(newnode.CORE_node, API.topology.session.nodes[newnode.CORE_node.id])
        self.assertEqual(r.status_code, 201)
        print("finish test_post_node_returns_200")


    def test_post_node_invalid_params(self):
        print("start test_post_node_invalid_params")

        url = url_helper("node")
        PARAMS = {'name': 'newnode'}
        r = requests.post(url = url, params = PARAMS)
        self.assertEqual(r.status_code, 400)

        PARAMS = {'type':'host'}
        r = requests.post(url = url, params = PARAMS)
        self.assertEqual(r.status_code, 400)

        r = requests.post(url = url)
        self.assertEqual(r.status_code, 400)

        print("finish test_post_node_invalid_params")


    def test_post_node_duplicate_node(self):
        print("start test_post_node_duplicate_node")

        url = url_helper("node")
        PARAMS = {'name': 'subscriber',
                  'type': 'host'}
        r = requests.post(url = url, params = PARAMS)
        self.assertEqual(r.status_code, 409)

        PARAMS = {'name': 'subscriber',
                  'type': 'rj45'}
        r = requests.post(url = url, params = PARAMS)
        self.assertEqual(r.status_code, 409)

        print("finish test_post_node_duplicate_node")

    def test_delete_node_success(self):
        print("start test_delete_node_success")

        url = url_helper("node")
        PARAMS = {'name': 'subscriber'}

        node_count = len(API.topology.interNodeObjects)

        deleted_node = API.topology.get_node_by_name("subscriber")
        ip_address = deleted_node.ip_address
        # sending post request and saving the response as response object
        r = requests.delete(url = url, params = PARAMS)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(node_count-1, len(API.topology.interNodeObjects))
        self.assertNotIn(deleted_node, API.topology.interNodeObjects)
        self.assertNotIn(deleted_node.CORE_node.id, API.topology.session.nodes)
        self.assertIsNone(API.topology.get_node_by_name("subscriber"))
        publisher = API.topology.get_node_by_name("publisher")
        # attempt ping
        status = publisher.run_cmd("ping -c 1 {}".format(ip_address), wait=True)
        self.assertNotEqual(status, 0)

        print("finish test_delete_node_success")
if __name__ == '__main__':
    try:
        unittest.main()
    except CoreCommandError:
        pass
