# This is an example showing how to use the ns-3 SimulationExecutionManager to
# get from compilation to result visualization.

from sem import CampaignManager, list_param_combinations
import os
from pathlib import Path
import shutil
import re
import numpy as np
import matplotlib.pyplot as plt
import xarray as xr


# Define campaign parameters
############################

script = 'wifi-multi-tos'
# ns_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ns-3')
# ns_path = '/home/davide/Work/sem/examples/ns-3'
ns_path = '/Users/davide/Work/sem/examples/ns-3'
campaign_dir = "/tmp/sem-test/wifi-plotting-example"

# Create campaign
#################

if (Path(campaign_dir).exists()):
    shutil.rmtree(campaign_dir)
campaign = CampaignManager.new(ns_path, script, campaign_dir,
                               runner='ParallelRunner')

print(campaign)

# Run simulations
#################

# Parameter space
#################
nWifi_values = [1]
distance_values = [10]
simulationTime_values = [10]
useRts_values = ['false', 'true']
mcs_values = list(range(0,8))
channelWidth_values = ['20']
useShortGuardInterval_values = ['false', 'true']

param_combinations = {
    'nWifi': nWifi_values,
    'distance': distance_values,
    'simulationTime': simulationTime_values,
    'useRts': useRts_values,
    'mcs': mcs_values,
    'channelWidth': channelWidth_values,
    'useShortGuardInterval': useShortGuardInterval_values,
}

campaign.run_missing_simulations(list_param_combinations(param_combinations),
                                 runs=2)

# Print results
###############


def get_average_throughput(stdout):
    # This function takes a string and parses it to extract relevant
    # information
    m = re.match('.*throughput: [-+]?([0-9]*\.?[0-9]+).*', stdout,
                 re.DOTALL).group(1)
    return float(m)

###############################
# Exporting results to xarray #
###############################

# Reduce multiple runs to a single value (or tuple)
results = campaign.get_results_as_xarray(param_combinations,
                                                  get_average_throughput)

# Statistics can easily be computed from the xarray structure
results_average = results.reduce(np.mean, 'runs')
results_std = results.reduce(np.std, 'runs')

# Plot throughput for varying MCSs and different useRts/useShortGuardInterval
# parameter combinations.
stacked_params = results.stack(sgi_rts=('useShortGuardInterval','useRts')).reduce(np.mean,'runs')
stacked_params.plot.line(x='mcs', add_legend=True)
plt.xlabel('MCS')
plt.ylabel('Throughput [Mbit/s]')
plt.show()
