# This is an example showing how to use the ns-3 SimulationExecutionManager to
# run a single simulation and view the result.

from sem import CampaignManager, expand_to_space
import os
from pathlib import Path
from pprint import pprint


# Define campaign parameters
############################

script = 'wifi-tcp'
ns_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ns-3')
filename = "/tmp/wifi-tcp-sims.json"

# Create campaign
#################

if (Path(filename).exists()):
    os.remove(filename)
campaign = CampaignManager.new(ns_path, script, filename)
# campaign = CampaignManager.load(filename)

print(campaign)

# Run simulations
#################

param_combinations = {
    'payloadSize': 1472,
    'dataRate': '100Mbps',
    'tcpVariant': ['TcpHybla', 'TcpHighSpeed'],
    'phyRate': 'HtMcs7',
    'simulationTime': 4,
    'pcap': 'false'
}

print('Running simulations...', end='', flush=True)
campaign.run_simulations(expand_to_space(param_combinations), verbose=True)
print(' done!')

# Print results
###############

print('All results:')
campaign.db.get_results()

query = {
    'tcpVariant': ['TcpHybla', 'TcpHighSpeed'],
    'simulationTime': [4, 8]
}
print('Query results:')
pprint(campaign.db.get_results(query))
