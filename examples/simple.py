# This is a simple example of how to use the ns-3 SimulationExecutionManager

from sem import CampaignManager

# Campaign creation
###################

param_space = {
    'tcpVariant': ["TcpHybla", "TcpHighSpeed", "TcpHtcp", "TcpVegas",
                   "TcpScalable", "TcpVeno", "TcpBic", "TcpYeah",
                   "TcpIllinois", "TcpWestwood", "TcpWestwoodPlus",
                   "TcpLedbat"],
    'runs': 10
}

config = {
    'script': 'wifi-tcp',
    'ns-3-path': "/path/to/ns-3/",
}

campaign = CampaignManager.new_from_config(config, 'example-campaign.json')

campaign.run_simulations(param_space)

campaign.get_results_as_numpy_array(param_space)

campaign.print_campaign_information()
