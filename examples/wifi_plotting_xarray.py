# This is an example showing how to use the ns-3 SimulationExecutionManager to
# get from compilation to result visualization.

import sem
import os
import re
import numpy as np
import matplotlib
import matplotlib.pyplot as plt


#######################
# Create the campaign #
#######################

script = 'wifi-multi-tos'
ns_path = 'ns-3'
campaign_dir = "/tmp/sem-test/wifi-plotting-example"

campaign = sem.CampaignManager.new(ns_path, script, campaign_dir,
                                   runner_type='ParallelRunner',
                                   overwrite=True,
                                   check_repo=False)

print(campaign)  # This prints out the campaign settings

###################
# Run simulations #
###################

# These are the available parameters
# We specify each parameter as an array containing the desired values
params = {
    'nWifi': [1, 3],
    'distance': [1, 10],
    'useRts': ['false', 'true'],
    'useShortGuardInterval': ['false', 'true'],
    'mcs': list(range(2, 8, 2)),
    'channelWidth': ['20'],
    'simulationTime': [4],
}
runs = 2  # Number of runs to perform for each combination

# Actually run the simulations
# This will also print a progress bar
campaign.run_missing_simulations(
    sem.list_param_combinations(params),
    runs=runs)

##################################
# Exporting and plotting results #
##################################

# We need to define a function to parse the results. This function will
# then be passed to the get_results_as_xarray function, that will call it
# on every result it needs to export.
def get_average_throughput(result):
    stdout = result['output']['stdout']
    m = re.match('.*throughput: [-+]?([0-9]*\.?[0-9]+).*', stdout,
                    re.DOTALL).group(1)
    return float(m)

# Reduce multiple runs to a single value (or tuple)
results = campaign.get_results_as_xarray(params,
                                         get_average_throughput,
                                         'AvgThroughput', runs)

# We can then visualize the object that is returned by the function
print(results)

# Statistics can easily be computed from the xarray structure
results_average = results.reduce(np.mean, 'runs')
results_std = results.reduce(np.std, 'runs')

# Plot lines with error bars
plt.figure(figsize=[6, 6], dpi=100)
legend_entries = []
for useShortGuardInterval in params['useShortGuardInterval']:
    for useRts in params['useRts']:
        avg = results_average.sel(nWifi=1, distance=1,
                                    useShortGuardInterval=useShortGuardInterval,
                                    useRts=useRts)
        std = results_std.sel(nWifi=1, distance=1,
                                useShortGuardInterval=useShortGuardInterval,
                                useRts=useRts)
        plt.errorbar(x=params['mcs'], y=np.squeeze(avg), yerr=6*np.squeeze(std))
        legend_entries += ['SGI = %s, RTS = %s' %
                            (useShortGuardInterval, useRts)]
        plt.legend(legend_entries)
        plt.xlabel('MCS')
        plt.ylabel('Throughput [Mbit/s]')
        plt.savefig(os.path.join(figure_path, 'throughput.png'))

# Assess the influence of nWifi and distance parameters
plt.figure(figsize=[8, 8], dpi=300)
subplot_idx = 1
for nWifi in params['nWifi']:
    for distance in params['distance']:
        stacked_params = results.sel(
            nWifi=nWifi,
            distance=distance,
            channelWidth='20',
            simulationTime=4).stack(
                sgi_rts=('useShortGuardInterval', 'useRts')
            ).reduce(np.mean, 'runs')
        plt.subplot(2, 2, subplot_idx)
        stacked_params.plot.line(x='mcs', add_legend=True)
        subplot_idx += 1
        plt.savefig(os.path.join(figure_path, 'throughputComparison.png'))
