Examples walkthrough
====================

SEM offers some examples in the form of python scripts in the `examples/`
folder. This page walks through these scripts, explains what they achieve and
how they leverage the facilities provided by SEM with different objectives.

`wifi_example.py`
-------------------------

The full script is available here_. This document will only show the relevant
portions of the code.

.. _here: https://github.com/signetlabdei/sem/blob/master/examples/wifi_example.py

This example showcases how SEM's integration with the `xarray` python library
can be leveraged to quickly obtain plots.

After running simulations through the
:meth:`sem.CampaignManager.run_missing_simulations` method, results are exported
to an `xarray` data structure through the
:meth:`sem.CampaignManager.get_results_as_xarray` function::

  ##################################
  # Exporting and plotting results #
  ##################################

  # We need to define a function to parse the results. This function will
  # then be passed to the get_results_as_xarray function, that will call it
  # on every result it needs to export.
  def get_average_throughput(result):
      stdout = result['output']['stdout']
      m = re.match('.*throughput: [-+]?([0-9]*\.?[0-9]+).*', stdout,
                    re.DOTALL).group(1)
      return float(m)

  # Reduce multiple runs to a single value (or tuple)
  results = campaign.get_results_as_xarray(params,
                                            get_average_throughput,
                                            'AvgThroughput', runs)

  # We can then visualize the object that is returned by the function
  print(results)

This function essentially goes over the specified parameter space, and applies a
user-defined function to each one, to obtain some metrics. In the case of the
`wifi_example.py` example, a `get_average_throughput` function is defined. This
function takes as parameter a result, in the form of a dictionary with the
following structure:

.. code::

  result = {
    'meta': {
      'id': Simulation ID,
      'elapsed_time': Time spent running the simulation,
    },
    'params': {
      'param1': Value,
      ...
    }
    'output': {
      'stdout': String containing output of simulation,
      'stderr': String containing errors of simulation,
      'filename': Contents of filename output file,
      ...
    }
  }

and outputs a single value, which is obtained by parsing the `stdout` field of
the `output` value. The resulting structure is then saved in the `results`
variable, and can be inspected by using the `print` function.


