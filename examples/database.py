# This is an example showing functionality of the DatabaseManager class.

# A simulation campaign is created, two results are manually inserted and the
# database is queried for a set of results through specific parameter ranges.
# By changing the specified query, it can be verified that the database returns
# the correct set of results.

# This example will be turned into a test in the near future.

from sem import CampaignManager
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

db = campaign.db

print(campaign)

# Empty campaign database
db.wipe_results()

# Insert a couple of results
params = {
    'payloadSize': [1472/2],
    'dataRate': ['100Mbps'],
    'tcpVariant': ['TcpHybla'],
    'phyRate': ['HtMcs7'],
    'simulationTime': [4],
    'pcap': ['false'],
}
result = {}
result.update({**params, **{'stdout': ['0 1 2 3 4'], 'RngRun': [10]}})
db.insert_result(result)

result = {}
params['simulationTime'] = [3]
result.update({**params, **{'stdout': ['1 2 3 4 5'], 'RngRun': [11]}})
db.insert_result(result)

# Print results
params_query = {
    'simulationTime': [3, 4],  # Also try: [3] and [4] to verify query result
}

print("All results:")
pprint(db.get_results())

print("Query results:")
pprint(db.get_results(params_query))
