#!/usr/bin/env python3

# VMware Cloud Sizer Companion CLI - Cloud Sizer API module
################################################################################
### Copyright 2023 VMware, Inc.
### SPDX-License-Identifier: MIT License
################################################################################

import requests
import sys
import json

def sizer_error_handling(fxn_response):
    """ Error handling for HTML / REST API requests """
    code = fxn_response.status_code
    print (f'API call failed with status code {code}.')
    if code == 301:
        print(f'Error {code}: "Moved Permanently"')
        print("Request must be reissued to a different controller node.")
        print("The controller node has been replaced by a new node that should be used for this and all future requests.")
    elif code ==307:
        print(f'Error {code}: "Temporary Redirect"')
        print("Request should be reissued to a different controller node.")
        print("The controller node is requesting the client make further requests against the controller node specified in the Location header. Clients should continue to use the new server until directed otherwise by the new controller node.")
    elif code ==400:
        print(f'Error {code}: "Bad Request"')
        print("Request was improperly formatted or contained an invalid parameter.")
    elif code ==401:
        print(f'Error {code}: "Unauthorized"')
        print("The client has not authenticated.")
        print("It's likely your refresh token is out of date or otherwise incorrect.")
    elif code ==403:
        print(f'Error {code}: "Forbidden"')
        print("The client does not have sufficient privileges to execute the request.")
        print("The API is likely in read-only mode, or a request was made to modify a read-only property.")
        print("It's likely your refresh token does not provide sufficient access.")
    elif code ==409:
        print(f'Error {code}: "Temporary Redirect"')
        print("The request can not be performed because it conflicts with configuration on a different entity, or because another client modified the same entity.")
        print("If the conflict arose because of a conflict with a different entity, modify the conflicting configuration. If the problem is due to a concurrent update, re-fetch the resource, apply the desired update, and reissue the request.")
    elif code ==412:
        print(f'Error {code}: "Precondition Failed"')
        print("The request can not be performed because a precondition check failed. Usually, this means that the client sent a PUT or PATCH request with an out-of-date _revision property, probably because some other client has modified the entity since it was retrieved. The client should re-fetch the entry, apply any desired changes, and re-submit the operation.")
    elif code ==500:
        print(f'Error {code}: "Internal Server Error"')
        print('''
        An internal error occurred while executing the request. If the problem persists, perform diagnostic system tests, or contact your support representative.
        This could be due to the use of a modified RVTools or LiveOptics file... 
        be sure to submit an ** unmodified ** file for parsing and recommendations.
        ''')
    elif code ==503:
        print(f'Error {code}: "Service Unavailable"')
        print("The request can not be performed because the associated resource could not be reached or is temporarily busy. Please confirm the ORG ID and SDDC ID entries in your config.ini are correct.")
    else:
        print(f'Error: {code}: Unknown error')
    try:
        json_response = fxn_response.json()
        if 'error_message' in json_response:
            print(json_response['error_message'])
        print("See https://www.iana.org/assignments/http-status-codes/http-status-codes.xhtml for more information on HTML error codes.")
        print(fxn_response)
    except:
        print("No additional information in the error response.")
    return None


def get_access_token_api(rt):
    """ Gets the Access Token using the Refresh Token """
    params = {'api_token': rt}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post('https://console.cloud.vmware.com/csp/gateway/am/api/auth/api-tokens/authorize',
                             params=params, headers=headers)
    if response.status_code == 200:
        json_response = response.json()
        access_token = json_response['access_token']
        # print(json.dumps(json_response, indent = 4))
        return access_token
    else:
        sizer_error_handling(response)


def parse_excel_api(**kwargs):
    # sessiontoken = kwargs['access_token']
    fn = kwargs['file_name'][0]
    input_path = kwargs['input_path']
    adapter = kwargs['file_type']
    uri = f'https://vmc.vmware.com/api/vmc-sizer/v5/sizing/adapter/{adapter}'

    files=[
        ('file',(fn,open(f'{input_path}{fn}','rb'),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
        ]

    print()
    print("Submitting Excel file for parsing.")

    response = requests.post(uri, files=files)
    if response.status_code == 200:
        return response.json()
    else:
        sizer_error_handling(response)


def get_pdf_api(**kwargs):
    # sessiontoken = kwargs['access_token']
    json_data = kwargs['json_data']

    print()
    print("Requesting PDF")
    if kwargs['vp'] is not None:
        vp = kwargs['vp']
    else:
        vp = True

    if vp is True:
        uri = 'https://vmc.vmware.com/api/vmc-sizer/v5/recommendation?vmPlacement=true'
    else:
        uri = 'https://vmc.vmware.com/api/vmc-sizer/v5/recommendation?vmPlacement=false'

    # my_header = {'Content-Type': 'application/json', 'csp-auth-token': sessiontoken}

    my_header = {'Content-Type': 'application/json', 'Accept':'application/pdf'}
    response = requests.post(uri, headers = my_header, data = json_data)
    if response.status_code == 200:
        return response.content
    else:
        sizer_error_handling(response)


def get_recommendation_api(**kwargs):
    # sessiontoken = kwargs['access_token']
    json_data = kwargs['json_data']
    vp = kwargs['vp']

    print()
    print("Requesting recommendation")

    uri = f'https://vmc.vmware.com/api/vmc-sizer/v5/recommendation?vmPlacement={vp}'
    my_header = {'Content-Type': 'application/json'}
    response = requests.post(uri, headers = my_header, data = json_data)
    if response.status_code == 200:
        return response.json()
    else:
        sizer_error_handling(response)
