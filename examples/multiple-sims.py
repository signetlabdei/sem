# This is an example showing how to use the ns-3 SimulationExecutionManager to
# run a single simulation and view the result.

from sem import CampaignManager, expand_to_space
import os
from pathlib import Path


# Define campaign parameters
############################

script = 'lena-simple-epc'
ns_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ns-3')
filename = "/tmp/test-sims.json"

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
    'numberOfNodes': 10,
    'simTime': 3,
    'distance': 3000,
    'interPacketInterval': [100, 200],
    'useCa': ['true', 'false']
}

print('Running simulations...', end='', flush=True)
campaign.run_missing_simulations(expand_to_space(param_combinations), runs=3)
print(' done!')

# Print results
###############

print('All results:')
campaign.db.get_results()

query = {
    'distance': [3000],
    'useCa': ['true']
}
print('Found %s results' % len(campaign.db.get_results(query)))
