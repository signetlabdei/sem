# This is an example showing how sem can infer default values for parameters.

import sem

#######################
# Create the campaign #
#######################

script = 'wifi-multi-tos'
ns_path = 'ns-3'
campaign_dir = "/tmp/sem-test/wifi-plotting-example"

campaign = sem.CampaignManager.new(ns_path, script, campaign_dir,
                                   runner_type='ParallelRunner',
                                   overwrite=True,
                                   check_repo=False)

print(campaign)  # This prints out the campaign settings

###################
# Run simulations #
###################

# These are all the available parameters
params = {
    'nWifi': list(range(1, 20, 2)),
    'distance': [10],
    'useRts': ['true'],
    'useShortGuardInterval': ['true'],
    'mcs': 5,
    'channelWidth': ['20'],
    'simulationTime': [4],
}
runs = 10  # Number of runs to perform for each combination
campaign.run_missing_simulations(params, 1)

# These are only some of the available parameters. The rest of the parameters
# will be filled in automatically with default values by sem.
params = {
    'nWifi': list(range(1, 20, 2)),
    'channelWidth': [20],
    'simulationTime': [4],
}
runs = 10  # Number of runs to perform for each combination
campaign.run_missing_simulations(params, 1)
