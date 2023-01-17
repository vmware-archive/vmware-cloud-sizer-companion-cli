#!/usr/bin/env python3

#VMC Sizer Importer for Python

import argparse
from argparse import SUPPRESS
import requests
import sys
import json
from sizer_json import parse_excel, get_recommendation #, get_access_token 
from data_transform import lova_conversion, rvtools_conversion, workload_profiles
from sizer_output import recommendation_transformer, csv_output, excel_output, powerpoint_output, terminal_output 

# from rv_custom import rv_conversion

def main():
    class MyFormatter(argparse.RawDescriptionHelpFormatter):
        def __init__(self,prog):
            super(MyFormatter, self).__init__(prog,max_help_position=10)

    ap = argparse.ArgumentParser(
                    prog = 'sizerimporter.py',
                    description = 'A Command-line companion for the VMware Cloud Sizer.',
                    formatter_class=MyFormatter, usage=SUPPRESS,
                    epilog='''
                    Welcome to the VMC Sizer Import for Python!! \n\n
                    This tools is used to help you send and receive sizing recommendations from the VMware Cloud Sizer quickly and reliably, with a number of available options.
                    The script accepts files from either RVTools or LiveOptics (DO NOT MODIFY the original files).
                    The script will first send the file up to the sizer for parsing, and return a payload containing a parsed inventory of the workloads contained in the file.
                    Next, based on the arguments provided at the command line, the script will submit the data to receive a recommendation. \n\n
                    ''')

    ap.add_argument("-a", "--action", choices = ["default", "custom", "view_only"], default = "view_only", type=str.lower, required = True, help = '''
    Action to take:
    default - upload a LiveOptics / RVTools file and immediately receive a sizing recommendation with no transformation of data
    custom - transform the data prior to a recommendation - e.g. maintain existing cluster mappings, 
    view_only - ingest the file and display the ingested VM inventory.  Used for a quick look at the data.''',
    metavar='')

    file_hander = ap.add_argument_group('File handling', "Define arguments to manage file handling.")
    file_hander.add_argument("-fn", "--file_name", required=True, help="The file containing the VM inventory to be imported.")
    file_hander.add_argument("-ft", "--file_type", required=True, choices=['rv-tools', 'live-optics'], type=str.lower, help="Which tool completed the data collection? (choices: %(choices)s) ", metavar='')

    preferences = ap.add_argument_group('Sizer preferences', "Define arguments to manage how recommendation is calculated.")
    preferences.add_argument("-ct", "--cloud_type", required=True, choices=['VMC_ON_AWS', 'GCVE'], default = "VMC_ON_AWS", type=str.upper, help="Which cloud platform are you sizing for? (choices: %(choices)s) (default: %(default)s)", metavar='')
    preferences.add_argument("-novp", "--novm_placement", action= "store_false", help="Use to show vm placement. Default is True - results will, by default, include VM placement data.")
    # preferences.add_argument('-c', "--capacity",  choices = ["configured", "used"], type=str.lower, help = "Use to specify whether to use VMDK configured storage, or only that utilized by the guest. (choices: %(choices)s) ", metavar='')
    # preferences.add_argument('-s', "--scope",  choices = ["all", "powered on"], type=str.lower, help = "Use to specify whether to include all VM, or only those powered on. (choices: %(choices)s) ", metavar='')
    # preferences.add_argument('-sus', '--suspended', action = 'store_true', help = "Use to specify the parser should include suspended virtual machines.")

    transformations = ap.add_argument_group('Transformation Options', "Define arguments to transform data in file before submitting to Sizer for recommendation.")
    transformations.add_argument('-pc', '--profile_config', choices=["clusters"], type=str.lower, help = "Use to create workload profiles based on the selected grouping. (choices: %(choices)s)", metavar='')
    # transformations.add_argument('-pc', '--profile_config', choices=["clusters", "virtual_datacenter", "resource_pools", "folders"], type=str.lower, help = "Use to create workload profiles based on the selected grouping.", metavar='')

    output_group = ap.add_argument_group('Output Format', "Define arguments to alter how results are shown.")
    output_group.add_argument("-logs", "--calculation_logs", action= "store_true", help="Use to show calculation logs. Default is False - results will not, by default, show calculation logs.")
    output_group.add_argument("-of", "--output_format", choices=["csv","Excel","pdf","PowerPoint", "terminal"], help="Use to show calculation logs.  (choices: %(choices)s) ", metavar='')

    # currently access to sizer is ungated. If token is necessary, uncomment this argument as well as the token section below.
    # ap.add_argument("-rt", "--refresh_token", required=False, help="The CSP API refresh token")

    args = ap.parse_args()

    # argument for refresh token used to retreive access token
    # rt = args.refresh_token

    #Identify type of collection to call correct module
    action = args.action

    #create arguments for file parsing
    input_path = 'input/'
    fn = args.file_name
    ft = args.file_type
    # scope = args.scope
    # cap = args.capacity
    # susvm = args.suspended

    # create arguments for recommendation
    ct = args.cloud_type
    vp = args.novm_placement
    profile_config = args.profile_config

    # create arguments for output options
    cl = args.calculation_logs
    output_format = args.output_format

    if profile_config is not None:
        if ft == "live-optics" and (profile_config == "resource_pools" or profile_config == "folders"):
            print("Note that grouping by resource pools or folders is only available with RVTools data.")
            print("Please try again.")
            sys.exit(1)
        else:
            pass
    else:
        pass

    # Uncomment this section to retrieve an access token in the event the services is gated.
    # Set refresh token to authenticate / authorize use of sizer API
    # access_token = get_access_token(rt)
    # if access_token is None:
    #     print("Something went wrong.  Please check your syntax and your refresh token and try again.")
    #     sys.exit(1)

    # Use this params section if tokens are necessary
    # parse_params = {"file_type":ft,"input_path":input_path, "file_name":fn, "scope":scope, "cap":cap, "susvm":susvm, "access_token":access_token}

    # Define parameters sent to function
    # params = {"file_type":ft, "cloud_type":ct, "input_path":input_path, "file_name":fn, "scope":scope, "cap":cap, "susvm":susvm}
    params = {"file_type":ft, "cloud_type":ct, "input_path":input_path, "file_name":fn}

    match action:
        case "default":
            print("Using default parameters for sizing calculations.")
            vms_json = parse_excel(**params)
            if vms_json is not None:
                recommendation_payload = json.dumps(vms_json['response']['sizerRequest'])
            else:
                print()
                print("Something went wrong.  Please check your syntax and try again.")
                sys.exit(1)

        case "custom":
            #transform parsed data according to arguments
            if profile_config is None:
                print("You must select a profile configuration option when using 'custom'.")
                sys.exit(1)
            else:
                print("Using custom workload profiles.")
                print()
            if ft == 'live-optics':
                vm_data = lova_conversion(**params)
            elif ft == 'rv-tools':
                vm_data = rvtools_conversion(**params)
            if vm_data is not None:
                # custom_params = {"vm_data":vm_data, "ct":ct, "scope":scope, "cap":cap, "susvm":susvm, "profile_config":profile_config}
                custom_params = {"vm_data":vm_data, "ct":ct, "profile_config":profile_config}
                recommendation_payload = workload_profiles(**custom_params)
            else:
                print("Something went wrong.  Please check your syntax and try again.")
                sys.exit(1)

        case "view_only":
            print("Getting overview of environment. Only file type, input path and input file name will be used.")
            view_params = {"input_path":input_path, "file_name":fn}
            
            if ft == 'live-optics':
                vm_data = lova_conversion(**view_params)
            elif ft == 'rv-tools':
                vm_data = rvtools_conversion(**view_params)

            if vm_data is not None:
                print(vm_data)
            else:
                print()
                print("Something went wrong.  Please check your syntax and try again.")
                sys.exit(1)
            sys.exit(0)
        

    # take parsed / transformed data and get recommendation.
    rec_params = {}
    rec_params['vp'] = vp
    rec_params["json_data"] = recommendation_payload

    json_raw = get_recommendation(**rec_params)
    if json_raw is None:
        print("Something went wrong.  Please check your syntax and try again.")
        sys.exit(1)
    else:
        pass

    calcs = json_raw["calculationLog"]
    del json_raw["calculationLog"]

    output_json = recommendation_transformer(json_raw)
    output_params = {"recommendation":output_json, "calcs":calcs,"cl":cl}
    match output_format:
        case "csv":
            print("Exporting recommendation to CSV.")
            print()
            print("enabled in a future release.")

        case "excel":
            print("Exporting recommendation to Excel.")
            print()
            print("enabled in a future release.")

        case "powerpoint":
            print("Exporting recommendation to PowerPoint.")
            print()
            print("enabled in a future release.")

        case "terminal":
            print("Exporting recommendation to terminal.")
            terminal_output(**output_params)

if __name__ == "__main__":
    main()
