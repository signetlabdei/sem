import sem
import pprint
import os

#######################
# Create the campaign #
#######################

script = 'wifi-power-adaptation-distance'
ns_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ns-3')
campaign_dir = '/tmp/sem-test/wifi-plotting-example'

campaign = sem.CampaignManager.new(ns_path, script, campaign_dir,
                                   runner_type='ParallelRunner',
                                   overwrite=True,
                                   optimized=False,
                                   check_repo=False)

print(campaign)  # This prints out the campaign settings

###################
# Run simulations #
###################

params = {
    'powerLevels': 18.0,
    'manager': 'ns3::ParfWifiManager',
    'AP1_y': 0,
    'STA1_y': 0,
    'maxPower': 17,
    'outputFileName': 'parf',
    'AP1_x': 0,
    'STA1_x': 5.0,
    'stepsTime': 1,
    'minPower': 0,
    'steps': 2,
    'rtsThreshold': 2346,
    'stepsSize': 1
}

# Log Components in both formats
log_components = {
    'PowerAdaptationDistance': 'debug',
    'ParfWifiManager': 'info'
}
# log_components = 'NS_LOG="PowerAdaptationDistance=debug:ParfWifiManager=info"'

# Run the simulations with logging enabled
log_path = campaign.run_missing_simulations(
    sem.list_param_combinations(params),
    runs=1, log_components=log_components)

if log_path:
    print(log_path)

# Print the complete result
example_result = campaign.db.get_complete_results(log_components=log_components)[0]
print("Complete result:")
pprint.pprint(example_result)

# Printing the generated logs
print("Generated logs:")
pprint.pprint(example_result['output']['stderr'])

# Printing the meta entry describing what kind of logs were used for this
# simulation
print("Log component information:")
pprint.pprint(example_result['meta']['log_components'])
