The ns-3 Simulation Execution Manager
=====================================

Efficiently perform multiple ns-3 simulations and export the results for
processing in two shell commands:

.. code:: bash

  sem run
  sem export output.mat

Alternatively, achieve finer control and go from simulation running to plotting
results in a few lines of Python code::

  # Create a simulation campaign
  >>> import sem
  >>> campaign = sem.CampaignManager.new('examples/ns-3',
  ...   'wifi-multi-tos', '/tmp/results')

  # Run desired simulations with various parameter combinations
  >>> campaign.run_missing_simulations(
  ...   {'nWifi': 1, 'distance': 1, 'simulationTime': 10,
  ...   'useRts': ['false', 'true'], 'mcs': [1, 3, 5, 7],
  ...   'channelWidth': 20, 'useShortGuardInterval': 'false'},
  ...   runs=3)

  Running simulations: 100% 24/24 [00:42<00:00,  1.77s/simulation]

  # Access results (stdout, stderr and generated files)
  >>> results = campaign.db.get_complete_results()

Feature highlights
------------------

* Supports Python 3.5+;
* Runs multiple simulations in parallel;
* Automatically leverages DRMAA_-compatible computing clusters when available;
* Can parse results into Pandas dataframe, Xarray dataarray and Numpy ndarray.
  Save results in MATLAB .mat, Numpy .npy and directory tree formats;
* Enforces simulation reproducibility by requiring git-based codebase tracking.

  .. _DRMAA: https://en.wikipedia.org/wiki/DRMAA

User's guide
------------
.. toctree::
   :hidden:

   self

.. toctree::
   :maxdepth: 2

   installation
   getting-started
   cli
   detailed-functionality
   examples
   contributing

API Reference
-------------

.. toctree::
   :maxdepth: 2

   api
