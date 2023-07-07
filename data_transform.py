#!/usr/bin/env python3

# VMware Cloud Sizer Companion CLI - data transformation module
################################################################################
### Copyright 2023 VMware, Inc.
### SPDX-License-Identifier: MIT License
################################################################################

import json
import pandas as pd
from pandas import json_normalize
import sys


def data_describe(output_path,csv_file):
    vm_data_df = pd.read_csv(f'{output_path}{csv_file}')

    # Ensure guest OS column is cast as string to better handle blank values
    vm_data_df['os'] = vm_data_df['os'].astype(str)

    print(f'\n{vm_data_df}')
    print(f'\nTotal VM: {vm_data_df.vmName.count()}')
    print("\nVM Power States:")
    print(vm_data_df['vmState'].value_counts())
    print(f'\nTotal unique operating systems: {vm_data_df.os.nunique()}')
    print('\nGuest operating systems:')
    print(vm_data_df.groupby('os')['vmId'].nunique())
    print(f'\nTotal Clusters: {vm_data_df.cluster.nunique()}')
    print(f'Cluster names: {vm_data_df.cluster.unique()}')
    print(f'\nTotal vCPU: {vm_data_df.vCpu.sum()}')
    print(f'\nTotal vRAM (GiB): {vm_data_df.vRam.sum()}')
    print(f'\nTotal used VMDK (GiB): {vm_data_df.vmdkUsed.sum()}')
    print(f'\nTotal provisioned VMDK (GiB): {vm_data_df.vmdkTotal.sum()}')
    print(f'\n{vm_data_df.describe()}')


def lova_conversion(**kwargs):
    input_path = kwargs['input_path']
    file_name = kwargs['file_name'] 
    output_path = kwargs['output_path']

    print()
    print("Parsing LiveOptics file(s) locally.")

    df_list = []
    for file in file_name:
        file_df = pd.read_excel(f'{input_path}{file}', sheet_name="VMs")
        df_list.append(file_df)
    vmdata_df = pd.concat(df_list, axis=0, ignore_index=True)

    # specify columns to KEEP - all others will be dropped
    keep_columns = ['Cluster','Datacenter','Guest IP1','Guest IP2','Guest IP3','Guest IP4','VM OS','Guest Hostname', 'Power State', 'Virtual CPU', 'VM Name', 'MOB ID']
    if 'Virtual Disk Size (MiB)' in vmdata_df:
        keep_columns.extend(['Virtual Disk Size (MiB)','Virtual Disk Used (MiB)', 'Provisioned Memory (MiB)'])
    else:
        keep_columns.extend(['Virtual Disk Size (MB)','Virtual Disk Used (MB)', 'Provisioned Memory (MB)'])

    vmdata_df = vmdata_df.filter(items= keep_columns, axis= 1)

    # rename remaining columns
    vmdata_df.rename(columns = {
        'MOB ID':'vmId',
        'VM Name':'vmName',
        'VM OS':'os',
        'Guest Hostname':'os_name',
        'Power State':'vmState',
        'Virtual CPU':'vCpu',
        'Cluster':'cluster',
        'Datacenter':'virtualDatacenter'
        }, inplace = True)

    if 'Virtual Disk Size (MiB)' in vmdata_df:
        vmdata_df.rename(columns = {
            'Provisioned Memory (MiB)':'vRam',
            'Virtual Disk Size (MiB)':'vmdkTotal',
            'Virtual Disk Used (MiB)':'vmdkUsed',
            }, inplace = True)
    else:
        vmdata_df.rename(columns = {
            'Provisioned Memory (MB)':'vRam',
            'Virtual Disk Size (MB)':'vmdkTotal',
            'Virtual Disk Used (MB)':'vmdkUsed',
            }, inplace = True)

    fillna_values = {"Guest IP1": "no ip", "Guest IP2": "no ip", "Guest IP3": "no ip", "Guest IP4": "no ip", "os": "none specified"}
    vmdata_df.fillna(value=fillna_values, inplace = True)

    # aggregate IP addresses into one column
    vmdata_df['ip_addresses'] = vmdata_df['Guest IP1'].map(str)+ ', ' + vmdata_df['Guest IP2'].map(str)+ ', ' + vmdata_df['Guest IP3'].map(str)+ ', ' + vmdata_df['Guest IP4'].map(str)
    vmdata_df['ip_addresses'] = vmdata_df.ip_addresses.str.replace(', no ip' , '')
    vmdata_df.drop(['Guest IP1', 'Guest IP2', 'Guest IP3', 'Guest IP4'], axis=1, inplace=True)

    # convert RAM and storage numbers into GB
    vmdata_df['vmdkUsed'] = vmdata_df['vmdkUsed']/1024
    vmdata_df['vmdkTotal'] = vmdata_df['vmdkTotal']/1024
    vmdata_df['vRam'] = vmdata_df['vRam']/1024

    vm_df_export = vmdata_df.round({'vmdkUsed':0,'vmdkTotal':0,'vRam':0})

    # pull in rows from VM Performance for storage performance metrics
    diskperf_list = []
    for file in file_name:
        disk_df = pd.read_excel(f'{input_path}{file}', sheet_name = 'VM Performance')
        diskperf_list.append(disk_df)
    diskperf_df = pd.concat(diskperf_list, axis=0, ignore_index=True)

    perf_columns = ["MOB ID","Avg Read IOPS","Avg Write IOPS","Peak Read IOPS","Peak Write IOPS","Avg Read MB/s","Avg Write MB/s","Peak Read MB/s","Peak Write MB/s"]
    diskperf_df = diskperf_df.filter(items= perf_columns, axis= 1)
    diskperf_df.rename(columns = {
        'MOB ID':'vmId', 
        'Avg Read IOPS':'readIOPS',
        'Avg Write IOPS':'writeIOPS',
        'Peak Read IOPS':'peakReadIOPS',
        'Peak Write IOPS':'peakWriteIOPS',
        'Avg Read MB/s':'readThroughput',
        'Avg Write MB/s':'writeThroughput',
        'Peak Read MB/s':'peakReadThroughput',
        'Peak Write MB/s':'peakWriteThroughput'
        }, inplace = True)

    vm_consolidated = pd.merge(vmdata_df, diskperf_df, on = "vmId", how = "left")

    vm_consolidated.to_csv(f'{output_path}1_vmdata_df_lova.csv')

    csv_file = "1_vmdata_df_lova.csv"
    return csv_file


