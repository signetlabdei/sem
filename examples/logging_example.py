import sem

#######################
# Create the campaign #
#######################

script = 'wifi-power-adaptation-distance'
ns_path = './ns-3'
campaign_dir = "/tmp/sem-test/wifi-plotting-example"

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
# Log Component in both formats

log_component = {
    'PowerAdaptationDistance': 'debug',
    'ParfWifiManager': 'info'
}
# log_component = 'NS_LOG="PowerAdaptationDistance=debug"'
runs = 1  # Number of runs to perform for each combination

# Actually run the simulations
# This will also print a progress bar
log_path = campaign.run_missing_simulations(
    sem.list_param_combinations(params),
    runs=runs, log_component=log_component)

if log_path:
    print(log_path)

log_component = {"PowerAdaptationDistance": 'debug'}
print("Testing log_component: %s" % log_component)
print("This should be a 1: got %s" %
      len(campaign.db.get_complete_results(log_component=log_component)))

log_component = {"ParfWifiManager": 'info'}
print("Testing log_component: %s" % log_component)
print("This should be a 1: got %s" %
      len(campaign.db.get_complete_results(log_component=log_component)))

log_component = {"ParfWifiManager": 'level_info'}
print("Testing log_component: %s" % log_component)
print("This should be a 0: got %s" %
      len(campaign.db.get_complete_results(log_component=log_component)))

log_component = {"PowerAdaptationDistance": 'all'}
print("Testing log_component: %s" % log_component)
print("This should be a 0: got %s" %
      len(campaign.db.get_complete_results(log_component=log_component)))
