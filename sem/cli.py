import click
import sem
import ast
import pprint
import collections
import os


@click.group()
def cli():
    """
    A command line interface to the ns-3 Simulation Execution Manager.
    """
    pass


@cli.command()
@click.option("--results-dir",
              type=click.Path(dir_okay=True, resolve_path=True),
              prompt='Directory containing results',
              help='Directory containing the simulation results.')
@click.option("--do-not-try-parsing", default=False, is_flag=True,
              help='Whether to try and automatically parse contents'
              ' of simulation output.')
@click.argument('filename', type=click.Path(resolve_path=True))
def export(results_dir, filename, do_not_try_parsing):
    """
    Export results to file.

    An extension in output is required to deduce the file type. If no extension
    is specified, a directory tree export will be used.
    Note that this command automatically tries to parse the simulation output.

    Supported extensions:

    .mat (Matlab file), .npy (Numpy file), no extension (Directory tree)
    """

    _, extension = os.path.splitext(filename)

    campaign = sem.CampaignManager.load(results_dir)

    [params, defaults] = zip(*get_params_and_defaults(campaign.db.get_params(),
                                                      campaign.db))

    # Convert to string
    string_defaults = list()
    for idx, d in enumerate(defaults):
        string_defaults.append(str(d))

    parsing_function = None if do_not_try_parsing else sem.utils.automatic_parser

    if extension == ".mat":
        campaign.save_to_mat_file(query_parameters(params, string_defaults),
                                  parsing_function, filename,
                                  runs=click.prompt("Runs to export", type=int))
    elif extension == ".npy":
        campaign.save_to_npy_file(query_parameters(params, string_defaults),
                                  parsing_function, filename,
                                  runs=click.prompt("Runs to export", type=int))
    elif extension == "":
        campaign.save_to_folders(query_parameters(params, string_defaults),
                                 filename, runs=click.prompt("Runs to export",
                                                             type=int))


@cli.command()
@click.option("--results-dir", type=click.Path(dir_okay=True,
                                               resolve_path=True),
              prompt='Directory containing results',
              help='Directory containing the simulation results.')
@click.option("--result-id", default=None, prompt=False,
              help='Id of the result to view')
@click.option("--show-simulation-output", default=False, prompt=False,
              is_flag=True, help='Whether to show the simulation output')
def view(results_dir, result_id, show_simulation_output):
    """
    View results of simulations.
    """
    campaign = sem.CampaignManager.load(results_dir)

    if show_simulation_output:
        get_results_function = campaign.db.get_complete_results
    else:
        get_results_function = campaign.db.get_results

    if result_id:
        output = '\n\n\n'.join([pprint.pformat(item) for item in
                                get_results_function(result_id=result_id)])
    else:

        [params, defaults] = zip(*get_params_and_defaults(
            campaign.db.get_params(), campaign.db))

        # Convert to string
        string_defaults = list()
        for idx, d in enumerate(defaults):
            string_defaults.append(str(d))

        script_params = query_parameters(params, string_defaults)

        # Perform the search
        output = '\n\n\n'.join([pprint.pformat(item) for item in
                                get_results_function(script_params)])

    click.echo_via_pager(output)


@cli.command()
@click.option("--results-dir", type=click.Path(dir_okay=True,
                                               resolve_path=True),
              prompt='Directory containing results',
              help='Directory containing the simulation results.')
@click.argument('result_id')
def command(results_dir, result_id):
    """
    Print the commands to debug a result.
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


@cli.command()
@click.option("--ns-3-path", type=click.Path(exists=True,
                                             resolve_path=True),
              prompt='ns-3 installation',
              help='Path to ns-3 installation')
@click.option("--results-dir", type=click.Path(dir_okay=True,
                                               resolve_path=True),
              prompt='Results directory',
              help='Path to directory where results are saved')
@click.option("--script",
              prompt='Simulation script',
              help='Simulation script to run')
@click.option("--no-optimization", default=False, is_flag=True,
              help="Whether to avoid optimization of the build")
def run(ns_3_path, results_dir, script, no_optimization):
    """
    Run simulations.
    """
    if sem.utils.DRMAA_AVAILABLE:
        click.echo("Detected available DRMAA cluster: using GridRunner.")
        runner_type = "GridRunner"
    else:
        runner_type = "ParallelRunner"

    # Create a campaign
    campaign = sem.CampaignManager.new(ns_3_path,
                                       script,
                                       results_dir,
                                       runner_type=runner_type,
                                       overwrite=False,
                                       optimized=not no_optimization)

    # Print campaign info
    click.echo(campaign)

    # Run the simulations
    [params, defaults] = zip(*get_params_and_defaults(campaign.db.get_params(),
                                                      campaign.db))

    string_defaults = list()
    for idx, d in enumerate(defaults):
        if d is not None:
            string_defaults.append(str(d))
        else:
            string_defaults.append(d)

    script_params = query_parameters(params, defaults=string_defaults)
    campaign.run_missing_simulations(script_params,
                                     runs=click.prompt("Runs", type=int))


def get_params_and_defaults(param_list, db):
    return [[p, d] for p, d in db.get_all_values_of_all_params().items()]


def query_parameters(param_list, defaults=None):

    script_params = collections.OrderedDict([k, []] for k in param_list)

    if defaults is None:
        defaults = [None for i in param_list]

    for param, default in zip(list(script_params.keys()), defaults):
        user_input = click.prompt("%s" % param, default=default)
        script_params[param] = ast.literal_eval(user_input)

    return script_params
