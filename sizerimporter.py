#!/usr/bin/env python3

# VMware Cloud Sizer Companion CLI - main module
################################################################################
### Copyright 2023 VMware, Inc.
### SPDX-License-Identifier: MIT License
################################################################################


import argparse
from argparse import SUPPRESS
import sys
import json
from sizer_json import parse_excel, get_pdf, get_recommendation
from data_transform import data_describe, lova_conversion, rvtools_conversion, exclude_workloads, include_workloads, build_workload_profiles, build_recommendation_payload
from sizer_output import recommendation_transformer, csv_output, excel_output, pdf_output, powerpoint_output, terminal_output 

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
    Action to take:\n
    default - upload a LiveOptics / RVTools file and immediately receive a sizing recommendation with no transformation of data\n
    custom - transform the data prior to a recommendation - e.g. include or exclude workloads, maintain existing cluster mappings, create profiles, etc., \n
    view_only - ingest the file and display the ingested VM inventory.  Used for a quick look at the data.''',
    metavar='')

    file_hander = ap.add_argument_group('File handling', "Define arguments to manage file handling.")
    file_hander.add_argument("-fn", "--file_name", required=True, help="The file containing the VM inventory to be imported.")
    file_hander.add_argument("-ft", "--file_type", required=True, choices=['rv-tools', 'live-optics'], type=str.lower, help="Which tool completed the data collection? (choices: %(choices)s) ", metavar='')

    preferences = ap.add_argument_group('Recommendation preferences', "Define arguments to manage how recommendation is calculated.")
    preferences.add_argument("-ct", "--cloud_type", choices=['VMC_ON_AWS', 'GCVE'], default = "VMC_ON_AWS", type=str.upper, help="Which cloud platform are you sizing for? (choices: %(choices)s) (default: %(default)s)", metavar='')
    # preferences.add_argument('-c', "--capacity",  choices = ["configured", "used"], type=str.lower, help = "Use to specify whether to use VMDK configured storage, or only that utilized by the guest. (choices: %(choices)s) ", metavar='')
    preferences.add_argument("-vp", "--vm_placement", action= "store_true", help="Use to show vm placement. Default is True - results will, by default does not include VM placement data.")

    workload_filters = ap.add_argument_group('Workload filtering options', "Define arguments to filter workloads in file before submitting to Sizer for recommendation.")
    workload_filters.add_argument('-ef', '--exclude_filter', nargs = '+', help = 'A list of text strings used to identify workloads to exclude.')
    workload_filters.add_argument('-eff', '--exclude_filter_field', choices = ['cluster','os','vmName'], help = "The column/field used for exclusion filtering. (choices: %(choices)s) ", metavar='')
    workload_filters.add_argument('-if', '--include_filter', nargs = '+', help = 'A list of text strings used to identify workloads to keep.')
    workload_filters.add_argument('-iff', '--include_filter_field', choices = ['cluster','os','vmName'], help = "The column/field used for inclusion filtering. (choices: %(choices)s) ", metavar='')
    workload_filters.add_argument('-ps', "--power_state",  choices = ["a", "p", "ps"], type=str.lower, help = "Use to specify whether to include (a)ll VM, only those (p)owered on, or powered on and suspended (ps). (choices: %(choices)s) ", metavar='')

    transformations = ap.add_argument_group('Workload profile options', "Define arguments to create workload profiles / groups before submitting to Sizer for recommendation.")
    transformations.add_argument('-wp', '--workload_profiles', choices=["all_clusters", "custom_clusters", "guest_os", "vm_name"], type=str.lower, help = "Use to create workload profiles based on the selected grouping. (choices: %(choices)s)", metavar='')
    transformations.add_argument('-pl', '--profile_list', nargs= '+', help = "A list of text strings used to filter workloads for the creation of workload profiles.  Use '--workload_profiles' to identify the field used for grouping.")
    transformations.add_argument('-ir', '--include_remaining', action= 'store_true', help= 'Use to indicate you wish to keep remaining workloads - default is to discard.')   

    output_group = ap.add_argument_group('Output', "Define arguments to alter how results are shown.")
    output_group.add_argument("-logs", "--calculation_logs", action= "store_true", help="Use to show calculation logs. Default is False - results will not, by default, show calculation logs.")
    output_group.add_argument("-o", "--output_format", choices=["csv", "pdf", "ppt","xls"], help="Select output format Default is none.  (choices: %(choices)s) ", metavar='')

    args = ap.parse_args()

    #Identify type of collection to call correct module
    action = args.action

    #create arguments for file parsing
    input_path = 'input/'
    output_path = 'output/'
    
    fn = args.file_name
    ft = args.file_type
    power_state = args.power_state
    # cap = args.capacity
    # susvm = args.suspended

    # create arguments for recommendation
    ct = args.cloud_type
    vp = args.vm_placement

    # create arguments for transformations
    exclude_filter = args.exclude_filter
    exclude_filter_field = args.exclude_filter_field
    include_filter = args.include_filter
    include_filter_field = args.include_filter_field
    workload_profiles = args.workload_profiles
    profile_list = args.profile_list
    include_remaining = args.include_remaining

    # create arguments for output options
    cl = args.calculation_logs
    output_format = args.output_format

    match action:
        case "default":
            print("Using default parameters for sizing calculations.")
            default_params = {"file_type":ft, "input_path":input_path, "file_name":fn}
            vms_json = parse_excel(**default_params)
            if vms_json is not None:
                sizer_request = json.dumps(vms_json['response']['sizerRequest'])
            else:
                print()
                print("Something went wrong.  Please check your syntax and try again.")
                sys.exit(1)

        case "custom":
            # ingest file
            ingest_params = {"file_type":ft, "input_path":input_path, "file_name":fn}
            match ft:
                case 'live-optics':
                    csv_file = lova_conversion(**ingest_params)
                case 'rv-tools':
                    csv_file = rvtools_conversion(**ingest_params)

            #transform parsed data according to arguments
            if csv_file is not None:

                if exclude_filter is not None and exclude_filter_field is not None:
                    ex_filter_params = {"exclude_filter":exclude_filter, "exclude_filter_field":exclude_filter_field, "output_path":output_path, "csv_file":csv_file}
                    csv_file = exclude_workloads(**ex_filter_params)
                else:
                    print("You must specify BOTH a text string to use as a filter, AND field to filter by (vm_name, guest_os, cluster) when using an exclude filter.")

                if include_filter is not None and include_filter_field is not None:
                    inc_filter_params = {"include_filter":include_filter, "include_filter_field":include_filter_field, "output_path":output_path, "csv_file":csv_file}
                    csv_file = include_workloads(**inc_filter_params)
                else:
                    print("You must specify BOTH a text string to use as a filter, AND field to filter by (vm_name, guest_os, cluster) when using an include filter.")
                
                if workload_profiles is not None:
                    match workload_profiles:
                        case "all_clusters":
                            profile_params = {"csv_file":csv_file, "workload_profiles":workload_profiles, "output_path":output_path}
                            wp_file_list = build_workload_profiles(**profile_params)

                        case "some_clusters" | "guest_os" | "vm_name":
                            if profile_list is None:
                                print("You must supply a list of one or more valid cluster names / guest operating systems / VM names.  Use './sizerimpoter -a view_only' for a summary of the environment, or review your file.")
                                sys.exit(1)
                            else:
                                profile_params = {"csv_file":csv_file, "workload_profiles":workload_profiles, "profile_list":profile_list, "include_remaining":include_remaining, "output_path":output_path}
                                wp_file_list = build_workload_profiles(**profile_params)

                payload_params = {"output_path":output_path, "csv_file":csv_file, "wp_file_list":wp_file_list, "cloudType":ct}
                sizer_request = build_recommendation_payload(**payload_params)
            
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
                data_describe(vm_data)
            else:
                print()
                print("Something went wrong.  Please check your syntax and try again.")
                sys.exit(1)
            sys.exit(0)

    # take parsed / transformed data and get recommendation.
    rec_params = {}
    rec_params['vp'] = vp
    rec_params["json_data"] = sizer_request

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

        case "pdf":
            print("Exporting recommendation to PDF.")
            print()
            pdf_content = get_pdf(**rec_params)
            pdf_output(pdf_content)
            
        case "ppt":
            print("Exporting recommendation to PowerPoint.")
            print()
            print("enabled in a future release.")

        case "xls":
            print("Exporting recommendation to Excel.")
            print()
            print("enabled in a future release.")

    terminal_output(**output_params)

if __name__ == "__main__":
    main()
