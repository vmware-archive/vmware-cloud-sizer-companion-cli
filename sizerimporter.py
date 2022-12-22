#!/usr/bin/env python3

#VMC Sizer Importer for Python

import pandas as pd
import argparse
import requests
import sys
import json

def main(args):
    ap = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, epilog="Welcome to the VMC Sizer Import for Python")
    ap.add_argument("-f", "--file_name", required=True, help="The file name to be imported")
    ap.add_argument("-d", "--data_collection", required=True, choices=['rvtools', 'liveoptics'], help="Which tool completed the data collection, RVTools or Live Optics?")
    ap.add_argument("-rt", "--refresh_token", required=False, help="The CSP API refresh token")

    args = ap.parse_args(args)

    fn = args.file_name
    dt = args.data_collection
    rt = args.refresh_token

    access_token = get_access_token(rt)
    vm_json = []

    if dt == 'liveoptics':
        vms_json = live_optics_file_parser(fn)
    elif dt == 'rvtools':
        vms_json = rvtools_file_parser(fn)
    else:
        sys.exit("No filename provided")

def get_access_token(rt):
    """ Gets the Access Token using the Refresh Token """
    params = {'api_token': rt}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post('https://console.cloud.vmware.com/csp/gateway/am/api/auth/api-tokens/authorize',
                             params=params, headers=headers)
    if response.status_code != 200:
        print(f'Error received on api token: {response.status_code}.')
        if response.status_code == 400:
            print("Invalid request body | In case of expired refresh_token or bad token in config.ini")
        elif response.status_code == 404:
            print("The requested resource could not be found")
        elif response.status_code == 409:
            print("The request could not be processed due to a conflict")
        elif response.status_code == 429:
            print("The user has sent too many requests")
        elif response.status_code == 500:
            print("An unexpected error has occurred while processing the request")
        else:
            print(f"Unexpected error code {response.status_code}")
        return None

    json_response = response.json()
    access_token = json_response['access_token']
    return access_token


def live_optics_file_parser(filename):
    """Parse an ingested Live Optics file to JSON"""
    excel_vmdata_df = pd.read_excel(filename, sheet_name="VMs")
    excel_vmdata_df = excel_vmdata_df.drop(columns=['VM OS', 'Disks', 'NICs', 'Used Memory (active) (MB)',
                                                    'Consumed Memory (MB)', 'Provisioned Memory (Bytes)',
                                                    'Used Memory (active) (Bytes)', 'Consumed Memory (Bytes)',
                                                    'Guest VM % Occupancy', 'VMware Tools Version', 'Connection State',
                                                    'Template', 'Unshared (MB)', 'vCenter', 'UUID', 'InstanceUUID',
                                                    'Datastore', 'Host', 'Guest IP1', 'Guest IP2', 'Guest IP3',
                                                    'Guest IP4', 'Boot Time', 'Date Provisioned', ' Image Backup'])

    excel_perfdata_df = pd.read_excel(filename, sheet_name="VM Performance")
    excel_perfdata_df = excel_perfdata_df.drop(columns=['Host', 'Datacenter', 'Cluster', 'VM IO Classification'])

    vmerge = excel_vmdata_df.merge(excel_perfdata_df, left_on='MOB ID', right_on='MOB ID', suffixes=('_left', '_right'))

    print(vmerge)
    # pretty_data = json.dumps(excel_data_json, indent=4)
    # print(pretty_data)

def rvtools_file_parser(filename):
    """Parse an ingested RVTools file to JSON"""


