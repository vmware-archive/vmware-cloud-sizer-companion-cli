#!/usr/bin/env python3
import pandas as pd

def rvtools_conversion(**kwargs):

    file_name = kwargs['file_name'] 
    scope = kwargs['scope']
    cap = kwargs['cap']

    excel_vmdata_df = pd.read_excel(file_name, sheet_name = 'vInfo')

    # specify columns to KEEP - all others will be dropped
    # excel_vmdata_df.drop([“Accessibility”, “Annotation”, “Boot BIOS setup”, “Boot delay”, “Boot Required”, “Boot retry delay”, “Boot retry enabled”, “Business Tier”, “CBT”, “Change Version”, “Cluster rule name(s)”, “Cluster rule(s)”, “Config status”, “Connection state”, “Consolidation Needed”, “Cost Center”, “CreatedBy”, “CreatedOn”, “Creation date”, “DAS protection”, “Datacenter”, “Disks”, “EnableUUID”, “Environment Intent”, “Firmware”, “Folder”, “FT Bandwidth”, “FT Latency”, “FT Sec. Latency”, “FT State”, “Guest state”, “HA Isolation Response”, “HA Restart Priority”, “HA VM Monitoring”, “Heartbeat”, “Host”, “HW target”, “HW upgrade policy”, “HW upgrade status”, “HW version”, “Latency Sensitivity”, “Log directory”, “min Required EVC Mode Key “, “Network '#'1”, “Network '#'2”, “Network '#'3”, “Network '#'4”, “Network '#'5”, “Network #6”, “Network #7”, “Network #8”, “NICs”, “Num Monitors”, “Oracle Information”, “OS according to the configuration file”, “Patching Schedule”, “Path”, “PowerOn”, “Primary Backup”, “Resource pool”, “Snapshot directory”, “SRM Placeholder”, “Suspend directory”, “Suspend time”, “Template”, “Unshared MiB”, “vApp”, “Veeam.CustomTag1”, “Veeam.CustomTag2”, “VI SDK API Version”, “VI SDK Server”, “VI SDK Server type”, “VI SDK UUID”, “Video Ram KiB”, “VM ID”, “VM UUID”, “vSAN Backing”, “XdConfig”, “Zerto Replication Status”], axis=1, inplace=True)
    excel_vmdata_df.drop(excel_vmdata_df.columns.difference([
        'Cluster', 'Primary IP Address','OS according to the VMware Tools',
        'DNS Name','Powerstate','CPUs','VM','Provisioned MiB','In Use MiB','Memory'
        ]), axis = 1, inplace = True)

    # rename remaining columns
    excel_vmdata_df.rename(columns = {
        'Cluster':'cluster', 
        'OS according to the VMware Tools':'os',
        'DNS Name':'os_name',
        'Powerstate':'power_state',
        'CPUs':'vcpu',
        'VM':'vm_name',
        'Provisioned MiB':'vmdk_size_gb',
        'In Use MiB':'vmdk_used_gb',
        'Memory':'vram_gb', 
        'Primary IP Address':'ip_addresses' 
        }, inplace = True)

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