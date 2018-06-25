import sem
import os


# Define campaign parameters
############################

script = 'wifi-multi-tos'
ns_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ns-3')
campaign_dir = "/nfsd/signet/ns/magrin/grid-runner-testing"

# Create campaign
#################

campaign = sem.CampaignManager.new(ns_path, script, campaign_dir,
                                   runner='GridRunner',
                                   overwrite=False)

print(campaign)

# Run simulations
#################

# Parameter space
#################
nWifi_values = [1]
distance_values = [1]
simulationTime_values = [10]
useRts_values = ['false', 'true']
mcs_values = list(range(8))
channelWidth_values = ['20']
useShortGuardInterval_values = ['false', 'true']
runs = 2

param_combinations = {
    'nWifi': nWifi_values,
    'distance': distance_values,
    'simulationTime': simulationTime_values,
    'useRts': useRts_values,
    'mcs': mcs_values,
    'channelWidth': channelWidth_values,
    'useShortGuardInterval': useShortGuardInterval_values,
}

campaign.run_missing_simulations(
    sem.list_param_combinations(param_combinations), runs=runs)

print("Simulations done.")
