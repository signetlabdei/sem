# This is an example showing how to use the ns-3 SimulationExecutionManager to
# get from compilation to result visualization.


def main():

    import sem
    import numpy as np
    import os
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from scipy.interpolate import interp1d

    # Define campaign parameters
    ############################

    script = 'lorawan-sem-example'
    ns_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ns-3')
    campaign_dir = "/tmp/sem-test/lorawan-parsing-example"

    # Create campaign
    #################

    campaign = sem.CampaignManager.new(ns_path, script, campaign_dir,
                                       runner_type='ParallelRunner',
                                       overwrite=True)

    print(campaign)

    # Run simulations
    #################

    # Parameter space
    #################
    nDevices_values = [100, 500, 1000, 2000, 4000]
    radius_values = [5500]
    simulationTime_values = [600]
    appPeriod_values = [600]
    runs = 3

    param_combinations = {
        'nDevices': nDevices_values,
        'radius': radius_values,
        'simulationTime': simulationTime_values,
        'appPeriod': appPeriod_values,
    }

    campaign.run_missing_simulations(sem.list_param_combinations(
        param_combinations), runs=runs)

    print("Simulations done.")

    ####################################
    # View results of first simulation #
    ####################################

    figure_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'figures')
    if not os.path.isdir(figure_path):
        os.makedirs(figure_path)

    for result in [campaign.db.get_complete_results({'nDevices': 4000})[0]]:

        dtypes = {'endDevices': (float, float, int),
                  'occupiedReceptionPaths': (float, int),
                  'packets': (float, int, float, int, float, int)}

        string_to_number = {'R': 0, 'U': 1, 'N': 2, 'I': 3}

        converters = {'packets': {5: lambda x:
                                  string_to_number[x.decode('UTF-8')]}}

        parsed_result = sem.utils.automatic_parser(result, dtypes, converters)

        # Plot network topology
        plt.figure(figsize=[6, 6], dpi=300)
        positions = np.array(parsed_result['endDevices'])
        plt.scatter(positions[:, 0], positions[:, 1], s=2, c=positions[:, 2])
        plt.scatter(0, 0, s=20, marker='^', c='black')
        plt.xlim([-radius_values[0], radius_values[0]])
        plt.ylim([-radius_values[0], radius_values[0]])
        plt.title("Network topology")
        plt.savefig(os.path.join(figure_path, 'networkTopology.png'))

        # Plot gateway occupation metrics
        plt.figure(figsize=[6, 6], dpi=300)
        path_occupancy = np.array(parsed_result['occupiedReceptionPaths'])
        t = np.linspace(path_occupancy[0, 0], 5, num=1001, endpoint=True)
        plt.plot(t, interp1d(
            path_occupancy[:, 0], path_occupancy[:, 1], kind='nearest')(t))

        packets = np.array(parsed_result['packets'])

        # Plot successful packets
        successful_packets = packets[:, 5] == 0
        plt.scatter(packets[successful_packets, 0],
                    np.zeros([sum(successful_packets)]), s=40, c='green',
                    marker='^')
        # Plot failed packets
        failed_packets = packets[:, 5] != 0
        plt.scatter(packets[failed_packets, 0],
                    np.zeros([sum(failed_packets)]),
                    s=40, c='red', marker='^')

        plt.xlim([0, 5])
        plt.title("Occupied reception paths")
        plt.savefig(os.path.join(figure_path, 'receptionPaths.png'))

    #################################
    # Plot probabilities of success #
    #################################

    # This is the function that we will pass to the export function
    def get_outcome_probabilities(result):

        # Parse all files into lists
        parsed_result = sem.utils.automatic_parser(result, dtypes, converters)

        # Get the file we are interested in
        outcomes = np.array(parsed_result['packets'])[:, 5]
        successful = sum(outcomes == 0)
        interfered = sum(outcomes == 1)
        no_more_receivers = sum(outcomes == 2)
        under_sensitivity = sum(outcomes == 3)
        total = outcomes.shape[0]

        return [successful/total, interfered/total,
                no_more_receivers/total, under_sensitivity/total]

    metrics = ['successful', 'interfered', 'no_more_receivers',
               'under_sensitivity']
    results = campaign.get_results_as_xarray(param_combinations,
                                             get_outcome_probabilities,
                                             metrics,
                                             runs)

    plt.figure(figsize=[6, 6], dpi=300)
    for metric in metrics:
        plt.plot(param_combinations['nDevices'],
                 results.reduce(np.mean, 'runs').sel(
                     radius=5500,
                     simulationTime=600,
                     appPeriod=600,
                     metrics=metric))
    plt.xlabel("Number of End Devices")
    plt.ylabel("Probability")
    plt.legend(["Success", "Interfered", "No more receivers",
                "Under sensitivity"])
    plt.savefig(os.path.join(figure_path, 'outcomes.png'))


if __name__ == '__main__':
    main()
