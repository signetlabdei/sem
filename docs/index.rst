Welcome to SEM
==============

Efficiently perform multiple ns-3 simulations, easily manage the results and
export them for processing with a few lines of Python code::

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

User's guide
------------
.. toctree::
   :hidden:

   self

.. toctree::
   :maxdepth: 2

   installation
   getting-started

API Reference
-------------

.. toctree::
   :maxdepth: 2

   api
