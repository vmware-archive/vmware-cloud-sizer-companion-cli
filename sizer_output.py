#!/usr/bin/env python3

# VMware Cloud Sizer Companion CLI - output module
################################################################################
### Copyright 2023 VMware, Inc.
### SPDX-License-Identifier: MIT License
################################################################################

import json
import pandas as pd
from pandas import json_normalize
from prettytable import PrettyTable
import time

def generate_table(results):
    """Generates a 'prettytable' using a JSON payload; automatically uses the dictionary keys in the payload as column headers."""
    keyslist = list(results[0].keys())
    table = PrettyTable(keyslist)
    for dct in results:
        table.add_row([dct.get(c, "") for c in keyslist])
    return table


def recommendation_transformer(json_data):
    '''Extracts the data from the recommendation into discrete dataframes / arrays to be displayed on the screen.'''
    # create dict for SDDC overview
    overview_df = pd.json_normalize(json_data['sddcList'][0]['clusterList']['sazClusters']['hostBreakupList'][0])
    overview_df = overview_df.transpose()

    # extract vm exceptions
    if 'vmExceptions' in json_data['sddcList'][0]:
        vm_exceptions = (json_data['sddcList'][0]['vmExceptions']['vmExceptionInfo'])
        limited_compat = (json_data['sddcList'][0]['vmExceptions']['limitedHostCompatibility'])
    else:
        vm_exceptions = None
        limited_compat = None

    #create array objects to be returned
    cluster_json = {}
    vm_json = {}

    #extract clusters and virtual machines into separate arrays
    clusters = (json_data['sddcList'][0]['clusterList']['sazClusters']['clusterInfoList'])
    for count, cluster in enumerate(clusters, start=0):
        cluster_id = f'cluster_{count}'
        df_host_list = pd.json_normalize(cluster, record_path =['hostList'], max_level=1)
        df_host_list.drop('vmList', axis=1, inplace=True)
        cluster_json[cluster_id] = df_host_list

        #enumerate VMs in the cluster
        vm_list = []
        hosts = (json_data['sddcList'][0]['clusterList']['sazClusters']['clusterInfoList'][count]['hostList'])
        for hostcount, host in enumerate(hosts):
            vms = (json_data['sddcList'][0]['clusterList']['sazClusters']['clusterInfoList'][count]['hostList'][hostcount]['vmList'])
            if vms is not None:
                for vmcount, vm in enumerate(vms):
                    vm_list.append(vm['vmName'])
        vm_json[cluster_id] = vm_list

    output_array = {}
    output_array["overview"] = overview_df
    output_array["cluster_json"] = cluster_json
    output_array["vm_json"] = vm_json
    output_array['vm_exceptions'] = vm_exceptions
    output_array['limited_compat'] = limited_compat

    return output_array


def csv_output(**kwargs):
    print()
    print("enabled in a future release.")


def excel_output(**kwargs):
    print()
    print("enabled in a future release.")


def pdf_output(pdf_content):
    timestr = time.strftime("%Y%m%d-%H%M%S")
    file_name = f'VMC_Sizer_report_{timestr}.pdf'
    with open(f'output/{file_name}', 'wb') as f:
        f.write(pdf_content)
    return file_name


def powerpoint_output(**kwargs):
    print()
    print("enabled in a future release.")


def terminal_output(**kwargs):
    calcs = kwargs['calcs']
    logs = kwargs['cl']
    overview = kwargs['recommendation']['overview']
    cluster_json =  kwargs['recommendation']['cluster_json']
    vm_json =  kwargs['recommendation']['vm_json']
    vm_exceptions = kwargs['recommendation']['vm_exceptions']
    limited_compat = kwargs['recommendation']['limited_compat']

    print()
    print(overview)

    for id, cluster in cluster_json.items():
        print(f'\n\n{id}\n', cluster)

    for cluster, vm_list in vm_json.items():
        print(f'\n\n{cluster} virtual machines:\n', vm_list)

    try:
        vm_exceptions
        print('\nVM exceptions:\n')
        table = generate_table(vm_exceptions)
        print(table.get_string(fields=['vmName', 'exceptionReason', 'unsupportedResourceTypes', 'preferredHostType', 'chosenHostType']))
    except:
        print("There are no VM exceptions.")

    try:
        limited_compat
        print('\nHost incompatibilities:\n')
        table = generate_table(limited_compat)
        print(table.get_string(fields=['vmName', 'exceptionReason', 'unsupportedResourceTypes', 'preferredHostType', 'chosenHostType']))
    except:
        print("There are no host incompatibilities.")

    # print calculation logs if user desires
    if logs is True:
        print(calcs)
    
    print("\nAll output files are saved in the '/output' directory.")

