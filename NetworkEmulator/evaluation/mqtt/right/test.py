#!/usr/bin/python

import datetime
from datetime import datetime


sending_time = "2019-08-31 16:30:36.998898"
receipt_time = "2019-08-31 16:46:37.907559"

sending_time = datetime.strptime(sending_time, "%Y-%m-%d %H:%M:%S.%f")
receipt_time = datetime.strptime(receipt_time, "%Y-%m-%d %H:%M:%S.%f")

duration = receipt_time - sending_time

print(duration.total_microseconds())
