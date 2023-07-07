#!/usr/bin/env python3

# VMware Cloud Sizer Companion CLI - functions module
################################################################################
### Copyright 2023 VMware, Inc.
### SPDX-License-Identifier: MIT License
################################################################################

import sys
import json
from sizer_json import parse_excel_api, get_pdf_api, get_recommendation_api
from data_transform import data_describe, lova_conversion, rvtools_conversion, ps_filter, exclude_workloads, include_workloads, build_workload_profiles, build_recommendation_payload
from sizer_output import recommendation_transformer, csv_output, excel_output, pdf_output, powerpoint_output, terminal_output 


def describe_import(**kwargs):
    '''Triggered when user selects "view_only"'''
    print("Getting overview of environment. Only file type, input path and input file name will be used.")
    input_path = kwargs['input_path']
    ft = kwargs['file_type']
    fn = kwargs['file_name']
    output_path = kwargs['output_path']

    view_params = {"input_path":input_path,"file_name":fn, "output_path":output_path}
    
    match ft:
        case 'live-optics':
            csv_file = lova_conversion(**view_params)
        case 'rv-tools':
            csv_file = rvtools_conversion(**view_params)

    if csv_file is not None:
        data_describe(output_path,csv_file)
    else:
        print()
        print("Something went wrong.  Please check your syntax and try again.")
        sys.exit(1)
    sys.exit(0)


def default_import_sizing(**kwargs):
    '''Triggered when user selects "default sizing" using an import file"'''
    print("Using default parameters for sizing calculations.")
    input_path = kwargs['input_path']
    ft = kwargs['file_type']
    fn = kwargs['file_name']
    options = ['vm_placement', 'calculation_logs', 'output_format']

    rec_params = {}
    for i in options:
        if i in kwargs:
            option = kwargs[i]
        else:
            option = None
        rec_params[i] = option

    default_params = {"file_type":ft, "input_path":input_path, "file_name":fn}
    vms_json = parse_excel_api(**default_params)
    if vms_json is not None:
        sizer_request = json.dumps(vms_json['response']['sizerRequest'], indent=2)
        with open("output/default_recommendation_request.txt", "w") as f:
            print(sizer_request, file=f)
        rec_params['sizer_request'] = sizer_request
        get_recommendation(**rec_params)

    else:
        print()
        print("Something went wrong.  Please check your syntax and try again.")
        sys.exit(1)


