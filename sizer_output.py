#!/usr/bin/env python3
import json
import pandas as pd
from pandas import json_normalize
import time

def recommendation_transformer(json_data):
    # create dict for SDDC overview
    overview_df = pd.json_normalize(json_data['sddcList'][0]['clusterList']['sazClusters']['hostBreakupList'][0])
    overview_df = overview_df.transpose()

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

    return output_array

def csv_output(**kwargs):
    print()
    print("enabled in a future release.")


def excel_output(**kwargs):
    print()
    print("enabled in a future release.")


def pdf_output(pdf_content):
    timestr = time.strftime("%Y%m%d-%H%M%S")
    with open(f'output/VMC_Sizer_report_{timestr}.pdf', 'wb') as f:
        f.write(pdf_content)


def powerpoint_output(**kwargs):
    print()
    print("enabled in a future release.")


def terminal_output(**kwargs):
    calcs = kwargs['calcs']
    logs = kwargs['cl']
    overview = kwargs['recommendation']['overview']
    cluster_json =  kwargs['recommendation']['cluster_json']
    vm_json =  kwargs['recommendation']['vm_json']

    print()
    print(overview)
    # for i, j in overview.items():
    #     print(f'{i}                    {j}')

    for id, cluster in cluster_json.items():
        print(f'\n\n{id}\n', cluster)

    for cluster, vm_list in vm_json.items():
        print(f'\n\n{cluster} virtual machines:\n', vm_list)

    # print calculation logs if user
    if logs is True:
        print(calcs)
