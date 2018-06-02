# This is an example showing how to use the ns-3 SimulationExecutionManager to
# run a single simulation and view the result.

from sem import CampaignManager, list_param_combinations
import os
from pathlib import Path
import time


# Define campaign parameters
############################

script = 'lena-simple-epc'
ns_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ns-3')
filename = "/tmp/test-sims.json"

# Create campaign
#################

if (Path(filename).exists()):
    os.remove(filename)
campaign = CampaignManager.new(ns_path, script, filename,
                               runner='ParallelRunner')

# campaign = CampaignManager.load(filename)

print(campaign)

# Run simulations
#################

param_combinations = {
    'numberOfNodes': 20,
    'simTime': 10,
    'distance': 3000,
    'interPacketInterval': 50,
    'useCa': ['true', 'false']
}

print('Running simulations...', end='', flush=True)
start = time.time()
campaign.run_missing_simulations(list_param_combinations(param_combinations), runs=5)
end = time.time()
print(' done!')

elapsed = (end-start)

print('Elapsed time: %s s' % elapsed)

# # Print results
# ###############

# print('All results:')
# campaign.db.get_results()

# query = {
#     'distance': [3000],
#     'useCa': ['true']
# }
# print('Found %s results' % len(campaign.db.get_results(query)))
