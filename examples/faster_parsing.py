# %load_ext autoreload
# %autoreload 2
import sem
import os
import re
import numpy as np
import matplotlib
# matplotlib.use('Agg')
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

###################
# Run simulations #
###################

# These are the available parameters
# We specify each parameter as an array containing the desired values
params = {
    'nWifi': [3],
    'distance': [10],
    'useRts': ['true'],
    'useShortGuardInterval': ['false', 'true'],
    'mcs': list(range(0, 8)),
    'channelWidth': ['20'],
    'simulationTime': [4],
}


# Function we would use with extract_complete_results=True
def get_average_throughput(result):
    stdout = result['output']['stdout']
    m = re.match('.*throughput: [-+]?([0-9]*\.?[0-9]+).*', stdout,
                    re.DOTALL).group(1)
    return float(m)

# If this function is used together with extract_complete_results=False, we can
# avoid reading all output files if we don't need them to extract our results.
# Instead, the passed result will contain the file name - file path
# correspondence at the ['output'] key
def get_average_throughput(result):
    # We access result['output']['stdout'] to get the path of the stdout for
    # this current result
    with open(result['output']['stdout'], 'r') as file_contents:
        stdout = file_contents.read()
    m = re.match('.*throughput: [-+]?([0-9]*\.?[0-9]+).*', stdout,
                    re.DOTALL).group(1)
    return float(m)

results = campaign.get_results_as_xarray(params, get_average_throughput,
                                         'throughput', extract_complete_results=False).squeeze()
