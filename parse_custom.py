#!/usr/bin/env python3
import json
import pandas as pd
from pandas import json_normalize


def workload_profiles(**kwargs):
    parsed__data = kwargs['parsed_data'] 
    profile_config = kwargs['profile_config']

    json_data = json.loads(parsed__data)
    # print(json.dumps(json_data, indent = 4))

    # recommendation_df = pd.json_normalize(json_data['workloadProfiles'], record_path=['vmList'])
    recommendation_df = pd.json_normalize(json_data['workloadProfiles'])
    # recommendation_df = pd.read_json(json_data)
    print(recommendation_df)
    for col in recommendation_df.columns:
        print(col)


# vmId
# vmGroupId
# vmName
# vmState
# workloadProfileIndex
# importedFileName
# vmComputeInfo.vCpu
# vmComputeInfo.vCpuOverall
# vmComputeInfo.vCpuPerCore
# vmComputeInfo.utilizationRatio
# vmMemoryInfo.vRam
# vmMemoryInfo.vRamConsumed
# vmMemoryInfo.ramOverhead
# vmMemoryInfo.utilizationRatio
# vmStorageInfo.vmdkTotal
# vmStorageInfo.vmdkUsed
# vmStorageInfo.readIOPS
# vmStorageInfo.writeIOPS

    # df = pd.json_normalize(
    #     data, 
    #     record_path =['students'], 
    #     meta=[
    #         'class',
    #         ['info', 'president'], 
    #         ['info', 'contacts', 'tel']
    #     ]
    # )

