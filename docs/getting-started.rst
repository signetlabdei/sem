Getting started
===============

SEM operates on a simulation campaign paradigm. Simulation campaigns
are thought as a collection of results obtained from running an ns-3
simulation with different parameters. A simulation campaign is
contained in a single json database for portability, and is accessible
through a CampaignManager object, which is provided by this library.
Through this class it's possible to create new campaigns, load
existing ones, run simulations and export results to other formats.

Creating and loading a simulation campaign
------------------------------------------

Creation of a new campaign requires:

* The path of the ns-3 installation to use
* The name of the simulation script
* A name for the file where the campaign will be saved.

The following lines give an example:

::

   >>> ns_path = "/tmp/ns-3-dev-gsoc/"
   >>> script = 'wifi-tcp'
   >>> filename = "/tmp/wifi-tcp-sims.json"
   >>> campaign = CampaignManager.new(ns_path, script, filename)

Internally, SEM also checks whether the path points to a valid ns-3
installation, and whether the script is actually available for
execution or not. An error is also raised if the new campaign filename
points to an already existing file.

Alternatively, campaigns can be loaded from existing files:

::

   >>> campaign = CampaignManager.load(filename)

CampaignManager objects can be directly printed to inspect the status
of the campaign:

::

   >>> print(campaign)
   --- Campaign info ---
   ns-3 path: /tmp/ns-3-dev-gsoc/
   script: wifi-tcp
   params: ['payloadSize', 'dataRate', 'tcpVariant', 'phyRate',
            'simulationTime', 'pcap']
   commit: 9386dc7d106fd9241ff151195a0e6e5cb954d363
   ---------------------

Note that, additionally to the path and script we specified in the
campaign creation process, SEM also retrieved a list of the available
script parameters and the SHA of the current HEAD of the git
repository at the ns-3 path.

Running simulations
-------------------

Simulations can be run by specifying a list of parameter combinations.

::

   >>> param_combination = {
    'payloadSize': 1472,
    'dataRate': '100Mbps',
    'tcpVariant': 'TcpHybla',
    'phyRate': 'HtMcs7',
    'simulationTime': 4,
    'pcap': 'false'
   }
   >>> campaign.run_simulations([param_combination])
   Simulation 1/1:
   {'payloadSize': 1472, 'dataRate': '100Mbps', 'tcpVariant': 'TcpHybla',
    'phyRate': 'HtMcs7', 'simulationTime': 4, 'pcap': 'false', 'RngRun': 1}

The run_simulations method automatically queries the database looking for an
appropriate RngRun value that has not yet been used, and runs the simulations.

Multiple simulations corresponding to the exploration of a parameter space can
be run by employing the list_param_combinations function, which can take a
dictionary specifying multiple values for a key and translate it into a list of
dictionaries specifying all combinations of parameter values::

  >>> from sem import list_param_combinations
  >>> param_combinations = {
   'payloadSize': 1472,
   'dataRate': '100Mbps',
   'tcpVariant': ['TcpHybla', 'TcpNewReno'],
   'phyRate': 'HtMcs7',
   'simulationTime': [4, 8],
   'pcap': 'false'
  }
  >>> campaign.run_simulations(list_param_combinations(param_combinations))

Exporting results
-----------------

Once enough simulations are run, results can be exported to the numpy or xarray
formats. At its current state, the SEM library supports automatic parsing of the
stdout result field: in the following example, a get_average_throughput function
is passed to the export function. This allows SEM to use the function to
automatically clean up the results before putting them in an xarray structure.

::

  >>> results = campaign.get_results_as_xarray(param_combinations,
                                            get_average_throughput)

After results are exported, they can be plotted via facilities such as
matplotlib or xarray. See the examples/wifi-plotting-xarray.py script for a
complete example.
