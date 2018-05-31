# This is an example showing how to use the ns-3 SimulationExecutionManager to
# run a single simulation and view the result.

from sem import CampaignManager, expand_to_space
import os
from pprint import pprint


# Define campaign parameters
############################

script = 'lena-pathloss-traces'
ns_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ns-3')
filename = "/tmp/test-sims.json"

# Create campaign
#################

# if (Path(filename).exists()):
#     os.remove(filename)
# campaign = CampaignManager.new(ns_path, script, filename)
campaign = CampaignManager.load(filename)

print(campaign)

# Run simulations
#################

param_combinations = {
    'enbDist': list(range(20, 100, 10)),
    'radius': 10,
    'numUes': list(range(1, 5))
}

print('Running simulations...', end='', flush=True)
campaign.run_missing_simulations(expand_to_space(param_combinations), runs=5)
print(' done!')

# Print results
###############

print('All results:')
campaign.db.get_results()

query = {
    'enbDist': [20, 30, 40],
    'radius': 10,
    'numUes': [1, 3]
}
print('Query results:')
pprint(campaign.db.get_results(query))
