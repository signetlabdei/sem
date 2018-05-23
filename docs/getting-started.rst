Getting started
===============

SEM operates on a simulation campaign paradigm. Simulation campaigns
are accessible through a CampaignManager object. Through this class
it's possible to create new campaigns, load existing ones, run
simulations and export results.

Creating a new simulation campaign
----------------------------------

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

CampaignManager objects can be directly printed to inspect the status
of the campaign:

::

   >>> print(campaign)
   --- Campaign info ---
   ns-3 path: /tmp/ns-3-dev-gsoc/
   script: wifi-tcp
   params: ['payloadSize', 'dataRate', 'tcpVariant', 'phyRate', 'simulationTime', 'pcap']
   commit: 9386dc7d106fd9241ff151195a0e6e5cb954d363
   ------------

Note that, additionally to the path and script we specified in the
campaign creation process, SEM also retrieved a list of the available
script parameters and the SHA of the current HEAD of the git
repository at the ns-3 path.
