# This is an example showing how to use the ns-3 SimulationExecutionManager to
# run simulations exploring a parameter space

from sem import CampaignManager, DatabaseManager
import os
from pathlib import Path
from pprint import PrettyPrinter


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

db = campaign.db

print(campaign)

params = {
    'payloadSize': [1472/2],
    'dataRate': ['100Mbps'],
    'tcpVariant': ['TcpHybla'],
    'phyRate': ['HtMcs7'],
    'simulationTime': [4],
    'pcap': ['false'],
}

# Empty database
db.wipe_results()

# Insert a couple of results
result = {}
result.update({**params, **{'stdout': ['0 1 2 3 4'], 'run': [10]}})
db.insert_result(result)

result = {}
params['simulationTime'] = [3]
result.update({**params, **{'stdout': ['1 2 3 4 5'], 'run': [11]}})
db.insert_result(result)

# Print results

params_query = {
    'payloadSize': [1472/2],
    'dataRate': ['100Mbps'],
    'tcpVariant': ['TcpHybla'],
    'phyRate': ['HtMcs7'],
    'simulationTime': [3, 4],
    'pcap': ['false'],
}

print("All results:")
PrettyPrinter(indent=4).pprint(db.get_results())

print("Query results:")
PrettyPrinter(indent=4).pprint(db.get_results(params_query))
