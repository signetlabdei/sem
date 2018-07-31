import click
import sem
import ast
import pprint
import collections
import os
import re


@click.group()
def cli():
    """
    A command line interface to the ns-3 Simulation Execution Manager.
    """
    pass


#######
# Run #
#######

@cli.command()
@click.option("--ns-3-path",
              type=click.Path(exists=True, resolve_path=True),
              prompt='ns-3 installation directory',
              help='Path to ns-3 installation')
@click.option("--results-dir",
              type=click.Path(dir_okay=True, resolve_path=True),
              prompt='Results directory',
              help='Path to directory where results are saved')
@click.option("--script",
              prompt='Simulation script',
              help='Simulation script to run')
@click.option("--no-optimization",
              default=False,
              is_flag=True,
              help="Whether to avoid optimization of the build")
@click.option("--parameters",
              type=click.Path(exists=True, readable=True, resolve_path=True),
              default=None,
              help="File containing the parameter specification,"
              " in the following format\n"
              "param1: value1\nparam2: value2\n...")
def run(ns_3_path, results_dir, script, no_optimization, parameters):
    """
    Run multiple simulations.
    """
    # Create a campaign
    campaign = sem.CampaignManager.new(ns_3_path,
                                       script,
                                       results_dir,
                                       overwrite=False,
                                       optimized=not no_optimization)

    # Print campaign info
    click.echo(campaign)

    # Run the simulations
    [params, defaults] = zip(*get_params_and_defaults(campaign.db.get_params(),
                                                      campaign.db))

    # Check whether we need to read parameters from the command line
    if not parameters:
        # Substitute non-None defaults with their string representation
        # This will be then converted back to a Python data structure in
        # query_parameters
        string_defaults = list()
        for idx, d in enumerate(defaults):
            if d is not None:
                string_defaults.append(str(d))
            else:
                string_defaults.append(d)
        script_params = query_parameters(params, defaults=string_defaults)
    else:
        script_params = import_parameters_from_file(parameters)

    # Finally, run the simulations
    campaign.run_missing_simulations(script_params,
                                     runs=click.prompt("Total runs", type=int))


########
# View #
########

@cli.command()
@click.option("--results-dir",
              type=click.Path(dir_okay=True, resolve_path=True),
              prompt='Directory containing results',
              help='Directory containing the simulation results.')
@click.option("--result-id",
              default=None,
              prompt=False,
              help='Id of the result to view')
@click.option("--hide-simulation-output",
              default=False,
              prompt=False,
              is_flag=True,
              help='Whether to hide the simulation output')
@click.option("--parameters",
              type=click.Path(exists=True, readable=True, resolve_path=True),
              default=None,
              help="File containing the parameter specification,"
                   " in form of a python dictionary")
@click.option("--no-pager",
              is_flag=True,
              help="If used, directly print the results without passing"
              " through a pager.")
def view(results_dir, result_id, hide_simulation_output, parameters, no_pager):
    """
    View results of simulations.
    """

    campaign = sem.CampaignManager.load(results_dir)

    # Pick the most appropriate function based on the level of detail we want
    if hide_simulation_output:
        get_results_function = campaign.db.get_results
    else:
        get_results_function = campaign.db.get_complete_results

    # If a result id was specified, just query for that result
    if result_id:
        output = '\n\n\n'.join([pprint.pformat(item) for item in
                                get_results_function(result_id=result_id)])
    else:

        [params, defaults] = zip(*get_params_and_defaults(
            campaign.db.get_params(), campaign.db))

        if not parameters:
            # Convert to string
            string_defaults = list()
            for idx, d in enumerate(defaults):
                string_defaults.append(str(d))

            script_params = query_parameters(params, string_defaults)
        else:
            script_params = import_parameters_from_file(parameters)

        # Perform the search
        output = '\n\n\n'.join([pprint.pformat(item) for item in
                                get_results_function(script_params)])

    # Print the results
    if no_pager:
        click.echo(output)
    else:
        click.echo_via_pager(output)


###########
# Command #
###########

