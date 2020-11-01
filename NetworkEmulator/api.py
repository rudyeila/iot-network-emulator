'''
This is the RESTAPI that can be used to control the emulator at runtime. For a full documentation, refer to https://documenter.getpostman.com/view/8436185/SVfRtnYd?version=latest

In order to expand this API, you can simply add new resources and define the HTTP methods on them. See some of the examples below. 
'''

from flask import Flask, request
from flask_restful import Resource, Api
from collections import OrderedDict
from utils import get_LinkOptions
import logging
#from globals import topology

app = Flask(__name__)
api = Api(app)


def html(content):  # Also allows you to set your own <head></head> etc
    return '<html><head>Emulator API</head><body>' + content + '</body></html>'


def help_text():
    return '''
<p1>
This is a short documentation for using the API.

For a full documentation, refer to: <a href="https://documenter.getpostman.com/view/8436185/SVfRtnYd?version=latest">

You are able to access the following resources:

Topology
Nodes
Links
NodeTerminals
Scheduler
Jobs

We will take a look at the possible commands for each resource.

<h1>Topology:</h1>
get - http://localhost:5000/topology/ - Returns a dictionary containing the nodes and the link contained within the topology

<h1>Nodes:</h1>
get - http://localhost:5000/topology/nodes - Returns a dictionary of the current nodes within the topology
get - http://localhost:5000/topology/nodes?name=subscriber - Parameters: name=<str:name> - returns node with specified name

post - http://localhost:5000/topology/nodes?name=newnode&type=host - Parameters: name=<str:name>, type=<str:nodetype> - adds specified node to topology

delete - http://localhost:5000/topology/nodes?name=subscriber - Parameters: [name] - Deletes node with specified name from topology

<h2>Node Terminals</h2>
get - http://localhost:5000/topology/nodes/term?name=subscriber - parameters: name=NodeName - Launches a terminal from the specified node. You need to have Xterm installed.


<h1>Links:</h1>
get - http://localhost:5000/topology/links - Returns a dictionary of the current nodes within the topology
get - http://localhost:5000/topology/links?node1=name1&node2=name2 -Parameters [node1=<str:name>, node2=<str:name>] - Returns the link between the provided node1 and node2, if it exists.

post - http://localhost:5000/topology/links?node1=name1&node2=name2 -Parameters [node1=<str:name>, node2=<str:name>] - Creates a new link between the provided node names (the two nodes must already exist in the topology)

put - http://localhost:5000/topology/links?node1=name1&node2=name2&delay=10000&bandwidth=1024&loss=10&dup=2&jitter=15
Parameters [
node1 = name of the first node of the link
node2 = name of the second node of the link
delay = delay to add in microseconds
bandwidth = new limited bandidth in bits per second
loss = packet loss rate in %
dup = packet duplication rate in %
jitter = new jitter value
]

delete - http://localhost:5000/topology/links?node1=name1&node2=name2 -Parameters [node1=<str:name>, node2=<str:name>] - Deletes the link between the provided node1 and node2, if it exists.



<h1>Scheduler</h1>
get - http://localhost:5000/scheduler - returns a dictionary of currents jobs in the scheduler

<h2>Jobs</h2>
get - http://localhost:5000/scheduler/jobs?id=eas566eteassafsareg - Parameters: id=Job_id - Returns information regarding the provided scheduler job id. </p1>
'''


class API(object):

    '''
    This class is responsible for setting up the API
    '''

    # The input parameters are a hack to pass the toplogy and scheduler from the main module to this one.
    # I was having issues with the python import system and this ugly solution is what I came up with.
    def __init__(self, topology=None, scheduler=None):
        #global topology, scheduler
        API.topology = topology
        API.scheduler = scheduler

        #topology = self.topology
        if (scheduler):
            logging.debug("No scheduler was passed to the API")
        #self.topology = topology
        self.app = app
        self.api = api
        self.api.add_resource(Home, '/')
        self.api.add_resource(Topology, '/topology')
        self.api.add_resource(Node, '/topology/nodes')
        self.api.add_resource(NodeTerm, '/topology/nodes/term')
        self.api.add_resource(Link, '/topology/links')
        self.api.add_resource(Scheduler, '/scheduler')
        self.api.add_resource(Job, '/scheduler/jobs')

    def set_topology(self, new_topology):
        #global topology
        API.topology = new_topology

    def run(self, debug=False, reloader=False):
        print("debug = {}".format(debug))
        self.app.run(host='0.0.0.0', debug=debug, use_reloader=reloader)


class Home(Resource):
    '''
        The hope path of the API
    '''

    def get(self):
        result = help_text()
        return html(result)  # , 200


class Topology(Resource):
    '''
        This class represents the Topology resource
    '''

    def get(self):
        return API.topology.get_data(), 200


