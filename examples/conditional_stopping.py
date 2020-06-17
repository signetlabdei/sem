# %load_ext autoreload
# %autoreload 2
import sem
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


def get_average_throughput(result):
    stdout = result['output']['stdout']
    m = re.match(r'.*throughput: [-+]?([0-9]*\.?[0-9]+).*',
                 stdout, re.DOTALL).group(1)
    return float(m)


# This user-defined function should return False if more repetitions are needed
# for the current parameter combination, True if enough simulations are
# available. For instance, in this case, we decide that we have enough
# simulations based on the confidence intervals we compute based on the
# currently available data.
def is_enough(campaign, params):
    # Parse the available results
    throughput_values = [get_average_throughput(i) for i in
                         campaign.db.get_complete_results(params)]
    # If we don't have enough simulations, return False straight away
    if len(throughput_values) < 3:
        # print ("We have %s samples, not enough" % len(throughput_values))
        return False
    # Else, compute the confidence interval
    std = np.std(throughput_values)
    ci = 1.96 * std / np.sqrt(len(throughput_values))
    maximum_ci = 0.3
    # if ci > maximum_ci:
    #     print ("Current ci: %s" % ci)
    return (ci < maximum_ci)


campaign.run_missing_simulations(params, condition_checking_function=is_enough)

results = campaign.get_results_as_xarray(params,
                                         get_average_throughput,
                                         'throughput')
mean = results.squeeze().mean('runs')
std = results.squeeze().std('runs')
repetitions = results.reduce(np.vectorize(
    lambda x: not math.isnan(x))).sum('runs').squeeze()
ci = (1.96 * std / np.sqrt(repetitions)).squeeze()
mean.plot.line(x='mcs')
(mean + ci).plot.line('--', x='mcs')
(mean - ci).plot.line('--', x='mcs')
plt.show()