def rvtools_conversion(**kwargs):
    input_path = kwargs['input_path']
    file_name = kwargs['file_name'] 
    output_path = kwargs['output_path']

    print()
    print("Parsing RVTools file(s) locally.")

    df_list = []
    for file in file_name:
        print(f'Reading {input_path}{file}')
        file_df = pd.read_excel(f'{input_path}{file}', sheet_name = 'vInfo')
        df_list.append(file_df)
    vmdata_df = pd.concat(df_list, axis=0, ignore_index=True)

    # specify columns to KEEP - all others will be dropped
    keep_columns = ['VM ID','Cluster', 'Datacenter','Primary IP Address','OS according to the VMware Tools', 'DNS Name','Powerstate','CPUs','VM','Memory']
    vmdata_df = vmdata_df.filter(items= keep_columns, axis= 1)

    # rename remaining columns
    vmdata_df.rename(columns = {
        'VM ID':'vmId', 
        'VM':'vmName',
        'OS according to the VMware Tools':'os',
        'DNS Name':'os_name',
        'Powerstate':'vmState',
        'CPUs':'vCpu',
        'Memory':'vRam', 
        'Primary IP Address':'ip_addresses',
        'Folder':'vmFolder',
        'Resource pool':'resourcePool',
        'Cluster':'cluster', 
        'Datacenter':'virtualDatacenter'
        }, inplace = True)
        
    fillna_values = {"ip_addresses": "no ip", "os": "none specified"}
    vmdata_df.fillna(value=fillna_values, inplace = True)

    # pull in rows from vDisk for allocated storage
    diskdf_list = []
    for file in file_name:
        disk_df = pd.read_excel(f'{input_path}{file}', sheet_name = 'vDisk')
        diskdf_list.append(disk_df)
    vdisk_df = pd.concat(diskdf_list, axis=0, ignore_index=True)
    
    vdisk_columns = ['VM ID']
    # Different versions of RVTools use either "MB" or "MiB" for storage; check for presence and include appropriate columns
    if 'Capacity MiB' in vdisk_df:
        vdisk_columns.extend(['Capacity MiB'])
    else:
        vdisk_columns.extend(['Capacity MB'])
    vdisk_df = vdisk_df.filter(items= vdisk_columns, axis= 1)

    if 'Capacity MiB' in vdisk_df:
        vdisk_df.rename(columns ={'Capacity MiB':'vmdkTotal'}, inplace = True)
    else:
        vdisk_df.rename(columns ={'Capacity MB':'vmdkTotal'}, inplace = True)
    vdisk_df.rename(columns ={'VM ID':'vmId'}, inplace = True)
    vdisk_df = vdisk_df.groupby(['vmId'])['vmdkTotal'].sum().reset_index()

    # pull in rows from vPartition for consumed storage
    partdf_list = []
    for file in file_name:
        part_df = pd.read_excel(f'{input_path}{file}', sheet_name = 'vPartition')
        partdf_list.append(part_df)
    vpart_df = pd.concat(partdf_list, axis=0, ignore_index=True)
    
    part_list = ['VM ID']
    if 'Consumed MiB' in vpart_df:
        part_list.extend(['Consumed MiB'])
    else:
        part_list.extend(['Consumed MB'])
    vpart_df = vpart_df.filter(items= part_list, axis= 1)

    if 'Consumed MiB' in vpart_df:
        vpart_df.rename(columns ={'Consumed MiB':'vmdkUsed'}, inplace = True)
    else:
        vpart_df.rename(columns ={'Consumed MB':'vmdkUsed'}, inplace = True)
    vpart_df.rename(columns ={'VM ID':'vmId'}, inplace = True)
    vpart_df = vpart_df.groupby(['vmId'])['vmdkUsed'].sum().reset_index()

    vm_consolidated = pd.merge(vmdata_df, vdisk_df, on = "vmId", how = "left")
    vm_consolidated = pd.merge(vm_consolidated, vpart_df, on = "vmId", how = "left")

    # convert RAM and storage numbers into GB
    vm_consolidated['vmdkUsed'] = vm_consolidated['vmdkUsed']/1024
    vm_consolidated['vmdkTotal'] = vm_consolidated['vmdkTotal']/1024
    vm_consolidated['vRam'] = vm_consolidated['vRam']/1024

    # Replace NA values for used VMDK and total VMDK with 10GB
    storage_na_values = {"vmdkTotal": 10, "vmdkUsed": 10}
    vm_consolidated.fillna(value=storage_na_values, inplace = True)

    # Replace 0 values for used VMDK and total VMDK with 10GB
    vm_consolidated['vmdkUsed'] = vm_consolidated['vmdkUsed'].replace(0, 10)
    vm_consolidated['vmdkTotal'] = vm_consolidated['vmdkTotal'].replace(0, 10)

    vm_consolidated.to_csv(f'{output_path}1_vmdata_df_rvtools.csv')
    csv_file = "1_vmdata_df_rvtools.csv"
    return csv_file


