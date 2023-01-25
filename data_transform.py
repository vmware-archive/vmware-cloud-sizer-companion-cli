#!/usr/bin/env python3
import json
import pandas as pd
from pandas import json_normalize
import sys


def data_describe(vm_data):
    vm_data_df = pd.DataFrame(vm_data)

    # Ensure guest OS column is cast as string to better handle blank values
    vm_data_df['os'] = vm_data_df['os'].astype(str)

    print(f'\n{vm_data_df}')
    print(f'\nTotal VM: {vm_data_df.vmName.count()}')
    print("\nVM Power States:")
    print(vm_data_df['vmState'].value_counts())
    print(f'\nTotal unique operating systems: {vm_data_df.os.nunique()}')
    print('\nGuest operating systems:')
    for i in sorted(vm_data_df.os.unique()):
        if i != 'nan':
            print(i)
    print(f'\nTotal Clusters: {vm_data_df.cluster.nunique()}')
    print(f'Cluster names: {vm_data_df.cluster.unique()}')
    print(f'\nTotal vCPU: {vm_data_df.vCpu.sum()}')
    print(f'\nTotal vRAM: {vm_data_df.vRam.sum()}')
    print(f'\nTotal used VMDK: {vm_data_df.vmdkUsed.sum()}')
    print(f'\nTotal provisioned VMDK: {vm_data_df.vmdkTotal.sum()}')
    print(f'\n{vm_data_df.describe()}')


def lova_conversion(**kwargs):
    input_path = kwargs['input_path']
    file_name = kwargs['file_name'] 

    vmdata_df = pd.read_excel(f'{input_path}{file_name}', sheet_name="VMs")

    # specify columns to KEEP - all others will be dropped
    vmdata_df.drop(vmdata_df.columns.difference([
        'Cluster','Datacenter','Guest IP1','Guest IP2','Guest IP3','Guest IP4','VM OS',
        'Guest Hostname', 'Power State', 'Virtual CPU', 'VM Name', 'Virtual Disk Size (MB)',
        'Virtual Disk Used (MB)', 'Provisioned Memory (MB)', 'Consumed Memory (MB)', 'MOB ID'
        ]), axis=1, inplace=True)

    # rename remaining columns
    vmdata_df.rename(columns = {
        'MOB ID':'vmId',
        'VM Name':'vmName',
        'VM OS':'os',
        'Guest Hostname':'os_name',
        'Power State':'vmState',
        'Virtual CPU':'vCpu',
        'Provisioned Memory (MB)':'vRam',
        'Virtual Disk Size (MB)':'vmdkTotal',
        'Virtual Disk Used (MB)':'vmdkUsed',
        'Cluster':'cluster',
        'Datacenter':'virtualDatacenter'
        }, inplace = True)

    # aggregate IP addresses into one column
    vmdata_df["Guest IP1"].fillna("no ip", inplace = True)
    vmdata_df["Guest IP2"].fillna("no ip", inplace = True)
    vmdata_df["Guest IP3"].fillna("no ip", inplace = True)
    vmdata_df["Guest IP4"].fillna("no ip", inplace = True)
    vmdata_df['ip_addresses'] = vmdata_df['Guest IP1'].map(str)+ ', ' + vmdata_df['Guest IP2'].map(str)+ ', ' + vmdata_df['Guest IP3'].map(str)+ ', ' + vmdata_df['Guest IP4'].map(str)
    vmdata_df['ip_addresses'] = vmdata_df.ip_addresses.str.replace(', no ip' , '')
    vmdata_df.drop(['Guest IP1', 'Guest IP2', 'Guest IP3', 'Guest IP4'], axis=1, inplace=True)

    # convert RAM and storage numbers into GB
    vmdata_df['vmdkUsed'] = vmdata_df['vmdkUsed']/1024
    vmdata_df['vmdkTotal'] = vmdata_df['vmdkTotal']/1024
    vmdata_df['vRam'] = vmdata_df['vRam']/1024

    return vmdata_df


