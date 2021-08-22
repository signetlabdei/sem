from sem import utils, logging
import sem
import os

#######################
# Create the campaign #
#######################
script = 'wifi-power-adaptation-distance'
ns_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ns-3')
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
    'steps': [2],
    'rtsThreshold': 2346,
    'stepsSize': 1
}
# Log Component in both formats

log_components = {
    'PowerAdaptationDistance': 'all',
    'ParfWifiManager': 'all',
    'WifiPhy': 'level_all',
    'FrameExchangeManager': 'level_all',
    'OnOffApplication': 'level_all',
    'MinstrelWifiManager': 'all'
}
# log_components = 'NS_LOG="PowerAdaptationDistance=debug:ParfWifiManager=info"'
runs = 1  # Number of runs to perform for each combination

# Actually run the simulations
# This will also print a progress bar
log_path = campaign.run_missing_simulations(
    sem.list_param_combinations(params),
    runs=runs, log_components=log_components)

if log_path:
    db, data_dir = logging.process_logs(log_path[0])
    print('Filtered Logs:')
    print(logging.filter_logs(db,
                              components={'MinstrelWifiManager': 'debug'},
                              time_begin=0.8,
                              time_end=0.81))
    try:
        # Creates a dashboard the visualize the log file passed
        utils.visualize_logs(log_path[0])
    finally:
        logging.wipe_results(db, data_dir)
