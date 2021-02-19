import sem
import os
import re
import numpy as np

#######################
# Create the campaign #
#######################

script = 'wifi-multi-tos'
ns_path = 'ns-3'
campaign_dir = "/tmp/sem-test/wifi-plotting-example"

campaign = sem.CampaignManager.new(ns_path, script, campaign_dir,
                                    runner_type='ParallelRunner',
                                    overwrite=True)

print(campaign)  # This prints out the campaign settings

###################
# Run simulations #
###################

# These are the available parameters
# We specify each parameter as an array containing the desired values
params = {
    'nWifi': [1],
    'distance': [10],
    'useRts': [False],
    'useShortGuardInterval': [False],
    'mcs': [5],
    'channelWidth': [20],
    'simulationTime': [0.5],
}
log_file = campaign.run_and_log(params, ['RegularWifiMac', 'WifiPhy'])

# sem.utils.parse_log(log_file)
sem.utils.parse_and_plot_log(log_file)
