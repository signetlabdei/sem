# Import statements
import sem
import matplotlib.pyplot as plt
import numpy as np

# Creating the campaign object
campaign = sem.CampaignManager.new('ns-3',
                                   'wifi-multi-tos',
                                   'results-dir',
                                   check_repo=False,
                                   overwrite=False)

# Running simulations
params = {
    'nWifi': [10],
    'distance': list(range(0, 75, 5)),
    'useRts': [False],
    'useShortGuardInterval': [False],
    'mcs': [0, 3, 6],
    'channelWidth': [20],
    'simulationTime': [4],
}
runs = 20
campaign.run_missing_simulations(params, runs=runs)

# Parsing results
def get_average_throughput(result):
    return float(result['output']['stdout'])
results = campaign.get_results_as_xarray(params,
                                        get_average_throughput,
                                        'AvgThroughput', runs).squeeze()

# Plotting with confidence intervals
for mcs in params['mcs']:
    plt.errorbar(x=params['distance'],
                y=results.sel(mcs=mcs).reduce(np.mean, 'runs'),
                yerr=(1.96 * results.sel(mcs=mcs).reduce(np.std, 'runs') / np.sqrt(runs)))
plt.legend(['MCS %s' % s for s in params['mcs']])
plt.xlabel('Distance from AP [m]')
plt.ylabel('Aggregate Throughput [Mbit/s]')
plt.savefig('../../sempaper/paper/plot.pdf', bbox_inches='tight')
plt.show()
