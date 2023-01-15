#!/usr/bin/env python3
import json
import pandas as pd
from pandas import json_normalize


def csv_output(**kwargs):
    print()
    print("enabled in a future release.")

def excel_output(**kwargs):
    print()
    print("enabled in a future release.")

def powerpoint_output(**kwargs):
    print()
    print("enabled in a future release.")

def terminal_output(**kwargs):
    json_data = kwargs["recommendation"]
    calcs = kwargs["calcs"]
    logs = kwargs["cl"]

    print(json.dumps(json_data['sddcList'][0], indent = 4))

    # print calculation logs if user
    if logs is True:
        print(calcs)