def ps_filter(**kwargs):
    output_path = kwargs['output_path']
    csv_file = kwargs['csv_file']
    power_state = kwargs['power_state']

    print()
    print("Filtering workloads based on power state.")
    vm_data_df = pd.read_csv(f'{output_path}{csv_file}',index_col=0)
    if power_state == "p":
        vm_data_df_trimmed = vm_data_df[vm_data_df.vmState == "poweredOn"]
    elif power_state == "ps":
        vm_data_df_trimmed = vm_data_df[vm_data_df.vmState != "poweredOff"]
    else:
        pass

    vm_data_df_trimmed.to_csv(f'{output_path}2_vmdata_df_power_state.csv')
    csv_file = "2_vmdata_df_power_state.csv"
    return csv_file


def include_workloads(**kwargs):
    output_path = kwargs['output_path']
    csv_file = kwargs['csv_file']
    infil = kwargs['include_filter']
    infilf = kwargs['include_filter_field']

    print()
    print(f'Including only those workloads where {infilf} includes {infil}')
    vm_data_df = pd.read_csv(f'{output_path}{csv_file}',index_col=0)

    pattern = '|'.join(infil)
    vm_data_df_trimmed = vm_data_df[vm_data_df[infilf].str.contains(pattern, case=False) == True]
    vm_data_df_trimmed.to_csv(f'{output_path}3_vmdata_df_infil.csv')
    csv_file = "3_vmdata_df_infil.csv"
    return csv_file


