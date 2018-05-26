# This is an example showing how to use the ns-3 SimulationExecutionManager to
# run a single simulation and view the result.

from sem import CampaignManager
import os
from pathlib import Path


# Define campaign parameters
############################

script = 'wifi-tcp'
ns_path = "/home/davide/Work/ns-3-dev-gsoc"
filename = "/tmp/wifi-tcp-sims.json"

# Create campaign
#################

if (Path(filename).exists()):
    os.remove(filename)
campaign = CampaignManager.new(ns_path, script, filename)

print(campaign)

# Run a simulation
##################

param_combination = {
    'payloadSize': 1472,
    'dataRate': '100Mbps',
    'tcpVariant': 'TcpHybla',
    'phyRate': 'HtMcs7',
    'simulationTime': 4,
    'pcap': 'false'
}

print('Running simulation...', end='', flush=True)
campaign.run_single_simulation(param_combination)
print(' done!')

print('Results:')
print(campaign.db.get_results())

# campaign.get_results_as_numpy_array(param_space)