class Node(Resource):
    '''
        This class represents the Node resource
    '''

    def get(self):
        name = request.args.get('name')

        if (not name):
            data = []
            for node in API.topology.interNodeObjects:
                print(node.name)
                data.append(node.get_data())
            return data, 200

        node = API.topology.get_node_by_name(name)
        if (not node):
            return {"error": "No node with name \"{}\" was found.".format(name)}, 404

        return node.get_data(verbose=True), 200

    def post(self):

        name = request.args.get("name")
        type = request.args.get("type")
        if (not name or not type):
            return {"Error": "You need to specify a node name and type to create a new node"}, 400
        if (API.topology.get_node_by_name(name) != None):
            return {"Error": "A node with name {} already exist. Nodes must have unique names.".format(name)}, 409

        return API.topology.add_node(name, type).get_data(), 201

    # def put(self):
    #     name = request.args.get("name")
    #     new_name=request.args.get("newname")
    #     if (not name):
    #         return {"Error": "You need to specify the name of the node to be updated"}, 404
    #     if (API.topology.get_node_by_name(name) != None):
    #         return {"Error": "A node with name {} already exist. Nodes must have unique names.".format(name)}, 404

    def delete(self):
        name = request.args.get("name")

        if (not name):
            return {"Error": "You did not provide the name of the node that has to be deleted.".format(name)}, 404

        delete = API.topology.delete_node(name)
        print(delete)
        if (not delete):
            return {"Error": "No node with name \"{}\" was found.".format(name)}, 404

        return {"success": "{} has been deleted".format(name),
                "node": delete}, 200


class Link(Resource):
    '''
        This class represents the Link resource
    '''

    def get(self):
        node1_name = request.args.get('node1')
        node2_name = request.args.get('node2')
        print("node1 name {} node2 name  {}".format(node1_name, node2_name))

        if (not node1_name or not node2_name):
            result = []
            links = API.topology.interLinkObjects
            for link in links:
                result.append(link.get_data())
            return result, 200
        # node1 = API.topology.get_node_by_name(node1_name)
        # node2 = API.topology.get_node_by_name(node2_name)
        link = API.topology.get_link_by_node_names(node1_name, node2_name)
        response = link.get_data()
        return response, 200

    def post(self):
        node1_name = request.args.get('node1')
        node2_name = request.args.get('node2')

        if (not node1_name or not node2_name):
            return {"Error": "You must provide the names of the two nodes that you want to create a link between"}, 404

        link = API.topology.add_link(node1_name, node2_name, init=False)
        return link.get_data(), 201

    def put(self):
        node1_name = request.args.get('node1')
        node2_name = request.args.get('node2')
        if (not node1_name or not node2_name):
            return {"Error": "You must provide the names of the two nodes that you want to create a link between"}, 404
        delay = request.args.get('delay')
        bandwidth = request.args.get('bandwidth')
        loss = request.args.get('loss')
        dup = request.args.get('dup')
        jitter = request.args.get('jitter')

        link_params = {}
        link_params['delay'] = delay
        link_params['bandwidth'] = bandwidth
        link_params['loss'] = loss
        link_params['dup'] = dup
        link_params['jitter'] = jitter

        print("IN API:")
        for e, v in link_params.items():
            print("{} = {} ({})".format(e, v, type(v)))

        print("finish API")
        link_ops = get_LinkOptions(link_params)
        status = API.topology.update_link(node1_name, node2_name, link_ops)
        if (status == None or status == False):
            return {"Error": "Link could not be updated"}, 400
        return {
            "Status": "Link successfully updated",
            "Parameters": link_params
        }, 200

    def delete(self):
        node1_name = request.args.get('node1')
        node2_name = request.args.get('node2')
        if (not node1_name or not node2_name):
            return {"Error": "You must provide the names of the two nodes that constitute the link you want to delete"}, 404

        return {
            "Result": "The following link was removed",
            "link": API.topology.delete_link(node1_name, node2_name).get_data()
        }, 200


class NodeTerm(Resource):
    '''
        launch terminal for node
    '''

    def get(self):
        name = request.args.get("name")
        #shell = request.args.get("shell")

        if (not name):
            return {"Error": "You must provide the name of the name you want to launch the terminal from"}, 400

        node = API.topology.get_node_by_name(name)

        if (not node):
            return {"Error": "No node with name \"{}\" was found in the topology".format(name)}, 404

        try:
            result = node.open_term(sh="/bin/bash")
        except AttributeError as e:
            return {"Error": "An error occured when launching terminal. Launching a terminal for a physical node is not supported. \n you have to manually launch the terminal from the host computer.",
                    "type": str(type(e)),
                    "message": str(e)}, 400
        except Exception as e:
            return {"Error": "An error occured when launching terminal",
                    "type": str(type(e)),
                    "message": str(e)}, 400

        return {"Message": "Terminal successfully launched from node \"{}\"".format(name)}, 200

    def put(self):
        ''' Run command on a node '''
        name = request.args.get("name")
        # plus '+' signs represent spaces in command
        cmd = request.args.get("command")
        cmd = cmd.replace('+', ' ')
        wait = request.args.get("wait")

        if wait == None:
            wait = True

        try:
            status = API.topology.get_node_by_name(name).run_cmd(cmd, wait)
            print(status)
            if wait:
                return {"Body": status}, 200
            else:
                return {"Output": status}, 200
        except Exception as e:
            return {"Error": "An error occured when executing command",
                    "type": str(type(e)),
                    "message": str(e)}, 400


class Scheduler(Resource):
    '''
        This class represents the Scheduler resource
    '''

    def get(self):
        jobs = API.scheduler.format_jobs()
        return {"result": jobs}, 200

    def post(self):
        if (API.scheduler.is_started == True):
            return {"status": "Scheduler is already running"}, 409
        else:
            API.scheduler.schedule_events(
                API.scheduler.events, API.scheduler.topology)
            API.scheduler.start()
            return {"status": "Scheduler is being started. It has the following jobs",
                    "jobs": self.get()}, 200


class Job(Resource):
    '''
        This class represents a scheduler job resource
    '''

    def get(self):
        job_id = request.args.get("id")
        jobs = API.scheduler.format_jobs(job_id=job_id)
        return {"result": jobs[0]}, 200


if __name__ == '__main__':
    app.run(debug=True)
