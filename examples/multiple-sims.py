# This is an example showing how to use the ns-3 SimulationExecutionManager to
# run a single simulation and view the result.

from sem import CampaignManager, list_param_combinations
import os
from pathlib import Path
import shutil


# Define campaign parameters
############################

script = 'lena-simple-epc'
ns_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ns-3')
campaign_dir = "/tmp/sem-test/lena-simple-epc-example"

# Create campaign
#################

if (Path(campaign_dir).exists()):
    shutil.rmtree(campaign_dir)
campaign = CampaignManager.new(ns_path, script, campaign_dir,
                               runner='ParallelRunner')

# campaign = CampaignManager.load(filename)

print(campaign)

# Run simulations
#################

param_combinations = {
    'numberOfNodes': [5, 10],
    'simTime': 5,
    'distance': [1000, 2000, 3000],
    'interPacketInterval': [50, 100, 200],
    'useCa': ['true', 'false']
}

campaign.run_missing_simulations(list_param_combinations(param_combinations),
                                 runs=5)

# # Print results
# ###############

# print('All results:')
# campaign.db.get_results()

# query = {
#     'distance': [3000],
#     'useCa': ['true']
# }
# print('Found %s results' % len(campaign.db.get_results(query)))
