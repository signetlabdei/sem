Advanced usage
==============

ParallelRunner
--------------

A parallel runner, leveraging multi-core systems to run multiple simulations in
parallel, can be used instead of the standard SimulationRunner. Please note that
support for this feature is still experimental. To perform simulations in
parallel, use the runner parameter in the campaign creation as follows::

  >>> campaign = CampaignManager.new(ns_path, script, filename, runner='ParallelRunner')
