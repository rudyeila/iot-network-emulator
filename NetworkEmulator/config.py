'''
This is a simple script that can be used to create event configuration files for the scheduler. Refer to the console help (python config.py -h).

In a nutshell, you can use this script to define 'n' events, the node or link the events belong to, the parameters you want to influence, the start value of the parameters,
a discrete increment, as well as the time of the first events and the time interval at which the events should occur.

This is only a simple script as mentioned, but it can be used for testing purposes.
'''

import argparse
import yaml


def create_yml(args):
    num_events = args.num_events
    output_file = args.output
    node1 = args.node1
    node2 = args.node2
    start_time = args.start_time
    time_offset = args.time_offset
    parameter = args.parameter
    start_value = args.start_value
    value_increment = args.value_increment

    next_time = start_time
    next_value = start_value
    dict_list = []
    for i in range(0, num_events):
        yml = {
            "event":
            {
                "type": "LinkUpdate",
                        "time": "{} seconds".format(next_time),
                        "parameters":
                            {
                                "node1": node1,
                                "node2": node2,
                                "link_params":
                                    {
                                        "delay": next_value
                                    }
                        }
            }
        }
        dict_list.append(yml)

        next_time += time_offset
        next_value += value_increment
    with open(output_file, 'w') as outfile:
        yaml.dump_all(dict_list, outfile, default_flow_style=False)


def main():
    parser = argparse.ArgumentParser(
        description='Create event configuration file')
    parser.add_argument('--num-events', '-n', type=int,
                        help='Number of events you want to create')
    parser.add_argument('--output', '-o', type=str, help='output file name')
    parser.add_argument('--node1', '-n1', type=str, help='name of node1')
    parser.add_argument('--node2', '-n2', type=str, help='name of node2')
    parser.add_argument('--start-time', '-st', type=float,
                        help='time (in seconds) for the first event')
    parser.add_argument('--time-offset', '-to', type=float,
                        help='interval (in seconds) between each event')
    parser.add_argument('--parameter', '-p', type=str,
                        help='parameter to modify in the event')
    parser.add_argument('--start-value', '-sv', type=float,
                        help='parameter value in the first event')
    parser.add_argument('--value-increment', '-v', type=float,
                        help='value increase amount with each event')

    args = parser.parse_args()

    create_yml(args)


if __name__ == "__main__":
    main()
