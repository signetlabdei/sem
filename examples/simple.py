# This is a simple example of how to use the ns-3 SimulationExecutionManager

from sem import CampaignManager
from itertools import product
import os
from pathlib import Path


# Define campaign parameters
############################

script = 'wifi-tcp'
ns_path = "/home/davide/Work/ns-3-dev-gsoc/"
filename = "/tmp/wifi-tcp-sims.json"

# Create campaign
#################

# if (Path(filename).exists()):
#     os.remove(filename)
# campaign = CampaignManager.new(ns_path, script, filename)
campaign = CampaignManager.load(filename)

print(campaign)

# Run some simulations
######################

param_ranges = {
    'payloadSize': [1472/2, 1472],
    'dataRate': ['100Mbps'],
    'tcpVariant': ['TcpHybla', 'TcpHighSpeed', 'TcpHtcp', 'TcpVegas',
                   'TcpScalable', 'TcpVeno', 'TcpBic', 'TcpYeah',
                   'TcpIllinois', 'TcpWestwood', 'TcpWestwoodPlus',
                   'TcpLedbat'],
    'phyRate': ['HtMcs7'],
    'simulationTime': [4],
    'pcap': ['false'],
    'runs': [10]
}

param_space = [dict(zip(param_ranges, v)) for v in
               product(*param_ranges.values())]

# Visualize parameter space
for param in param_space:
    print(param)

# campaign.run_simulations(param_space)

# campaign.get_results_as_numpy_array(param_space)
