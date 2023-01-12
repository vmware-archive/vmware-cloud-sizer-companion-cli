#!/usr/bin/env python3
import json
import pandas as pd
from pandas import json_normalize


def workload_profiles(**kwargs):
    json_data = kwargs['parsed_data'] 
    profile_config = kwargs['profile_config']
    pd.json_normalize(json_data)
    recommendation_df = pd.read_json(json_data)
    print(recommendation_df)