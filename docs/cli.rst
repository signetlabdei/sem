.. _cli:

Command Line Interface
======================

SEM offers a command line tool that can be used to run simulations, quickly
scroll the results to make sure everything looks ok and finally exporting the
results to the MATLAB .mat and Numpy .npy formats for further elaboration by the
user.

This documentation page describes a workflow that does not require writing a
Python script and only relies on the command line interface.

Getting help
------------

SEM's command line tool is simply called `sem`. To see usage information, call
the program with the `--help` flag::

  sem --help

  Usage: sem [OPTIONS] COMMAND [ARGS]...

    A command line interface to the ns-3 Simulation Execution Manager.

  Options:
    --help  Show this message and exit.

  Commands:
    command  Print the commands to debug a result.
    export   Export results to file.
    run      Run simulations.
    view     View results of simulations.

The following sections describe each sub-command in detail.

Running simulations
-------------------

Simulations can be run through the `run` sub-command. To visualize information
about a command, call it with the `--help` flag::

  sem run --help

  Usage: sem run [OPTIONS]

    Run simulations.

  Options:
    --ns-3-path PATH    Path to ns-3 installation
    --results-dir PATH  Path to directory where results are saved
    --script TEXT       Simulation script to run
    --no-optimization   Whether to avoid optimization of the build
    --help              Show this message and exit.

A choice for the required options will be prompted if they are not specified::

  sem run
  ns-3 installation: examples/ns-3
  Results directory: examples/results
  Simulation script: wifi-multi-tos
  --- Campaign info ---
  script: wifi-multi-tos
  params: ['channelWidth', 'distance', 'mcs', 'nWifi', 'simulationTime', 'useRts', 'useShortGuardInterval']
  HEAD: c19d291f35f2a394d03c3fc7c74377b65666e1a4
  ------------

After the ns-3 installation path, a directory where to save (or load, in case
the directory already exists) results and the simulation script to run
simulations with are specified by the user, the program asks for the parameter
values that need to be used to run the simulations. These can either be
specified as single values (with string enclosed by quotation marks) or as
lists, in the `[value1, value2, value3]` format::

  channelWidth: 20
  distance: 5
  mcs: [1, 3, 5, 7]
  nWifi: 1
  simulationTime: 10
  useRts: [False, True]
  useShortGuardInterval: [False, True]
  Runs: 5
  Running simulations: 100%|████████| 80/80 [02:43<00:00,  2.05s/simulation]

Note that SEM performed 80 simulations: this is indeed correct, since we
specified 3 parameters with multiple values (respectively, mcs with 4 possible
values, useRts with 2 and useShortGuardInterval with 2 possible values). The
exploration of this parameter space requires us to perform 4 * 2 * 2 = 16
simulations. If, then, we are interested in 5 repetitions for each parameter
combination, this means we need 16 * 5 = 80 simulations.

At this point, say we realize we also interested in the effect of the `nWifi`
variable, and additionally to the already used parameter value of 1 we are also
interested in seeing what happens when the value is 5: it will suffice to run
`sem run` again with the same parameters as before, and the previously ran
simulations will be loaded and taken into account when the new parameter space
is defined. This will lead to another batch of 80 simulations instead of the 160
that would be necessary to cover the entire parameter space, since we have
already performed the 80 that correspond to the parameter value of 1.
Additionally, sem will detect the already available results in the database, and
propose defaults (which can be accepted by pressing enter)::

  sem run
  ...
  channelWidth [[20]]:
  distance [[5]]:
  mcs [[1, 3, 5, 7]]:
  nWifi [[1]]: [1, 5]
  simulationTime [[10]]:
  useRts [[False, True]]:
  useShortGuardInterval [[False, True]]:
  Runs: 5
  Running simulations: 100%|████████| 80/80 [04:55<00:00,  3.69s/simulation]

Viewing results
---------------

At this point, we have a nice set of results in our database. Let's say we want
to view them in order to make sure everything is working as expected. To do so,
it's possible to use the `view` command::

  sem view --help

  Usage: sem view [OPTIONS]

    View results of simulations.

  Options:
    --results-dir PATH        Directory containing the simulation results.
    --result-id TEXT          Id of the result to view
    --hide-simulation-output  Whether to hide the simulation output
    --help                    Show this message and exit.