def exclude_workloads(**kwargs):
    output_path = kwargs['output_path']
    csv_file = kwargs['csv_file']
    exfil = kwargs['exclude_filter']
    exfilf = kwargs['exclude_filter_field']

    print()
    print(f'Excluding those workloads where {exfilf} includes {exfil}')
    vm_data_df = pd.read_csv(f'{output_path}{csv_file}',index_col=0)

    pattern = '|'.join(exfil)
    vm_data_df_trimmed = vm_data_df[vm_data_df[exfilf].str.contains(pattern, case=False) == False]
    vm_data_df_trimmed.to_csv(f'{output_path}4_vmdata_df_exfil.csv')
    csv_file = "4_vmdata_df_exfil.csv"
    return csv_file


def build_workload_profiles(**kwargs):
    output_path = kwargs['output_path']
    csv_file = kwargs['csv_file']
    profile_config = kwargs['workload_profiles']
    if kwargs['profile_list'] is not None:
        profile_list = kwargs['profile_list']

    print()
    print(f'Separating workloads into profiles based on {profile_config}')
    #create list for storing file names
    wp_file_list = []

    vm_data_df = pd.read_csv(f'{output_path}{csv_file}',index_col=0)

    match profile_config:
        case "all_clusters":
            print("Creating workload profiles by cluster.")
            workload_profiles = vm_data_df.groupby('cluster')
            # save resulting dataframes as csv files 
            for profile, profile_df in workload_profiles:
                profile_df.to_csv(f'{output_path}5_cluster_{profile}.csv')
                wp_file_list.append(f'5_cluster_{profile}.csv')
            return wp_file_list
    
        case "some_clusters":
            print("Creating custom cluster workload profiles.")
            workload_profiles = vm_data_df.groupby('cluster')

            # for list of clusters to keep, export to csv
            for profile, profile_df in workload_profiles:
                if profile in profile_list:
                    profile_df.to_csv(f'{output_path}5_cluster_{profile}.csv')
                    wp_file_list.append(f'5_cluster_{profile}.csv')

            # if desired in original DF, drop rows for exported clusters
            if kwargs['include_remaining'] == True:
                vm_data_df_trimmed = vm_data_df[vm_data_df.cluster.isin(profile_list) == False]
                vm_data_df_trimmed.to_csv(f'{output_path}5_cluster_remainder.csv')
                wp_file_list.append('5_cluster_remainder.csv')
            return wp_file_list

        case "os":
            print("Creating workload profiles based on GUEST OPERATING SYSTEM using text match.")
            for match_string in profile_list:
                profile_df = vm_data_df[vm_data_df['os'].str.contains(match_string)]
                profile_df.to_csv(f'{output_path}5_guest_os_{match_string}.csv')
                wp_file_list.append(f'5_guest_os_{match_string}.csv')
                
            # to keep remaining workloads, export all VM NOT matching to remainder CSV
            if kwargs['include_remaining'] == True:
                pattern = '|'.join(profile_list)
                vm_data_df_trimmed = vm_data_df[~vm_data_df['os'].str.contains(pattern, case=False)]
                vm_data_df_trimmed.to_csv(f'{output_path}5_os_remainder.csv')
                wp_file_list.append('5_os_remainder.csv')

            return wp_file_list

        case "vmName":
            print("Creating workload profiles based on VM NAME using text match.")

            for match_string in profile_list:
                profile_df = vm_data_df[vm_data_df['vmName'].str.contains(match_string)]
                profile_df.to_csv(f'{output_path}5_vmName_{match_string}.csv')
                wp_file_list.append(f'5_vmName_{match_string}.csv')

            # to keep remaining workloads, export all VM NOT matching to remainder CSV
            if kwargs['include_remaining'] == True:
                pattern = '|'.join(profile_list)
                vm_data_df_trimmed = vm_data_df[~vm_data_df['vmName'].str.contains(pattern, case=False)]
                vm_data_df_trimmed.to_csv(f'{output_path}5_vmName_remainder.csv')
                wp_file_list.append('5_vmName_remainder.csv')
            return wp_file_list


