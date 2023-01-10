#!/usr/bin/env python3

#VMC Sizer Importer for Python

import argparse
import requests
import sys
import json
from sizer_json import get_access_token, parse_excel, get_recommendation
from lova_custom import lova_conversion
# from rv_custom import rv_conversion

def main():
    ap = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, epilog="Welcome to the VMC Sizer Import for Python")
    ap.add_argument("-a", "--action", choices = ["default", "custom"], required = True, help = "Action to take - default: use the Sizer to parse a LiveOptics / RVTools file, or use the custom profiles this scripts builds.")
    ap.add_argument("-f", "--file_name", required=True, help="The file containing the VM inventory to be imported.")
    ap.add_argument("-ft", "--file_type", required=True, choices=['rvtools', 'live-optics', 'movere'], help="Which tool completed the data collection, RVTools, Live Optics, or Movere?")
    ap.add_argument('-s', "--scope",  choices = ["all", "powered on"], required = True, help = "Specify whether to include all VM, or only those powered on.")
    ap.add_argument('-c', "--capacity",  choices = ["configured", "used"], required = True, help = "Specify whether to use VMDK configured storage, or only that utilized by the guest.")
    ap.add_argument("-rt", "--refresh_token", required=False, help="The CSP API refresh token")

    # Manual / local calculations?
    # direct upload - send to VMC Sizer?
    # cluster mapping?


    # *** We will need to add some arguments if we want to allow for techniques that gather data across multiple files, like Movere 
    # ap.add_argument("-part", "--partition_file", required=True, help="The file containing the VM partitions to be imported.")
    # ap.add_argument("-perf", "--performance_file", required=True, help="The file containing the VM partitions to be imported.")

    args = ap.parse_args()

    #Set refresh token to authenticate / authorize use of sizer API
    rt = args.refresh_token
    access_token = get_access_token(rt)

    #Identify type of collection to call correct module
    action = args.action
    ft = args.file_type

    #create keyword argument dictionary to call conversion modules
    fn = args.file_name
    scope = args.scope
    cap = args.capacity

    params = {"file_type":ft, "file_name":fn, "scope":scope, "cap":cap, "access_token":access_token}

    match action:
        case "default":
            if ft == 'live-optics':
                vms_json = parse_excel(**params)
                print(vms_json)
                # if vms_json is not None:
                #     recommendation_payload = vms_json["response"]["key"]["request"]
                #     params["json_payload"] = recommendation_payload
                #     recommendation = get_recommendation(**params)
                #     print(recommendation)
                # else:
                #     print()
                #     print("Something went wrong.  Please check your syntax and try again.")
        case "custom":
            if ft == 'live-optics':
                vms_json = lova_conversion(**params)
                if vms_json is not None:
                    print(vms_json)
                else:
                    print()
                    print("Something went wrong.  Please check your syntax and try again.")

if __name__ == "__main__":
    main()
