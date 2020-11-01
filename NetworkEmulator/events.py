'''
 In this module, the different events that the scheduler can take are defined.

 When you want to add an event, there are 3 parts of the code that you mainly have to modify.
 1. Define a class for the event here. The new event should inherit from the TimedEvent class and should contain all of the arguments required for the event.
 2. You need to add instructions for parsing this new event in the parser.py module, specifcally in the parse_events method.
 3. In the scheduler module, specifically in the schedule_events method, you need to add an if statement for the new event, and schedule a call to the correct funtion that should handle the event.
'''


from core.emulator.emudata import LinkOptions


class TimedEvent(object):
    '''
        Base class for Scheduler events.
    '''

    def __init__(self, execution_delay=0):
        # The time, after the start of the scheduler of when the event should be executed.
        self.execution_delay = execution_delay

        '''
        Conveniece method that retrieves the InterLink object belonging to the link between the two specified node names

        :param first_node_name: the name of the first node that is part of the link
        :type first_node_name: str

        :param second_node_name: the name of the second node that is part of the link
        :type second_node_name: str

        :return: the InterLink object that is associated with the link between the two provided node names
        :rtype: TopologyConfigurator.InterLink
        '''


class OpenTermEvent(TimedEvent):
    '''
        Scheduler event that is used to launch a terminal from a virtual node

        :param node_name: the name of the node from which the terminal is launched
        :type node_name: str

        :param shell: The path to the shell environment, defaults to /bin/bash
        :type shell: str

        :param args: a list of the arguments that are required for the execution
        :type args: list
    '''

    def __init__(self, node_name, execution_delay, shell="/bin/bash"):
        super(OpenTermEvent, self).__init__(execution_delay)
        self.node_name = node_name
        # Defaults to the xterm environment, but this param can be used to specify another terminal env.
        self.shell = shell
        self.args = [self.shell]


class RunCMDEvent(TimedEvent):
    '''
    Scheduler event that is used to execute a command on a virtual node.

    :param node_name: the name of the node on which the command should be executed
    :type node_name: str

    :param command: the command that should be executed
    :type command: str

    :param wait: If wait is true, then program wait until execution is over, otherwise, it simply retunrs 0 and conttinues.
    :type wait: boolean

    :param args: a list of the arguments that are required for the execution
    :type args: list
    '''

    def __init__(self, node_name, command, execution_delay,  wait=True):
        super(RunCMDEvent, self).__init__(execution_delay)
        self.node_name = node_name
        self.command = command
        self.wait = wait
        self.args = [self.command, self.wait]


class LinkEvent(TimedEvent):
    '''
        LinkEvents are used to control the connections quality of different links
    '''

    def __init__(self, first_node_name, second_node_name, execution_delay, link_params):
        '''
        Scheduler event that is used to fluctuate the connection quality of a link
        :param first_node_name: the name of the first node that constitutes the link
        :type second_node_name: str

        :param second_node_name: the name of the second node that constitutes the link
        :type second_node_name: str

        :param link_params:  a dictionary of parameters and values derived from the YaML file
        :type link_params: dict

        :param linkOptions: class LinkOption representation of the link_params
        :type linkOptions: core.emulator.emudata.LinkOptions

        :param args: a list of the arguments that are required for the execution
        :type args: list
        '''

        super(LinkEvent, self).__init__(execution_delay)
        self.first_node_name = first_node_name
        self.second_node_name = second_node_name
        self.link_params = link_params
        self.linkOptions = self.get_LinkOptions()

        self.args = [self.first_node_name,
                     self.second_node_name, self.linkOptions]

    def get_LinkOptions(self):
        '''This method is used derive new LinkOptions() from the LinkEvent object.
        LinkOptions are used by CORE to specify delays, bandwidth etc for a specific link.

        :returns: linkOptions, a convenience object used by core to specify link values (delay, bandwidth, jitter etc.)
        :rtype: core.emulator.emudata.LinkOptions
        '''

        linkOptions = LinkOptions()
        for param, value in self.link_params.items():
            #print ("param = {} -- Value = {}".format(param, value))
            parameter = param.lower()
            newValue = value
            if (parameter == "session"):
                linkOptions.session = newValue
            elif (parameter == "delay"):
                linkOptions.delay = newValue
            elif (parameter == "bandwidth"):
                linkOptions.bandwidth = float(newValue)
            # Packet Loss Rate
            elif (parameter == "loss"):
                linkOptions.per = newValue
            # Packet duplication rate
            elif (parameter == "duplication"):
                linkOptions.dup = newValue
            elif (parameter == "jitter"):
                linkOptions.jitter = newValue
            # elif (parameter == "mer"):
            #     linkOptions.mer = newValue
            # elif (parameter == "burst"):
            #     linkOptions.burst = newValue
            # elif (parameter == "mburst"):
            #     linkOptions.mburst = newValue
            # elif (parameter == "gui_attributes"):
            #     linkOptions.gui_attributes = newValue
            # elif (parameter == "unidirectional"):
            #     linkOptions.unidirectional = newValue
            # elif (parameter == "emulation_id"):
            #     linkOptions.emulation_id = newValue
            # elif (parameter == "network_id"):
            #     linkOptions.network_id = newValue
            # elif (parameter == "key"):
            #     linkOptions.key = newValue
            # elif (parameter == "opaque"):
            #     linkOptions.opaque = newValue

        return linkOptions

    def __str__(self):
        result = '''
        Event Type = LinkUpdate
        first node_name = %s
        second_node_name = %s
        execution_delay = %s
        New Link Parameters:
        ''' % (self.first_node_name, self.second_node_name, self.execution_delay)

        for param, value in self.link_params.items():
            result += ("{} = {}\n".format(param, value))

            return result