@cli.command()
@click.option("--results-dir",
              type=click.Path(dir_okay=True, resolve_path=True),
              prompt='Directory containing results',
              help='Directory containing the simulation results.')
@click.argument('result_id')
def command(results_dir, result_id):
    """
    Print the command that needs to be used to reproduce a result.
    """
    campaign = sem.CampaignManager.load(results_dir)

    result = campaign.db.get_results(result_id=result_id)[0]

    click.echo("Simulation command:")
    click.echo(sem.utils.get_command_from_result(campaign.db.get_script(),
                                                 result))
    click.echo("Debug command:")
    click.echo(sem.utils.get_command_from_result(campaign.db.get_script(),
                                                 result,
                                                 debug=True))

##########
# Export #
##########


@cli.command()
@click.option("--results-dir",
              type=click.Path(dir_okay=True, resolve_path=True),
              prompt='Directory containing results',
              help="Directory containing the simulation results.")
@click.option("--do-not-try-parsing",
              default=False,
              is_flag=True,
              help='Whether to try and automatically parse contents'
              ' of simulation output.')
@click.option("--parameters",
              type=click.Path(exists=True, readable=True, resolve_path=True),
              default=None,
              help="File containing the parameter specification,"
                   " in form of a python dictionary")
@click.argument('filename', type=click.Path(resolve_path=True))
def export(results_dir, filename, do_not_try_parsing, parameters):
    """
    Export results to file.

    An extension in filename is required to deduce the file type. If no
    extension is specified, a directory tree export will be used. Note that
    this command automatically tries to parse the simulation output.

    Supported extensions:

    .mat (Matlab file),
    .npy (Numpy file),
    no extension (Directory tree)
    """

    # Get the extension
    _, extension = os.path.splitext(filename)

    campaign = sem.CampaignManager.load(results_dir)

    [params, defaults] = zip(*get_params_and_defaults(campaign.db.get_params(),
                                                      campaign.db))

    if do_not_try_parsing:
        parsing_function = None
    else:
        parsing_function = sem.utils.automatic_parser

    if not parameters:
        # Convert to string
        string_defaults = list()
        for idx, d in enumerate(defaults):
            string_defaults.append(str(d))
        parameter_query = query_parameters(params, string_defaults)
    else:
        # Import specified parameter file
        parameter_query = import_parameters_from_file(parameters)

    if extension == ".mat":
        campaign.save_to_mat_file(parameter_query, parsing_function, filename,
                                  runs=click.prompt("Runs", type=int))
    elif extension == ".npy":
        campaign.save_to_npy_file(parameter_query, parsing_function, filename,
                                  runs=click.prompt("Runs", type=int))
    elif extension == "":
        campaign.save_to_folders(parameter_query, filename,
                                 runs=click.prompt("Runs", type=int))
    else:  # Unrecognized format
        raise ValueError("Format not recognized")


def get_params_and_defaults(param_list, db):
    """
    Deduce [parameter, default] pairs from simulations available in the db.

    Args:
      param_list (list): List of parameters to query for.
      db (DatabaseManager): Database where to query for defaults.
    """
    return [[p, d] for p, d in db.get_all_values_of_all_params().items()]


def query_parameters(param_list, defaults=None):
    """
    Asks the user for parameters. If available, proposes some defaults.

    Args:
        param_list (list): List of parameters to ask the user for values.
        defaults (list): A list of proposed defaults. It must be a list of the
            same length as param_list. A value of None in one element of the
            list means that no default will be proposed for the corresponding
            parameter.
    """

    script_params = collections.OrderedDict([k, []] for k in param_list)

    for param, default in zip(list(script_params.keys()), defaults):
        user_input = click.prompt("%s" % param, default=default)
        script_params[param] = ast.literal_eval(user_input)

    return script_params


def import_parameters_from_file(parameters_file):
    """
    Try importing a parameter dictionary from file.

    We expect values in parameters_file to be defined as follows:
        param1: value1
        param2: [value2, value3]
    """
    params = {}

    with open(parameters_file, 'r') as f:
        matches = re.findall('(.*): (.*)', f.read())

    for m in matches:
        params[m[0]] = ast.literal_eval(m[1])

    return params
