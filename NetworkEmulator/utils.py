# NetworkEmulator/utils.py

'''
    This modules contains some utility methods that are used all over the program
'''
import socket
from core.emulator.enumerations import NodeTypes
from core.emulator.emudata import LinkOptions


def get_LinkOptions(link_params):
    '''This class is used derive new LinkOptions() from the LinkEvent object.
    LinkOptions are used by CORE to specify delays, bandwidth etc for a specific link.

    :returns: linkOptions, a convenience object used by core to specify link values (delay, bandwidth, jitter etc.)
    :rtype: LinkOptions
    '''

    linkOptions = LinkOptions()
    for param, value in link_params.items():
        parameter = param.lower()

        if (value):
            newValue = float(value)
        else:
            newValue = value

        if (parameter == "session"):
            linkOptions.session = newValue
        elif (parameter == "delay"):
            linkOptions.delay = newValue
        elif (parameter == "bandwidth"):
            linkOptions.bandwidth = newValue
        # Packet Loss Rate
        elif (parameter == "loss"):
            linkOptions.per = newValue
        # Packet duplication rate
        elif (parameter == "duplication" or parameter == "dup"):
            linkOptions.dup = newValue
        elif (parameter == "jitter"):
            linkOptions.jitter = newValue

    return linkOptions


def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def get_cmd_command(command):
    ''' takes a string of a terminal command, and returns the individual words as a list '''
    return command.split()


def getCoreNodeType(type_name):
    ''' Get node types as "understood" by the CORE emulator

        In other words, translate types from our simple language to the CORE language

    '''
    if (type_name.lower() == "switch"):
        type = NodeTypes.SWITCH
    elif (type_name.lower() == "hub"):
        type = NodeTypes.HUB
    elif(type_name.lower() == "rj45" or type_name.lower() == "phys" or type_name.lower() == "physical"):
        type = NodeTypes.RJ45
    else:
        type = NodeTypes.DEFAULT

    return type


def convert_time_to_seconds(timeValue, timeUnit):
    """Converts time values (for the queue) to seconds (1 ms will become 0.001 second for example)

    :param timeValue: The actual time value in the specified unit
    :param timeUnit: The unit of time (ns, us, ms, min, hr)
        (default is seconds)
    :returns: timeInSeconds, the time value converted to seconds
    :rtype: float
    """
    timeInSeconds = 0.0
    if (timeUnit.lower == "s" or timeUnit.lower == "second" or timeUnit.lower == "seconds" or timeUnit.lower == "sec"):
        timeInSeconds = timeValue
    elif (timeUnit.lower == "ns" or timeUnit.lower == "nanosecond" or timeUnit.lower == "nanoseconds"):
        timeInSeconds = timeValue / 0.000000001
    elif (timeUnit.lower == "us" or timeUnit.lower == "microsecond" or timeUnit.lower == "microseconds"):
        timeInSeconds = timeValue / 0.000001
    elif (timeUnit.lower == "ms" or timeUnit.lower == "millisecond" or timeUnit.lower == "milliseconds"):
        timeInSeconds = timeValue / 0.001
    elif (timeUnit.lower == "min" or timeUnit.lower == "mins" or timeUnit.lower == "minute" or timeUnit.lower == "minutes" or timeUnit.lower == "m"):
        timeInSeconds = timeValue * 60.0
    elif (timeUnit.lower == "hr" or timeUnit.lower == "hour" or timeUnit.lower == "hours" or timeUnit.lower == "hrs" or timeUnit.lower == "h"):
        timeInSeconds = timeValue * 3600
    else:
        timeInSeconds = timeValue

    return timeInSeconds