Note that, by default, the simulation output is hidden to avoid printing very
long files to the command line. In our case, we will enable this option since
our output is fairly small. Let's also directly specify the `--results-dir` to
skip the option querying step::

  sem view --show-simulation-output --results-dir=examples/results

  channelWidth [[20]]:
  distance [[5]]:
  mcs [[1, 3, 5, 7]]: 1
  nWifi [[1, 5]]: 1
  simulationTime [[10]]:
  useRts [[False, True]]: False
  useShortGuardInterval [[False, True]]: False

  {'meta': {'elapsed_time': 6.632506847381592,
            'id': 'fb1bd9be-b034-4f36-9562-07aa7988a266'},
  'output': {'stderr': '', 'stdout': 'Aggregated throughput: 18.9311 Mbit/s\n'},
  'params': {'RngRun': 0,
              'channelWidth': 20,
              'distance': 5,
              'mcs': 1,
              'nWifi': 1,
              'simulationTime': 10,
              'useRts': False,
              'useShortGuardInterval': False}}
  ...

Note that, as before, we are asked for the parameter ranges we are interested in
viewing. Since we've specified a single value for each parameter, the output
consisted in 5 results (of which only one is shown here), that are visualized as
printouts of python dictionaries for inspection. We can see that for the
specified parameter combination, two output files were created, and that the
script printed on the `stdout` that an aggregated throughput of 18.9311 Mbit/s
was achieved.

Getting commands to re-run simulations
--------------------------------------

In the previous section, we were able to view one of the obtained results. Let's
say we are interested in replicating that simulation, maybe to debug it. Serving
this purpose, `sem command` prints out the command that is necessary to run in
order to replicate a simulation result::

  sem command --help

  Usage: sem command [OPTIONS] RESULT_ID

    Print the commands to debug a result.

  Options:
    --results-dir PATH  Directory containing the simulation results.
    --help              Show this message and exit.

This sub-command requires the id of the simulation that we want to replicate.
Let's take the one of the previously viewed result::

  sem command --results-dir examples/results fb1bd9be-b034-4f36-9562-07aa7988a266

  Simulation command:
  ./waf --run "wifi-multi-tos --mcs=1 --RngRun=0 --useRts=False
                              --channelWidth=20 --useShortGuardInterval=False
                              --simulationTime=10 --nWifi=1 --distance=5"
  Debug command:
  ./waf --run wifi-multi-tos --command-template="gdb --args %s --mcs=1
                             --RngRun=0 --useRts=False --channelWidth=20
                             --useShortGuardInterval=False --simulationTime=10
                             --nWifi=1 --distance=5"

Two commands are printed: one for running the simulation, and the other for
running the simulation under the `gdb` debugger. Let's copy and paste the first
command, and run it from the ns-3 directory root::

  ./waf --run "wifi-multi-tos --mcs=1 --RngRun=0 --useRts=False
                              --channelWidth=20 --useShortGuardInterval=False
                              --simulationTime=10 --nWifi=1 --distance=5"

  Waf: Entering directory `/Users/davide/Work/sem/examples/ns-3/build/optimized'
  Waf: Leaving directory `/Users/davide/Work/sem/examples/ns-3/build/optimized'
  Build commands will be stored in build/optimized/compile_commands.json
  'build' finished successfully (1.352s)
  Aggregated throughput: 18.9311 Mbit/s

From the aggregated throughput value, we can confirm that this indeed is the
command that generated that result.

Exporting results
-----------------

One final step we can take now is to export the results into a format that can
be read from MATLAB, for instance. For this, we can use the export command::

  sem export --help

  Usage: sem export [OPTIONS] FILENAME

    Export results to file.

    An extension in filename is required to deduce the file type. This command
    automatically tries to parse the simulation output.

    Supported extensions:

    .mat (Matlab file), .npy (Numpy file)

  Options:
    --results-dir PATH    Directory containing the simulation results.
    --do-not-try-parsing  Whether to try and automatically parse contents of
                          simulation output.
    --help                Show this message and exit.

This command will try to automatically parse all results into a data structure,
recognizing numbers and strings as necessary. However, since our output (as can
be seen in the Viewing results section) is not formatted as a table, let's
switch parsing off. This will keep the output as a string, that can then be
processed, e.g. in MATLAB, to extract the relevant information::

  sem export --do-not-try-parsing --results-dir examples/results results.mat
  channelWidth [[20]]:
  distance [[5]]:
  mcs [[1, 3, 5, 7]]:
  nWifi [[1, 5]]:
  simulationTime [[10]]:
  useRts [[False, True]]:
  useShortGuardInterval [[False, True]]:
  Runs to export: 5

This will create a results.mat file, containing two data structures:

* An n-dimensional (with n=4 in this case) cell array, containing a `struct`
  linking each file to its parsed or non-parsed version
* A list of n structures, describing the values that can be taken by each
  parameter that the n-dimensional structure represents.
