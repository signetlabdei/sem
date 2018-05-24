# This is an example showing how to use the ns-3 SimulationExecutionManager to
# run simulations exploring a parameter space

from sem import CampaignManager
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
    # os.remove(filename)
# campaign = CampaignManager.new(ns_path, script, filename)
campaign = CampaignManager.load(filename)

print(campaign)

# Run some simulations
######################

param_combination = {
    'payloadSize': 1472/2,
    'dataRate': '100Mbps',
    'tcpVariant': 'TcpHybla',
    'phyRate': 'HtMcs7',
    'simulationTime': 4,
    'pcap': 'false',
    'runs': 10
}

# campaign.run_simulations(param_space)

# campaign.get_results_as_numpy_array(param_space)
