# This is an example showing how to use the ns-3 SimulationExecutionManager to
# get from compilation to result visualization.

import sem
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from io import StringIO


# Define campaign parameters
############################

script = 'lorawan-sem-example'
# ns_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ns-3')
ns_path = '/Users/davide/Work/sem/examples/ns-3'
campaign_dir = "/tmp/sem-test/lorawan-parsing-example"

# Create campaign
#################

campaign = sem.CampaignManager.new(ns_path, script, campaign_dir,
                                   runner='ParallelRunner',
                                   overwrite=False, optimized=False)

print(campaign)

# Run simulations
#################

# Parameter space
#################
nDevices_values = [100, 500, 1000, 1500, 2000, 2500]
radius_values = [5500]
simulationTime_values = [600]
appPeriod_values = [600]
runs = 10

param_combinations = {
    'nDevices': nDevices_values,
    'radius': radius_values,
    'simulationTime': simulationTime_values,
    'appPeriod': appPeriod_values,
}

campaign.run_missing_simulations(sem.list_param_combinations(
    param_combinations), runs=runs)

print("Simulations done.")

####################################
# View results of first simulation #
####################################


def parse_string_as_numpy_array(string, **kwargs):
    return np.loadtxt(StringIO(string), **kwargs)


def outcome_to_number(string):
    string = string.decode('UTF-8')
    if string == 'R':
        return 0
    if string == 'U':
        return 1
    if string == 'N':
        return 2
    if string == 'I':
        return 3


for result in [campaign.db.get_complete_results({'nDevices': 1000})[0]]:
    # Plot network topology
    plt.figure()
    positions = parse_string_as_numpy_array(result['endDevices.dat'])
    plt.scatter(positions[:, 0], positions[:, 1], s=2, c=positions[:, 2])
    plt.scatter(0, 0, s=20, marker='^', c='black')
    plt.xlim([-radius_values[0], radius_values[0]])
    plt.ylim([-radius_values[0], radius_values[0]])
    plt.title("Network topology")

    # Plot gateway occupation metrics
    plt.figure()
    path_occupancy = parse_string_as_numpy_array(
        result['occupiedReceptionPaths.dat'])
    t = np.linspace(path_occupancy[0, 0], 5, num=1001, endpoint=True)
    plt.plot(t, interp1d(
        path_occupancy[:, 0], path_occupancy[:, 1], kind='previous')(t))

    packets = parse_string_as_numpy_array(result['packets.dat'],
                                          converters={5: outcome_to_number})
    successful_packets = packets[:, 5] == 0
    failed_packets = packets[:, 5] != 0
    plt.scatter(packets[successful_packets, 0],
                np.zeros([sum(successful_packets)]), s=40, c='green',
                marker='^')
    plt.scatter(packets[failed_packets, 0], np.zeros([sum(failed_packets)]),
                s=40, c='red', marker='^')

    plt.xlim([0, 5])

    plt.title("Occupied reception paths")

    plt.show()
