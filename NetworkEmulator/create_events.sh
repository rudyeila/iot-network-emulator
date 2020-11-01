#!/bin/bash
# Example of using the config.py script.

# This example defined 4 LinkEvents on the left-right link. The events are executed with 10 second time intervals with the first event at time 0.
# The bandwidth parameters is influenced and the first value is 1,000,000 bps and is incremented by 10,000,000 bps with every events. 
python config.py --output evaluation/bandwidth/bandwidth_events.yml --node1 left --node2 right --num-events 4 --start-time 0 --time-offset 10 --parameter bandwidth --start-value 1000000 --value-increment 10000000
