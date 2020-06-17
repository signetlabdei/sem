# This is an example showing how to use the ns-3 SimulationExecutionManager to
# get from compilation to result visualization.

import sem
import os
import re
import numpy as np
import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt

sem.parallelrunner.MAX_PARALLEL_PROCESSES = 10

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
    'nWifi': [1, 3],
    'distance': [1, 10],
    'useRts': ['false', 'true'],
    'useShortGuardInterval': ['false', 'true'],
    'mcs': list(range(2, 8, 2)),
    'channelWidth': ['20'],
    'simulationTime': [4],
}


def get_average_throughput(result):
    stdout = result['output']['stdout']
    m = re.match('.*throughput: [-+]?([0-9]*\.?[0-9]+).*', stdout,
                    re.DOTALL).group(1)
    return float(m)


def is_enough(campaign, params):
    throughput_values = [get_average_throughput(i) for i in
                         campaign.db.get_complete_results(params)]
    if len(throughput_values) < 2:
        return False
    avg = np.mean(throughput_values)
    std = np.std(throughput_values)
    ci = 1.96 * std / np.sqrt(len(throughput_values))
    maximum_ci = 0.1
    if ci > maximum_ci:
        print(ci)
    # print ("Current ci: %s" % ci)
    # print ("We had %s samples" % len(throughput_values))
    # print ("ci < 0.3? %s" % (ci < 0.3))
    return (ci < maximum_ci)


campaign.run_missing_simulations(params, condition_checking_function=is_enough)

# results = campaign.get_results_as_xarray(params, get_average_throughput, 'throughput', 10)
