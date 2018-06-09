# This is an example showing how to use the ns-3 SimulationExecutionManager to
# get from compilation to result visualization.

from sem import CampaignManager, list_param_combinations
import os
from pathlib import Path
import shutil
import re
import numpy as np
import matplotlib.pyplot as plt


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

# Complete parameter space
##########################
# nWifi_values = [1, 3, 5, 7]
# distance_values = list(range(1, 50, 10))
# simulationTime_values = [10]
# useRts_values = ['false', 'true']
# mcs_values = list(range(0,8))
# channelWidth_values = ['20', '40']
# useShortGuardInterval_values = ['false', 'true']

# Small parameter space
#######################
nWifi_values = [4]
distance_values = [1]
simulationTime_values = [10]
useRts_values = ['false', 'true']
mcs_values = list(range(8))
channelWidth_values = [20]
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


def get_average_throughput(stdout):
    # This function takes a string and parses it to extract relevant
    # information
    m = re.match('.*throughput: [-+]?([0-9]*\.?[0-9]+).*', stdout,
                 re.DOTALL).group(1)
    return float(m)


def get_statistics(runs):
    return (np.mean(runs), np.std(runs))


##############################
# Exporting results to numpy #
##############################

# Reduce multiple runs to a single value (or tuple)
averaged_results = campaign.get_results_as_numpy_array(param_combinations,
                                                       get_average_throughput,
                                                       get_statistics)

# Keep individual runs
# averaged_results = campaign.get_results_as_numpy_array(param_space,
#                                                        get_average_throughput)

print("Averaged results:\n%s" % averaged_results)

# Plot throughput for a varying distance
plt.figure()
legend = []
for rts in useRts_values:
    if rts == 'true':
        rts_idx = 1
    else:
        rts_idx = 0
    for gi in useShortGuardInterval_values:
        if gi == 'true':
            gi_idx = 1
        else:
            gi_idx = 0
        plt.errorbar(mcs_values, averaged_results[rts_idx, :, gi_idx, 0],
                     yerr=2*averaged_results[rts_idx, :, gi_idx, 1])
        legend.append('RTS: %s, Short Guard Interval: %s' % (rts, gi))
plt.legend(legend)
plt.show()