def build_recommendation_payload(**kwargs):
    output_path = kwargs['output_path']
    wp_file_list = kwargs['wp_file_list']
    cloudType = kwargs['cloud_type']
    storage_capacity = kwargs['storage_capacity']
    storage_type = kwargs['storage_type']
    storage_vendor = kwargs['storage_vendor']
    profile_type = kwargs['profile_type']
    pct_cpu = kwargs['pct_cpu']
    pct_mem = kwargs['pct_mem']
    fttFtmType = kwargs['fttFtmType']

    print()
    print('Building sizing request payload')
    # set configurations for recommendation calculations
    configurations = {
        "cloudType": cloudType,
        "computeOvercommitFactor": 4,
        "cpuHeadroom": 0.15,
        "hyperThreadingFactor": 1.25,
        "memoryOvercommitFactor": 1.25,
        "cpuUtilization": pct_cpu,
        "memoryUtilization": pct_mem,
        "storageThresholdFactor": 0.8,
        "compressionRatio": 1.25,
        "dedupRatio": 1.5,
        "ioAccessPattern": None,
        "ioSize": None,
        "ioRatio": None,
        "totalIOPs": None,
        "includeManagementVMs": True,
        "fttFtmType": fttFtmType,
        "separateClusters": True,
        "instanceSettingsList": None,
        "vmOutlierLimits": {
            "cpuLimit": 0.75,
            "storageLimit": 0.5,
            "memoryLimit": 0.75
        },
        "applianceSize": "AUTO",
        "addonsList": []
    }

    # set host type based on cloud type
    match cloudType:
        case "GCVE":
            pass
        case "VMC_ON_AWS":
            hostType = kwargs['host_type']
            clusterType = kwargs['cluster_type']            
            configurations["sddcHostType"] = hostType
            configurations["clusterType"] = clusterType
    
    # build json objects for recommendation payload
    workloadProfiles = []

    # build the sizerRequest payload, using exported files (from above) to populate the workload profiles
    for file in wp_file_list:
        vm_data_df = pd.read_csv(f'{output_path}{file}')

        # build the profiles
        profile = {}
        profile["profileName"] = file
        profile['separateCluster'] = True
        profile["isEnabled"] = True
        profile["workloadProfileType"] = profile_type
        profile["storagePreference"] = storage_type
        print(f'Using preferred storage type of: {profile["storagePreference"]}')
        profile["extStorageVendorType"] = storage_vendor

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
            if 'readIOPS' in vm_data_df:
                VMInfo["vmStorageInfo"]["readIOPS"] = int(vm_data_df['readIOPS'][ind])
                VMInfo["vmStorageInfo"]["writeIOPS"] = int(vm_data_df['writeIOPS'][ind])
                VMInfo["vmStorageInfo"]["peakReadIOPS"] = int(vm_data_df['peakReadIOPS'][ind])
                VMInfo["vmStorageInfo"]["peakWriteIOPS"] = int(vm_data_df['peakWriteIOPS'][ind])
                VMInfo["vmStorageInfo"]["readThroughput"] = int(vm_data_df['readThroughput'][ind])
                VMInfo["vmStorageInfo"]["writeThroughput"] = int(vm_data_df['writeThroughput'][ind])
                VMInfo["vmStorageInfo"]["peakReadThroughput"] = int(vm_data_df['peakReadThroughput'][ind])
                VMInfo["vmStorageInfo"]["peakWriteThroughput"] = int(vm_data_df['peakWriteThroughput'][ind])
            else:
                pass
            match storage_capacity:
                case "PROVISIONED":
                    VMInfo["vmStorageInfo"]["vmdkTotal"] = int(vm_data_df['vmdkTotal'][ind])
                    VMInfo["vmStorageInfo"]["vmdkUsed"] = int(vm_data_df['vmdkTotal'][ind])
                case "UTILIZED":
                    VMInfo["vmStorageInfo"]["vmdkTotal"] = int(vm_data_df['vmdkUsed'][ind])
                    VMInfo["vmStorageInfo"]["vmdkUsed"] = int(vm_data_df['vmdkUsed'][ind])
            vmList.append(VMInfo)

        profile['vmList'] = vmList
        workloadProfiles.append(profile)

    sizerRequest = {
        "configurations": configurations,
        "workloadProfiles": workloadProfiles
        }


    with open("output/custom_recommendation_request.txt", "w") as f:
        print(json.dumps(sizerRequest, indent=2), file=f)
 
    return json.dumps(sizerRequest)