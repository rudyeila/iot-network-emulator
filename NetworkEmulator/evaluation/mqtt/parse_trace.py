import yaml

def create_config(node1, node2, times, RTT, output_file):

    dict_list = []
    for time, rtt in zip(times, RTT):
        yml = {
                "event":
                    {
                        "type": "LinkUpdate",
                        "time": "{} seconds".format(time),
                        "parameters":
                            {
                                "node1": node1,
                                "node2": node2,
                                "link_params":
                                    {
                                        "delay": rtt*1000 # convert ms to microseconds by multiplying by thousan and then divide by 2 to get one way delay
                                    }
                            }
                    }
            }
        dict_list.append(yml)
    with open(output_file, 'w+') as outfile:
        yaml.dump_all(dict_list, outfile, default_flow_style=False)

def parse_file(path):
    with open(path, 'r') as f:
        lines = f.readlines()
    times = [] # in seconds
    rtt = [] # in microseconds
    for line in lines:
        seq, RTT = line.split(' ')
        times.append(float(seq))
        rtt.append(float(RTT))

    node1 = "left"
    node2 = "right"
    output = "broker_event_config.yml"

    create_config(node1, node2, times, rtt, output)

if __name__ == '__main__':
    parse_file("results5.txt")
