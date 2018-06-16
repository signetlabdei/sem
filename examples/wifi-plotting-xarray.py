# This is an example showing how to use the ns-3 SimulationExecutionManager to
# get from compilation to result visualization.

import sem
import os
import re
import numpy as np
import matplotlib.pyplot as plt


# Define campaign parameters
############################

script = 'wifi-multi-tos'
ns_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ns-3')
campaign_dir = "/tmp/sem-test/wifi-plotting-example"

# Create campaign
#################

campaign = sem.CampaignManager.new(ns_path, script, campaign_dir,
                                   runner='ParallelRunner')

print(campaign)

# Run simulations
#################

# Parameter space
#################
nWifi_values = [1, 3]
distance_values = [1, 10]
simulationTime_values = [10]
useRts_values = ['false', 'true']
mcs_values = list(range(8))
channelWidth_values = ['20']
useShortGuardInterval_values = ['false', 'true']
runs = 6

param_combinations = {
    'nWifi': nWifi_values,
    'distance': distance_values,
    'simulationTime': simulationTime_values,
    'useRts': useRts_values,
    'mcs': mcs_values,
    'channelWidth': channelWidth_values,
    'useShortGuardInterval': useShortGuardInterval_values,
}

campaign.run_missing_simulations(sem.list_param_combinations(param_combinations),
                                 runs=runs)

print("Simulations done.")

###############################
# Exporting results to xarray #
###############################


def get_average_throughput(stdout):
    # This function takes a string and parses it to extract relevant
    # information
    m = re.match('.*throughput: [-+]?([0-9]*\.?[0-9]+).*', stdout,
                 re.DOTALL).group(1)
    return float(m)


# Reduce multiple runs to a single value (or tuple)
results = campaign.get_results_as_xarray(param_combinations,
                                         get_average_throughput,
                                         'AvgThroughput', runs)

# Statistics can easily be computed from the xarray structure
results_average = results.reduce(np.mean, 'runs')
results_std = results.reduce(np.std, 'runs')

# Plot lines with error bars
plt.figure()
for useShortGuardInterval in ['false', 'true']:
    for useRts in ['false', 'true']:
        avg = results_average.sel(nWifi=1, distance=1,
                                  useShortGuardInterval=useShortGuardInterval,
                                  useRts=useRts)
        std = results_std.sel(nWifi=1, distance=1,
                              useShortGuardInterval=useShortGuardInterval,
                              useRts=useRts)
        plt.errorbar(x=mcs_values, y=avg, yerr=6*std)
        plt.xlabel('MCS')
        plt.ylabel('Throughput [Mbit/s]')
plt.show()

# Assess the influence of nWifi and distance parameters
plt.figure()
subplot_idx = 1
for nWifi in [1, 3]:
    for distance in [1, 10]:
        stacked_params = results.sel(nWifi=nWifi, distance=distance).stack(
            sgi_rts=('useShortGuardInterval', 'useRts')).reduce(np.mean,
                                                                'runs')

        plt.subplot(2, 2, subplot_idx)
        stacked_params.plot.line(x='mcs', add_legend=True)
        plt.xlabel('MCS')
        plt.ylabel('Throughput [Mbit/s]')
        subplot_idx += 1

plt.show()
