import sem
import pprint
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style("white")

ns_path = 'ns-3'
script = 'wifi-pcf'
campaign_dir = "results"
campaign = sem.CampaignManager.new(ns_path, script, campaign_dir, overwrite=True)

params = {
    'nWifi': list(range(1, 6, 1)),
    'enablePcf': [False, True], 
    'withData': [True],
    'trafficDirection': ['upstream'],
    'cfpMaxDuration': [65536.0],
    'simulationTime': [10.0], 
    'enablePcap': [False],  
}
runs = 1

campaign.run_missing_simulations(params, runs=runs)

example_result = next(campaign.db.get_complete_results())

def get_wifi_throughput(result):
    return [float(result['output']['stdout'].split(" ")[1])]

results = campaign.get_results_as_dataframe(get_wifi_throughput, ['Throughput (Mbps)'], params=params, drop_columns=True)

sns.catplot(data=results, x='nWifi', y='Throughput (Mbps)', hue='enablePcf', kind='point')
plt.title('Througput Variation with nWiFi (PCF ON/OFF)')
plt.show()
