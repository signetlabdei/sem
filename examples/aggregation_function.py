# %load_ext autoreload
# %autoreload 2
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
    'nWifi': list(range(1, 20, 2)),
    'distance': [10],
    'useRts': ['true'],
    'useShortGuardInterval': ['true'],
    'mcs': 5,
    'channelWidth': ['20'],
    'simulationTime': [4],
}
runs = 20  # Number of runs to perform for each combination

# Actually run the simulations
# This will also print a progress bar
campaign.run_missing_simulations(
    sem.list_param_combinations(params),
    runs=runs)

##################################
# Exporting and plotting results #
##################################

def get_average_throughput(result):
    stdout = result['output']['stdout']
    m = re.match('.*throughput: [-+]?([0-9]*\.?[0-9]+).*', stdout,
                    re.DOTALL).group(1)
    return float(m)

# This function aggregates multiple results already parsed by the parsing
# function, and computes a cdf of the throughputs.
bins = list(np.arange(0, 100, 0.05))
def aggregate_throughputs_cdf(parsed_results):
    cdf = np.cumsum(np.histogram(parsed_results, bins=bins)[0])
    cdf = cdf / cdf[-1]
    return cdf

# Reduce multiple runs to a single value (or tuple)
results = campaign.get_results_as_xarray(params,
                                         get_average_throughput,
                                         bins[:-1], runs,
                                         aggregation_function=aggregate_throughputs_cdf)
results.squeeze().plot.line(x='metrics')
plt.xlabel('Throughput')
plt.show()


# This next piece of code 'aggregates' the parsed results simply by returning
# the list, and then creates a box plot.

def aggregate_throughputs_statistics(parsed_results):
    return parsed_results

results = campaign.get_results_as_numpy_array(params,
                                              get_average_throughput,
                                              runs,
                                              aggregation_function=aggregate_throughputs_statistics)
plt.boxplot(np.transpose(results.squeeze()))
plt.xlabel('Number of STAs')
plt.ylabel('Throughput')
plt.xticks(range(1, len(params['nWifi'])+1), labels=params['nWifi'])
plt.show()
