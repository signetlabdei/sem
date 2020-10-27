# %load_ext autoreload
# %autoreload 2
import sem
import re
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import math

#######################
# Create the campaign #
#######################

script = 'wifi-multi-tos'
ns_path = 'ns-3'
campaign_dir = "/tmp/sem-test/wifi-plotting-example"

campaign = sem.CampaignManager.new(ns_path, script, campaign_dir,
                                   runner_type='ParallelRunner',
                                   overwrite=True)

print(campaign)  # This prints out the campaign settings

def get_average_throughput(result):
    stdout = result['output']['stdout']
    m = re.match(r'.*throughput: [-+]?([0-9]*\.?[0-9]+).*',
                 stdout, re.DOTALL).group(1)
    return float(m)

# Define ranges
param_ranges = {
    # 'nWifi': {'min': 1, 'max': 10},
    # 'distance': {'min': 1, 'max' :10},
    'nWifi': [1],
    'distance': [10],
    # 'useRts': [False, True],
    'useRts': [False],
    'useShortGuardInterval': [False],
    # 'mcs': list(range(0, 8)),
    'mcs': [5],
    'channelWidth': [20],
    'simulationTime': [4],
    'RngRun': list(range(10))
}
output = sem.utils.compute_sensitivity_analysis(campaign,
                                                get_average_throughput,
                                                param_ranges)