def rvtools_conversion(**kwargs):
    input_path = kwargs['input_path']
    file_name = kwargs['file_name'] 

    vmdata_df = pd.read_excel(f'{input_path}{file_name}', sheet_name = 'vInfo')

    # specify columns to KEEP - all others will be dropped
    vmdata_df.drop(vmdata_df.columns.difference([
        'VM ID','Cluster', 'Datacenter','Primary IP Address','OS according to the VMware Tools',
        'DNS Name','Powerstate','CPUs','VM','Provisioned MB','In Use MB','Memory', 'Resource pool', 'Folder'
        ]), axis = 1, inplace = True)

    # rename remaining columns
    vmdata_df.rename(columns = {
        'VM ID':'vmId',
        'VM':'vmName',
        'OS according to the VMware Tools':'os',
        'DNS Name':'os_name',
        'Powerstate':'vmState',
        'CPUs':'vCpu',
        'Memory':'vRam', 
        'Provisioned MB':'vmdkTotal',
        'In Use MB':'vmdkUsed',
        'Primary IP Address':'ip_addresses',
        'Folder':'vmFolder',
        'Resource pool':'resourcePool',
        'Cluster':'cluster', 
        'Datacenter':'virtualDatacenter'
        }, inplace = True)

    # convert RAM and storage numbers into GB
    vmdata_df['vmdkUsed'] = vmdata_df['vmdkUsed']/1024
    vmdata_df['vmdkTotal'] = vmdata_df['vmdkTotal']/1024
    vmdata_df['vRam'] = vmdata_df['vRam']/1024

    return vmdata_df


def workload_profiles(**kwargs):
    vm_data_df = kwargs["vm_data"]
    ct = kwargs["ct"]
    power_state = kwargs['power_state']
    # scope = kwargs["scope"]
    # cap = kwargs["cap"]
    # susvm = kwargs["susvm"]
    profile_config = kwargs["profile_config"]

    if power_state == "p":
        vm_data_df = vm_data_df[vm_data_df.vmState == "poweredOn"]
    elif power_state == "ps":
        vm_data_df = vm_data_df[vm_data_df.vmState != "poweredOff"]
    else:
        pass

    if kwargs['keep_list'] is None and profile_config != "clusters":
        print('When creating workload profiles using custom clusters, guest_os. folers, etc, you must use --keep_list to specify at least one text string to search by.')
        sys.exit(1)
    else:
        keep_list = kwargs['keep_list']

    #create list for storing file names
    file_list = []
    output_path = './output'

    match profile_config:
        case "clusters":
            print("Creating workload profiles by cluster.")
            workload_profiles = vm_data_df.groupby('cluster')
            # save resulting dataframes as csv files 
            for profile, profile_df in workload_profiles:
                profile_df.to_csv(f'{output_path}/cluster_{profile}.csv')
                file_list.append(f'cluster_{profile}.csv')
    
        case "custom_clusters":
            print("Creating custom cluster workload profiles.")
            workload_profiles = vm_data_df.groupby('cluster')

            # for list of clusters to keep, export to csv
            for profile, profile_df in workload_profiles:
                if profile in keep_list:
                    profile_df.to_csv(f'{output_path}/cluster_{profile}.csv')
                    file_list.append(f'cluster_{profile}.csv')

            # if desired in original DF, drop rows for exported clusters
            if kwargs['include_remaining'] == True:
                vm_data_df_trimmed = vm_data_df[vm_data_df.cluster.isin(keep_list) == False]
                vm_data_df_trimmed.to_csv(f'{output_path}/cluster_remainder.csv')
                file_list.append('cluster_remainder.csv')

        case "guest_os":
            print("Creating workload profiles based on GUEST OPERATING SYSTEM using text match.")

            for match_string in keep_list:
                profile_df = vm_data_df[vm_data_df['os'].str.contains(match_string)]
                profile_df.to_csv(f'{output_path}/guest_os_{match_string}.csv')
                file_list.append(f'guest_os_{match_string}.csv')

            # to keep remaining workloads, export all VM NOT matching to remainder CSV
            if kwargs['include_remaining'] == True:
                pattern = '|'.join(keep_list)
                vm_data_df_trimmed = vm_data_df[~vm_data_df['os'].str.contains(pattern, case=False)]
                vm_data_df_trimmed.to_csv(f'{output_path}/os_remainder.csv')
                file_list.append('os_remainder.csv')

        case "vm_name":
            print("Creating workload profiles based on VM NAME using text match.")

            for match_string in keep_list:
                profile_df = vm_data_df[vm_data_df['vmName'].str.contains(match_string)]
                profile_df.to_csv(f'{output_path}/vmName_{match_string}.csv')
                file_list.append(f'vmName_{match_string}.csv')

            # to keep remaining workloads, export all VM NOT matching to remainder CSV
            if kwargs['include_remaining'] == True:
                pattern = '|'.join(keep_list)
                vm_data_df_trimmed = vm_data_df[~vm_data_df['vmName'].str.contains(pattern, case=False)]
                vm_data_df_trimmed.to_csv(f'{output_path}/vmName_remainder.csv')
                file_list.append('vmName_remainder.csv')

    # set configurations for recommendation calculations
    configurations = {
        "cloudType": ct,
        # "sddcHostType": "COST_OPT",
        "clusterType": "SAZ",
        "computeOvercommitFactor": 4,
        "cpuHeadroom": 0.15,
        "hyperThreadingFactor": 1.25,
        "memoryOvercommitFactor": 1.25,
        "cpuUtilization": 1,
        "memoryUtilization": 1,
        "storageThresholdFactor": 0.8,
        "compressionRatio": 1.25,
        "dedupRatio": 1.5,
        "ioAccessPattern": None,
        "ioSize": None,
        "ioRatio": None,
        "totalIOPs": None,
        "includeManagementVMs": True,
        "fttFtmType": "AUTO_AUTO",
        "separateCluster": None,
        "instanceSettingsList": None,
        "vmOutlierLimits": {
            "cpuLimit": 0.75,
            "storageLimit": 0.5,
            "memoryLimit": 0.75
        },
        "applianceSize": "AUTO",
        "addonsList": []
    }
    
    # build json objects for recommendation payload
    workloadProfiles = []

    # build the sizerRequest payload, using exported files (from above) to populate the workload profiles
    for file in file_list:
        vm_data_df = pd.read_csv(f'./output/{file}')

        # build the profile
        profile = {}
        profile["profileName"] = file
        profile['separateCluster'] = True
        profile["isEnabled"] = True

        vmList = []

        for ind in vm_data_df.index:
            VMInfo = {}
            VMInfo["vmComputeInfo"] = {}
            VMInfo["vmMemoryInfo"] = {}
            VMInfo["vmStorageInfo"] = {}   
            VMInfo["vmId"] = str(vm_data_df['vmId'][ind])
            VMInfo["vmName"] = str(vm_data_df['vmName'][ind])
            VMInfo["vmComputeInfo"]["vCpu"] = int(vm_data_df['vCpu'][ind])
            VMInfo["vmMemoryInfo"]["vRam"] = int(vm_data_df['vRam'][ind])
            VMInfo["vmStorageInfo"]["vmdkTotal"] = int(vm_data_df['vmdkTotal'][ind])
            VMInfo["vmStorageInfo"]["vmdkUsed"] = int(vm_data_df['vmdkUsed'][ind])
            vmList.append(VMInfo)

        profile['vmList'] = vmList
        workloadProfiles.append(profile)

    sizerRequest = {
        "configurations": configurations,
        "workloadProfiles": workloadProfiles
        }

    return json.dumps(sizerRequest)


