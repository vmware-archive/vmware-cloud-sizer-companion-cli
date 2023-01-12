#!/usr/bin/env python3

#VMC Sizer Importer for Python

import argparse
import requests
import sys
import json
from sizer_json import parse_excel, get_recommendation #, get_access_token 
from lova_custom import lova_conversion
from rvtools_custom import rvtools_conversion
from parse_custom import workload_profiles

# from rv_custom import rv_conversion

def main():
    ap = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, epilog='''
    Welcome to the VMC Sizer Import for Python!! \n\n
    This tools is used to help you send and receive sizing recommendations from the VMware Cloud Sizer quickly and reliably, with a number of available options.
    The script accepts files from either RVTools or LiveOptics (DO NOT MODIFY the original files).
    The script will first send the file up to the sizer for parsing, and return a payload containing a parsed inventory of the workloads contained in the file.
    Next, based on the arguments provided at the command line, the script will submit the data to receive a recommendation. \n\n
    ''')

    # Define arguments to manage file handling.
    ap.add_argument("-a", "--action", choices = ["default", "custom", "view"], default = "default", type=str.lower, help = "Action to take - default: use the Sizer to parse a LiveOptics / RVTools file, use the custom profiles this scripts builds, just get an overview of the environment.")
    ap.add_argument("-f", "--file_name", required=True, help="The file containing the VM inventory to be imported.")
    ap.add_argument("-ft", "--file_type", required=True, choices=['rv-tools', 'live-optics', 'movere'], type=str.lower, help="Which tool completed the data collection, RVTools, Live Optics, or Movere?")

    # Define arguments to alter how results are shown.
    ap.add_argument("-l", "--calculation_logs", action= "store_true", help="Alters how recommendation results are shown. Use to show calculation logs. Default is False - results will not, by default, show calculation logs.")
    ap.add_argument("-novp", "--novm_placement", action= "store_false", help="Alters how recommendation results are shown. Use to show vm placement. Default is True - results will, by default, include VM placement data.")

    # Define arguments to filter data sent to file adapter for parsing.
    ap.add_argument('-s', "--scope",  choices = ["all", "powered on"], required = True, type=str.lower, help = "Filters data sent for parsing. Use to specify whether to include all VM, or only those powered on.")
    ap.add_argument('-c', "--capacity",  choices = ["configured", "used"], required = True, type=str.lower, help = "Filters data sent for parsing. Use to specify whether to use VMDK configured storage, or only that utilized by the guest.")
    ap.add_argument('-sus', '--suspended', action = 'store_true', help = "Filters data sent for parsing. Use to specify the parser should include suspended virtual machines.")

    # Define arguments to transform data before asking for recommendation.
    ap.add_argument('-pc', '--profile_config', choices=["clusters", "virtual datacenter", "resource pools", "folders"], type=str.lower, help = "Transforms data sent for recommendation.  Use to specify to create workload profiles based on the selected grouping.  Note that grouping by resource pool or folder is only available with RVTools data.")

    # currently access to sizer is ungated. If token is necessary, uncomment this argument as well as the token section below.
    # ap.add_argument("-rt", "--refresh_token", required=False, help="The CSP API refresh token")

    # *** We will need to add some arguments if we want to allow for techniques that gather data across multiple files, like Movere 
    # ap.add_argument("-part", "--partition_file", required=True, help="The file containing the VM partitions to be imported.")
    # ap.add_argument("-perf", "--performance_file", required=True, help="The file containing the VM partitions to be imported.")
    # ap.add_argument("-net", "--netstat_file", required=True, help="The file containing the netstat connection information to be imported.")
    # add option for suspended VM as well?

    args = ap.parse_args()

    # argument for refresh token used to retreive access token
    # rt = args.refresh_token

    #Identify type of collection to call correct module
    action = args.action

    #create arguments for file parsing
    ft = args.file_type
    input_path = 'input/'
    fn = args.file_name
    scope = args.scope
    cap = args.capacity
    susvm = args.suspended

    # create arguments for recommendation
    cl = args.calculation_logs
    vp = args.novm_placement
    profile_config = args.profile_config

    # Uncomment this section to retrieve an access token in the event the services is gated.
    # Set refresh token to authenticate / authorize use of sizer API
    # access_token = get_access_token(rt)
    # if access_token is None:
    #     print("Something went wrong.  Please check your syntax and your refresh token and try again.")
    #     sys.exit(1)

    # Use this params section if tokens are necessary
    # parse_params = {"file_type":ft,"input_path":input_path, "file_name":fn, "scope":scope, "cap":cap, "susvm":susvm, "access_token":access_token}

    # Define parameters sent to parser
    parse_params = {"file_type":ft,"input_path":input_path, "file_name":fn, "scope":scope, "cap":cap, "susvm":susvm}

    vms_json = parse_excel(**parse_params)
    if vms_json is not None:
        parsed_data = json.dumps(vms_json['response']['sizerRequest'])
    else:
        print()
        print("Something went wrong.  Please check your syntax and try again.")
        sys.exit(1)

    match action:
        case "default":
            print("Using default parameters for sizing calculations.")
            recommendation_payload = parsed_data

        case "custom":
            #transform parsed data according to arguments
            print("Using custom workload profiles.")

            # Define parameters sent to recommendation engine for custom data transformation
            custom_params = {}
            custom_params['parsed_data'] = parsed_data
            custom_params["profile_config"] = profile_config
            recommendation_payload = workload_profiles(**custom_params)
            sys.exit(0)

        case "view":
            print("Getting overview of environment. Only file type, input path and input file name will be used.")
            custom_params = {"input_path":input_path, "file_name":fn}
            if ft == 'live-optics':
                vms_json = lova_conversion(**custom_params)
                if vms_json is not None:
                    print(vms_json)
                else:
                    print()
                    print("Something went wrong.  Please check your syntax and try again.")

            if ft == 'rv-tools':
                vms_json = rvtools_conversion(**custom_params)
                if vms_json is not None:
                    print(vms_json)
                else:
                    print()
                    print("Something went wrong.  Please check your syntax and try again.")
            sys.exit(0)
        

    # take unaltered, parsed data OR transformed data and get recommendation.
    rec_params = {}
    rec_params['vp'] = vp
    rec_params["json_data"] = recommendation_payload

    recommendation = get_recommendation(**rec_params)
    if recommendation is None:
        print("Something went wrong.  Please check your syntax and try again.")
        sys.exit(1)
    else:
        pass

    calcs = recommendation["calculationLog"]
    del recommendation["calculationLog"]
    print(json.dumps(recommendation, indent = 4))

    # print calculation logs if user
    if cl is True:
        print(calcs)

if __name__ == "__main__":
    main()