def custom_import_sizing(**kwargs):
    ft = kwargs['file_type']
    fn = kwargs['file_name']
    input_path = kwargs['input_path']
    output_path = kwargs['output_path']

    # the following parameters will be used to build the payload contained in the 
    cloud_type = kwargs['cloud_type']
    cluster_type = kwargs['cluster_type']
    host_type = kwargs['host_type']
    storage_capacity = kwargs['storage_capacity']
    storage_type = kwargs['storage_type']
    storage_vendor = kwargs['storage_vendor']
    profile_type = kwargs['profile_type']
    pct_cpu = kwargs['percent_cpu']
    pct_mem = kwargs['percent_memory']
    fttFtmType = kwargs['data_protection']

    # build the payload parameter dictionary
    payload_params = {
        "output_path":output_path,
        "cloud_type":cloud_type,
        "host_type": host_type,
        "cluster_type":cluster_type,
        "storage_capacity":storage_capacity,
        "storage_type":storage_type,
        "storage_vendor":storage_vendor,
        "profile_type":profile_type,
        "cloudType":cloud_type,
        "pct_cpu":pct_cpu,
        "pct_mem":pct_mem,
        "fttFtmType":fttFtmType
        }

    # build the parameter dictionary for getting the recommendation
    options = ['vm_placement', 'calculation_logs', 'output_format']
    rec_params = {}
    for i in options:
        if i in kwargs:
            option = kwargs[i]
        else:
            option = None
        rec_params[i] = option

    # instantiate a list to be used in the payload parameter dictionary
    wp_file_list = []

    ingest_params = {"file_type":ft, "input_path":input_path, "file_name":fn, "output_path":output_path}
    match ft:
        case 'live-optics':
            csv_file = lova_conversion(**ingest_params)
        case 'rv-tools':
            csv_file = rvtools_conversion(**ingest_params)

    #transform parsed data according to arguments
    if csv_file is not None:

        if kwargs['power_state'] is not None:
            power_params = {"power_state":kwargs['power_state'], "output_path":output_path, "csv_file":csv_file}
            csv_file = ps_filter(**power_params)
        else:
            pass

        if kwargs['include_filter'] is not None:
            if kwargs['include_filter_field'] is None:
                print("You must specify BOTH a text string to use as a filter, AND field to filter by (vm_name, guest_os, cluster) when using an include filter.")
            else:
                inc_filter_params = {"include_filter":kwargs['include_filter'], "include_filter_field":kwargs['include_filter_field'], "output_path":output_path, "csv_file":csv_file}
                csv_file = include_workloads(**inc_filter_params)
        else:
            pass
        
        if kwargs['exclude_filter'] is not None:
            if kwargs['exclude_filter_field'] is None:
                print("You must specify BOTH a text string to use as a filter, AND field to filter by (vm_name, guest_os, cluster) when using an exclude filter.")
            else:
                ex_filter_params = {"exclude_filter":kwargs['exclude_filter'], "exclude_filter_field":kwargs['exclude_filter_field'], "output_path":output_path, "csv_file":csv_file}
                csv_file = exclude_workloads(**ex_filter_params)
        else:
            pass

        if kwargs['workload_profiles'] is not None:
            match kwargs['workload_profiles']:
                case "all_clusters":
                    profile_params = {"csv_file":csv_file, "workload_profiles":kwargs['workload_profiles'], "profile_list":kwargs['profile_list'], "include_remaining":kwargs['include_remaining'], "output_path":output_path}
                    wp_file_list = build_workload_profiles(**profile_params)

                case "some_clusters" | "os" | "vmName":
                    if kwargs['profile_list'] is None:
                        print("You must supply a list of one or more valid cluster names / guest operating systems / VM names.  Use './sizer-cli.py describe' for a summary of the environment, or review your file.")
                        sys.exit(1)
                    else:
                        profile_params = {"csv_file":csv_file, "workload_profiles":kwargs['workload_profiles'], "profile_list":kwargs['profile_list'], "include_remaining":kwargs['include_remaining'], "output_path":output_path}
                        wp_file_list = build_workload_profiles(**profile_params)
        else:
            pass

        # ensure either the last processed csv_file OR the list of workload profiles is stored as a common vairable to be used in the payload parameter dictionary
        if len(wp_file_list) == 0:
            wp_file_list = [csv_file]
        else:
            pass

        # add the list of files including the workloads to the payload parameter dictionary
        payload_params['wp_file_list'] = wp_file_list

        # build the recommendation payload
        sizer_request = build_recommendation_payload(**payload_params)

        # include the recommendation payload in the sizing request for the sizer
        rec_params['sizer_request'] = sizer_request

        # get the recommendation
        get_recommendation(**rec_params)
    
    else:
        print("Something went wrong.  Please check your syntax and try again.")
        sys.exit(1)


def get_recommendation(**kwargs):
    # take parsed / transformed data and get recommendation.
    sizer_request = kwargs['sizer_request']

    vp = kwargs['vm_placement']
    cl = kwargs['calculation_logs']
    output_format = kwargs['output_format']

    rec_params = {}
    rec_params['vp'] = vp
    rec_params["json_data"] = sizer_request

    json_raw = get_recommendation_api(**rec_params)
    if json_raw is None:
        print("Something went wrong.  Please check your syntax and try again.")
        sys.exit(1)
    else:
        pass

    # strip calculations out of the json, store for later use
    calcs = json_raw["calculationLog"]
    del json_raw["calculationLog"]

    # strip assumptions out of the json, store for later use
    assumps = json_raw["sizingAssumtions"]
    del json_raw["sizingAssumtions"]

    # take the rest of the json output and transform it
    output_json = recommendation_transformer(json_raw)
    output_params = {"recommendation":output_json, "calcs":calcs,"assumps":assumps,"cl":cl}
    match output_format:
        case "csv":
            print("Exporting recommendation to CSV.")
            print()
            print("enabled in a future release.")

        case "pdf":
            print("Exporting recommendation to PDF.")
            print()
            pdf_content = get_pdf_api(**rec_params)
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