####################################
# code / functions for later use
####################################

# import parition or performance data 
    # excel_partition_df = pd.read_excel(file_name, sheet_name="VM Disks")
    # excel_partition_df = excel_partition_df.drop(columns=[
    #     'Datacenter', 'Host','InstanceUUID','IsRunning','vCenter'
    #     ])

    # print(excel_partition_df)

    # excel_perfdata_df = pd.read_excel(file_name, sheet_name="VM Performance")
    # excel_perfdata_df = excel_perfdata_df.drop(columns=[
    #     '% of KB/sec', '% of Memory', '% of vCPU', 'Average IOPS', 'Average KB/sec', 'Average vCPU (GHz)', 'Average vCPU %', 'Avg Memory (MB)',
    #     'Avg Memory %', 'Avg Read IOPS', 'Avg Read Latency', 'Avg Read MB/s', 'Avg Write IOPS', 'Avg Write Latency', 'Avg Write MB/s','Datacenter',
    #     'Host','Max KB/sec', 'Peak Latency', 'Peak Memory (MB)', 'Peak Memory %', 'VM IO Classification'
    #     ], axis=1, inplace=True)

    # print(excel_perfdata_df)

    # vmerge = excel_vmdata_df.merge(excel_perfdata_df, left_on='MOB ID', right_on='MOB ID', suffixes=('_left', '_right'))
    # vmerge = excel_vmdata_df.merge(excel_partition_df, left_on='MOB ID', right_on='MOB ID', suffixes=('_left', '_right'))
    # return vmerge