#!/usr/bin/env python3
import pandas as pd

def lova_conversion(**kwargs):

    file_name = kwargs['file_name'] 
    scope = kwargs['scope']
    cap = kwargs['cap']

    excel_vmdata_df = pd.read_excel(file_name, sheet_name="VMs")

    # specify columns to KEEP - all others will be dropped
    # excel_vmdata_df.drop([
    #     "Boot Time","Connection State","Consumed Memory (Bytes)","Consumed Memory (MB)",
    #     "Datacenter","Datastore","Date Provisioned","Disks","Guest VM % Occupancy","Guest VM Disk Capacity (MB)","Guest VM Disk Used (MB)",
    #     "Host","InstanceUUID","IsRunning","NICs","Provisioned Memory (Bytes)","Template","Unshared (MB)","Used Memory (active) (Bytes)",
    #     "Used Memory (active) (MB)","UUID","vCenter","VMware Tools Version"," Image Backup"
    #     ], axis=1, inplace=True)

    excel_vmdata_df.drop(excel_vmdata_df.columns.difference([
        'Cluster','Guest IP1','Guest IP2','Guest IP3','Guest IP4','VM OS',
        'Guest Hostname', 'Power State', 'Virtual CPU', 'VM Name', 'Virtual Disk Size (MB)',
        'Virtual Disk Used (MB)', 'Provisioned Memory (MB)'
        ]), axis=1, inplace=True)

    # rename remaining columns
    excel_vmdata_df.rename(columns = {
        'Cluster':'cluster', 
        'VM OS':'os',
        'Guest Hostname':'os_name',
        'Power State':'power_state',
        'Virtual CPU':'vcpu',
        'VM Name':'vm_name',
        'Virtual Disk Size (MB)':'vmdk_size_gb',
        'Virtual Disk Used (MB)':'vmdk_used_gb',
        'Provisioned Memory (MB)':'vram_gb' 
        }, inplace = True)

    # aggregate IP addresses into one column
    excel_vmdata_df["Guest IP1"].fillna("no ip", inplace = True)
    excel_vmdata_df["Guest IP2"].fillna("no ip", inplace = True)
    excel_vmdata_df["Guest IP3"].fillna("no ip", inplace = True)
    excel_vmdata_df["Guest IP4"].fillna("no ip", inplace = True)
    excel_vmdata_df['ip_addresses'] = excel_vmdata_df['Guest IP1'].map(str)+ ', ' + excel_vmdata_df['Guest IP2'].map(str)+ ', ' + excel_vmdata_df['Guest IP3'].map(str)+ ', ' + excel_vmdata_df['Guest IP4'].map(str)
    excel_vmdata_df['ip_addresses'] = excel_vmdata_df.ip_addresses.str.replace(', no ip' , '')
    excel_vmdata_df.drop(['Guest IP1', 'Guest IP2', 'Guest IP3', 'Guest IP4'], axis=1, inplace=True)

    # convert RAM and storage numbers into GB
    excel_vmdata_df['vmdk_used_gb'] = excel_vmdata_df['vmdk_used_gb']/1024
    excel_vmdata_df['vmdk_size_gb'] = excel_vmdata_df['vmdk_size_gb']/1024
    excel_vmdata_df['vram_gb'] = excel_vmdata_df['vram_gb']/1024

    # separate workloads by cluster
    cluster_profiles = excel_vmdata_df.groupby('cluster')

    # save resulting dataframes as excel files 
    output_path = './output'
    for cluster, cluster_df in cluster_profiles:
        cluster_df.to_excel(f'{output_path}/cluster_{cluster}.xlsx')

    cluster_pivot = excel_vmdata_df.groupby('cluster').agg({'vcpu' : ['sum'],'vram_gb' : ['sum'], 'vmdk_size_gb' : ['sum']})
    return cluster_pivot

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