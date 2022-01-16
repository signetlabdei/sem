import collections
import gc
import os
import shutil
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from random import shuffle

from multiprocessing import Pool

import numpy as np
import xarray as xr
from scipy.io import savemat
from tqdm import tqdm

from .database import DatabaseManager
from .lptrunner import LptRunner
from .parallelrunner import ParallelRunner
from .conditionalrunner import ConditionalRunner
from .runner import SimulationRunner
from .utils import DRMAA_AVAILABLE, list_param_combinations
import pandas as pd

if DRMAA_AVAILABLE:
    from .gridrunner import GridRunner

def parse_result(param):
    result, function_yields_multiple_results, result_parsing_function, param_columns = param
    data = []
    if function_yields_multiple_results:
        for r in result_parsing_function(result):
            param_values = list(deepcopy(result['params']).values())
            if param_columns != 'all':
                param_keys = list(deepcopy(result['params']).keys())
                param_values_to_keep = [v for k, v in list(zip(param_keys, param_values)) if k in param_columns]
            else:
                param_values_to_keep = param_values
            param_values_to_keep += [r] if not isinstance(r, list) else r
            data += [param_values_to_keep]
    else:
        param_values = list(deepcopy(result['params']).values())
        if param_columns != 'all':
            param_keys = list(deepcopy(result['params']).keys())
            param_values_to_keep = list([v for k, v in list(zip(param_keys, param_values)) if k in param_columns])
        else:
            param_values_to_keep = param_values
        parsed = result_parsing_function(result)
        param_values_to_keep += [parsed] if not isinstance(parsed, list) else parsed
        data += [param_values_to_keep]
    return data

class CampaignManager(object):
    """
    This Simulation Execution Manager class can be used as an interface to
    execute simulations and access the results of simulation campaigns.

    The CampaignManager class wraps up a DatabaseManager and a
    SimulationRunner, which are used internally but can also be accessed as
    public member variables.
    """

    #######################################
    # Campaign initialization and loading #
    #######################################

    def __init__(self, campaign_db, campaign_runner, check_repo=True):
        """
        Initialize the Simulation Execution Manager, using the provided
        CampaignManager and SimulationRunner instances.

        This method should never be used on its own, but only as a constructor
        from the new and load @classmethods.

        Args:
            campaign_db (DatabaseManager): the DatabaseManager object to
                associate to this campaign.
            campaign_runner (SimulationRunner): the SimulationRunner object to
                associate to this campaign.
        """
        self.db = campaign_db
        self.runner = campaign_runner
        self.check_repo = check_repo

        # Check that the current repo commit corresponds to the one specified
        # in the campaign
        if self.check_repo:
            self.check_repo_ok()

    @classmethod
    def new(cls, ns_path, script, campaign_dir, runner_type='Auto',
            overwrite=False, optimized=True, check_repo=True,
            skip_configuration=False, max_parallel_processes=None):
        """
        Create a new campaign from an ns-3 installation and a campaign
        directory.

        This method will create a DatabaseManager, which will install a
        database in the specified campaign_dir. If a database is already
        available at the ns_path described in the specified campaign_dir and
        its configuration matches config, this instance is used instead. If the
        overwrite argument is set to True instead, the specified directory is
        wiped and a new campaign is created in its place.

        Furthermore, this method will initialize a SimulationRunner, of type
        specified by the runner_type parameter, which will be locked on the
        ns-3 installation at ns_path and set up to run the desired script.

        Finally, note that creation of a campaign requires a git repository to
        be initialized at the specified ns_path. This will allow SEM to save
        the commit at which the simulations are run, enforce reproducibility
        and avoid mixing results coming from different versions of ns-3 and its
        libraries.

        Args:
            ns_path (str): path to the ns-3 installation to employ in this
                campaign.
            script (str): ns-3 script that will be executed to run simulations.
            campaign_dir (str): path to the directory in which to save the
                simulation campaign database.
            runner_type (str): implementation of the SimulationRunner to use.
                Value can be: SimulationRunner (for running sequential
                simulations locally), ParallelRunner (for running parallel
                simulations locally), GridRunner (for running simulations using
                a DRMAA-compatible parallel task scheduler). Use Auto to
                automatically pick the best runner.
            overwrite (bool): whether to overwrite already existing
                campaign_dir folders. This deletes the directory if and only if
                it only contains files that were detected to be created by sem.
            optimized (bool): whether to configure the runner to employ an
                optimized ns-3 build.
            skip_configuration (bool): whether to skip the configuration step,
                and only perform compilation.
                NOTE: if skip_configuration=True and optimized=True, the build
                folder should be manually set to --out=build/optimized.
        """
        # Convert paths to be absolute
        ns_path = os.path.abspath(ns_path)
        campaign_dir = os.path.abspath(campaign_dir)

        # Verify if the specified campaign is already available
        if Path(campaign_dir).exists() and not overwrite:
            # Try loading
            manager = CampaignManager.load(campaign_dir, ns_path,
                                           runner_type=runner_type,
                                           optimized=optimized,
                                           check_repo=check_repo,
                                           skip_configuration=skip_configuration,
                                           max_parallel_processes=max_parallel_processes)

            if manager.db.get_script() == script:
                return manager
            else:
                del manager

        # Initialize runner
        runner = CampaignManager.create_runner(ns_path, script,
                                               runner_type=runner_type,
                                               optimized=optimized,
                                               skip_configuration=skip_configuration,
                                               max_parallel_processes=max_parallel_processes)

        # Get list of parameters to save in the DB
        params = runner.get_available_parameters()

        # Get current commit
        commit = ""
        if check_repo:
            from git import Repo, exc
            repo = Repo(ns_path)
            commit = repo.head.commit.hexsha
            if repo.is_dirty(untracked_files=True):
                raise Exception("ns-3 repository is not clean")

        # Create a database manager from the configuration
        db = DatabaseManager.new(script=script,
                                 params=params,
                                 commit=commit,
                                 campaign_dir=campaign_dir,
                                 overwrite=overwrite)

        return cls(db, runner, check_repo)

    @classmethod
    def load(cls, campaign_dir, ns_path=None, runner_type='Auto',
             optimized=True, check_repo=True, skip_configuration=False,
             max_parallel_processes=None):
        """
        Load an existing simulation campaign.

        Note that specifying an ns-3 installation is not compulsory when using
        this method: existing results will be available, but in order to run
        additional simulations it will be necessary to specify a
        SimulationRunner object, and assign it to the CampaignManager.

        Args:
            campaign_dir (str): path to the directory in which to save the
                simulation campaign database.
            ns_path (str): path to the ns-3 installation to employ in this
                campaign.
            runner_type (str): implementation of the SimulationRunner to use.
                Value can be: SimulationRunner (for running sequential
                simulations locally), ParallelRunner (for running parallel
                simulations locally), GridRunner (for running simulations using
                a DRMAA-compatible parallel task scheduler).
            optimized (bool): whether to configure the runner to employ an
                optimized ns-3 build.
            skip_configuration (bool): whether to skip the configuration step,
                and only perform compilation.
        """
        # Convert paths to be absolute
        if ns_path is not None:
            ns_path = os.path.abspath(ns_path)
        campaign_dir = os.path.abspath(campaign_dir)

        # Read the existing configuration into the new DatabaseManager
        db = DatabaseManager.load(campaign_dir)
        script = db.get_script()

        runner = None
        if ns_path is not None:
            runner = CampaignManager.create_runner(ns_path, script,
                                                   runner_type, optimized,
                                                   skip_configuration,
                                                   max_parallel_processes=max_parallel_processes)

        return cls(db, runner, check_repo)

    def create_runner(ns_path, script, runner_type='Auto',
                      optimized=True, skip_configuration=False,
                      max_parallel_processes=None):
        """
        Create a SimulationRunner from a string containing the desired
        class implementation, and return it.

        Args:
            ns_path (str): path to the ns-3 installation to employ in this
                SimulationRunner.
            script (str): ns-3 script that will be executed to run simulations.
            runner_type (str): implementation of the SimulationRunner to use.
                Value can be: SimulationRunner (for running sequential
                simulations locally), ParallelRunner (for running parallel
                simulations locally), GridRunner (for running simulations using
                a DRMAA-compatible parallel task scheduler). If Auto,
                automatically pick the best available runner (GridRunner if
                DRMAA is available, ParallelRunner otherwise).
            optimized (bool): whether to configure the runner to employ an
                optimized ns-3 build.
            skip_configuration (bool): whether to skip the configuration step,
                and only perform compilation.
        """
        # locals() contains a dictionary pairing class names with class
        # objects: we can create the object using the desired class starting
        # from its name.
        if runner_type == 'Auto' and DRMAA_AVAILABLE:
            runner_type = 'GridRunner'
        elif runner_type == 'Auto':
            runner_type = 'ParallelRunner'

        return locals().get(runner_type,
                            globals().get(runner_type))(
                                ns_path, script, optimized=optimized,
                                skip_configuration=skip_configuration,
                                max_parallel_processes=max_parallel_processes)

    def check_and_fill_parameters(self, param_list, needs_rngrun):
        # Check all parameter combinations fully specify the desired simulation
        desired_params = list(self.db.get_params().keys())
        for p in param_list:
            # Besides the parameters that were actually passed, we add the ones
            # that are always available in every script
            if isinstance(p, list):
                parameter = p[0]
            else:
                parameter = p
            passed = list(parameter.keys())
            available = ['RngRun'] + desired_params if needs_rngrun else desired_params
            if set(passed) != set(available):
                not_supported_parameters = set(passed) - set(available)
                if not_supported_parameters:
                    raise ValueError("The following parameters are "
                                     "not supported by the script: %s\n" %
                                     not_supported_parameters)
            # Automatically fill remaining parameters with defaults
            additional_required_parameters = set(available) - set(passed)
            for additional_parameter in additional_required_parameters:
                p[additional_parameter] = self.db.get_params()[additional_parameter]

    ######################
    # Simulation running #
    ######################

    def run_simulations(self, param_list, show_progress=True, stop_on_errors=True):
        """
        Run several simulations specified by a list of parameter combinations.

        Note: this function does not verify whether we already have the
        required simulations in the database - it just runs all the parameter
        combinations that are specified in the list.

        Args:
            param_list (list): list of parameter combinations to execute.
                Items of this list are dictionaries, with one key for each
                parameter, and a value specifying the parameter value (which
                can be either a string or a number).
            show_progress (bool): whether or not to show a progress bar with
                percentage and expected remaining time.
        """

        # Make sure we have a runner to run simulations with.
        # This can happen in case the simulation campaign is loaded and not
        # created from scratch.
        if self.runner is None:
            raise Exception("No runner was ever specified"
                            " for this CampaignManager.")

        # Return if the list is empty
        if param_list == []:
            return

        self.check_and_fill_parameters(param_list, needs_rngrun=True)

        # Check that the current repo commit corresponds to the one specified
        # in the campaign
        if self.check_repo:
            self.check_repo_ok()

        # Build ns-3 before running any simulations
        # At this point, we can assume the project was already configured
        self.runner.configure_and_build(skip_configuration=True)

        # Shuffle simulations
        # This mixes up long and short simulations, and gives better time
        # estimates for the simple ParallelRunner.
        shuffle(param_list)

        # Offload simulation execution to self.runner
        # Note that this only creates a generator for the results, no
        # computation is performed on this line.
        results = self.runner.run_simulations(param_list,
                                              self.db.get_data_dir(),
                                              stop_on_errors=stop_on_errors)

        # Wrap the result generator in the progress bar generator.
        if show_progress:
            result_generator = tqdm(results, total=len(param_list),
                                    unit='simulation',
                                    desc='Running simulations')
        else:
            result_generator = results

        self.run_and_save_results(result_generator)

    def run_and_save_results(self, result_generator, batch_results=True):
        # Insert result object in db. Using the generator here ensures we
        # save results as they are finalized by the SimulationRunner, and
        # that they are kept even if execution is terminated abruptly by
        # crashes or by a KeyboardInterrupt.
        results_batch = []
        last_save_time = datetime.now()

        for result in result_generator:

            results_batch += [result]

            # Save results to disk once every 60 seconds
            if not batch_results:
                self.db.insert_results(results_batch)
                results_batch = []
            elif (batch_results and
                  (datetime.now() - last_save_time).total_seconds() > 60):
                self.db.insert_results(results_batch)
                self.db.write_to_disk()
                results_batch = []
                last_save_time = datetime.now()

        self.db.insert_results(results_batch)
        self.db.write_to_disk()

    def get_missing_simulations(self, param_list, runs=None,
                                with_time_estimate=False):
        """
        Return a list of the simulations among the required ones that are not
        available in the database.

        Args:
            param_list (list): a list of dictionaries containing all the
                parameters combinations.
            runs (int): an integer representing how many repetitions are wanted
                for each parameter combination, None if the dictionaries in
                param_list already feature the desired RngRun value.
        """

        params_to_simulate = []

        # Fill up a possibly impartial parameter definition with defaults
        if runs is None:
            self.check_and_fill_parameters (param_list, needs_rngrun=True)
        else:
            self.check_and_fill_parameters (param_list, needs_rngrun=False)

        if runs is not None:  # Get next available runs from the database
            next_runs = self.db.get_next_rngruns()
            available_results = [r for r in self.db.get_results()]
            for param_comb in param_list:
                # Count how many param combinations we found, and remove them
                # from the list of available_results for faster searching in the
                # future
                needed_runs = runs
                if with_time_estimate:
                    time_prediction = float("Inf")
                for i, r in enumerate(available_results):
                    if param_comb == {k: r['params'][k] for k in
                                      r['params'].keys() if k != "RngRun"}:
                        needed_runs -= 1
                        if with_time_estimate:
                            time_prediction = float(r['meta']['elapsed_time'])
                new_param_combs = []
                for needed_run in range(needed_runs):
                    # Here it's important that we make copies of the
                    # dictionaries, so that if we modify one we don't modify
                    # the others. This is necessary because after this step,
                    # typically, we will add the RngRun key which must be
                    # different for each copy.
                    new_param = deepcopy(param_comb)
                    new_param['RngRun'] = next(next_runs)
                    if with_time_estimate:
                        new_param_combs += [[new_param, time_prediction]]
                    else:
                        new_param_combs += [new_param]
                params_to_simulate += new_param_combs
        else:
            for param_comb in param_list:
                previous_results = self.db.get_results(param_comb)
                if not previous_results:
                    if with_time_estimate:
                        # Try and find results with different RngRun to provide
                        # a time prediction
                        param_comb_no_rngrun = {k:param_comb[k] for k in
                                                param_comb.keys() if k != "RngRun"}
                        prev_results_different_rngrun = self.db.get_results(param_comb_no_rngrun)
                        if prev_results_different_rngrun:
                            time_prediction = float(prev_results_different_rngrun[0]['meta']['elapsed_time'])
                        else:
                            time_prediction = float("Inf")
                        params_to_simulate += [[param_comb, time_prediction]]
                    else:
                        params_to_simulate += [param_comb]

        return params_to_simulate

    def run_missing_simulations(self, param_list, runs=None,
                                condition_checking_function=None,
                                stop_on_errors=True):
        """
        Run the simulations from the parameter list that are not yet available
        in the database.

        This function also makes sure that we have at least runs replications
        for each parameter combination.

        Additionally, param_list can either be a list containing the desired
        parameter combinations or a dictionary containing multiple values for
        each parameter, to be expanded into a list.

        Args:
            param_list (list, dict): either a list of parameter combinations or
                a dictionary to be expanded into a list through the
                list_param_combinations function.
            runs (int): the number of runs to perform for each parameter
                combination. This parameter is only allowed if the param_list
                specification doesn't feature an 'RngRun' key already.
        """
        # Expand the parameter specification
        param_list = list_param_combinations(param_list)

        # In this case, we need to run simulations in batches
        if runs is None and condition_checking_function:
            next_runs = self.db.get_next_rngruns()
            # Create a ConditionalRunner
            cr = ConditionalRunner(self.runner.path,
                                   self.runner.script,
                                   self.runner.optimized,
                                   max_parallel_processes=self.runner.max_parallel_processes)
            # Set up the runner's stopping condition function
            cr.stopping_function = lambda x: condition_checking_function(self, x)
            # Set up the runner's iterator for next runs
            cr.next_runs = next_runs

            # Fill up a possibly impartial parameter definition with defaults
            self.check_and_fill_parameters (param_list, needs_rngrun=False)

            self.run_and_save_results(cr.run_simulations(param_list,
                                                         self.db.get_data_dir(),
                                                         stop_on_errors=stop_on_errors),
                                      batch_results=False)

        # Otherwise, we just run all required runs for each combination
        if condition_checking_function is None:
            # If we are passed a list already, just run the missing simulations
            if isinstance(self.runner, LptRunner):
                self.run_simulations(
                    self.get_missing_simulations(param_list,
                                                 runs,
                                                 with_time_estimate=True),
                    stop_on_errors=stop_on_errors)
            else:
                self.run_simulations(
                    self.get_missing_simulations(param_list, runs),
                    stop_on_errors=stop_on_errors)

    #####################
    # Result management #
    #####################

    def get_results_as_dataframe(self,
                                 result_parsing_function,
                                 columns=None,
                                 params=None,
                                 runs=None,
                                 param_columns='all',
                                 drop_constant_columns=False,
                                 parallel_parsing=False,
                                 verbose=False):
        """
        Return a Pandas DataFrame containing results parsed using a
        user-specified function.

        If function_yields_multiple_results if False, result_parsing_function is
        expected to return a list of outputs for each parsed result, and column
        should contain an equal number of labels describing the contents of the
        output list.

        If function_yields_multiple_results is True, instead,
        result_parsing_function is expected to return multiple lists of outputs,
        as described by the labels in columns, for each result. In this case,
        each result in the database will yield a number of rows in the output
        dataframe that is equal to the length of the result_parsing_function
        output computed on that result.

        Args:
            result_parsing_function (function): user-defined function, taking a
                result dictionary as input and returning a list of outputs or a list
                of lists of outputs.
        """

        results_list = []
        if params is not None:
            for param_combination in list_param_combinations(params):
                if runs is not None:
                    results_list += list(self.db.get_results(param_combination))[:runs]
                else:
                    results_list += list(self.db.get_results(param_combination))
        else:
            results_list = list(self.db.get_results())

        if result_parsing_function.__dict__.get('files_to_load', None) is not None:
            files_to_load = result_parsing_function.__dict__['files_to_load']
        else:
            files_to_load = r".*"

        if result_parsing_function.__dict__.get('yields_multiple_results', None) is not None:
            function_yields_multiple_results = True
        else:
            function_yields_multiple_results = False

        if columns is None and result_parsing_function.__dict__.get('output_labels', None) is None:
            raise ValueError("Please either specify a column parameter or decorate your function with the @sem.utils.output_labels decorator")
        elif columns is None:
            columns = result_parsing_function.__dict__['output_labels']

        data = []

        if parallel_parsing:
            with Pool(processes=self.runner.max_parallel_processes) as pool:
                for parsed_result in tqdm(pool.imap_unordered(parse_result,
                                                              [[self.db.get_complete_results(result_id=result['meta']['id'],
                                                                                             files_to_load=files_to_load)[0],
                                                                function_yields_multiple_results,
                                                                result_parsing_function,
                                                                param_columns] for result in results_list]),
                                          total=len(results_list),
                                          unit='result',
                                          desc='Parsing Results',
                                          disable=not verbose):
                    data += parsed_result
        else:
            for parsed_result in tqdm((parse_result([self.db.get_complete_results(result_id=result['meta']['id'],
                                                                                  files_to_load=files_to_load)[0],
                                                     function_yields_multiple_results,
                                                     result_parsing_function,
                                                     param_columns]) for result in results_list),
                                      total=len(results_list),
                                      unit='result',
                                      desc='Parsing Results',
                                      disable=not verbose):
                data += parsed_result

        if param_columns == 'all':
            param_columns = list(self.db.get_results()[0]['params'].keys())
        all_columns = ([k for k in list(self.db.get_results()[0]['params'].keys()) if k in param_columns] + columns)

        df = pd.DataFrame(data, columns=all_columns)

        if drop_constant_columns:
            nunique = df.apply(pd.Series.nunique)
            cols_to_drop = nunique[nunique == 1].index
            df = df.drop(cols_to_drop, axis=1)
            return df
        else:
            return df

    def get_results_as_numpy_array(self, parameter_space,
                                   result_parsing_function, runs=None,
                                   extract_complete_results=True):
        """
        Return the results relative to the desired parameter space in the form
        of a numpy array.

        Args:
            parameter_space (dict): dictionary containing
                parameter/list-of-values pairs.
            result_parsing_function (function): user-defined function, taking a
                result dictionary as argument, that can be used to parse the
                result files and return a list of values.
            runs (int): number of runs to gather for each parameter
                combination.
        """
        data = self.get_space(
            self.db.get_results(), {},
            collections.OrderedDict([(k, v) for k, v in
                                     parameter_space.items()]),
            result_parsing_function, runs, extract_complete_results)
        return np.array(data)

    def save_to_mat_file(self, parameter_space,
                         result_parsing_function,
                         filename, runs):
        """
        Return the results relative to the desired parameter space in the form
        of a .mat file.

        Args:
            parameter_space (dict): dictionary containing
                parameter/list-of-values pairs.
            result_parsing_function (function): user-defined function, taking a
                result dictionary as argument, that can be used to parse the
                result files and return a list of values.
            filename (path): name of output .mat file.
            runs (int): number of runs to gather for each parameter
                combination.
        """

        # Make sure all values are lists
        for key in parameter_space:
            if not isinstance(parameter_space[key], list):
                parameter_space[key] = [parameter_space[key]]

        # Add a dimension label for each non-singular dimension
        dimension_labels = [{key: np.array(parameter_space[key],
                                           dtype=object)} for key in
                            parameter_space.keys() if len(parameter_space[key])
                            > 0] + [{'runs': range(runs)}]

        # Create a list of the parameter names

        return savemat(
            filename,
            {'results':
             self.get_results_as_numpy_array(parameter_space,
                                             result_parsing_function,
                                             runs=runs).astype(object),
             'dimension_labels': dimension_labels})

    def save_to_npy_file(self, parameter_space,
                         result_parsing_function,
                         filename, runs):
        """
        Save results to a numpy array file format.
        """
        np.save(filename, self.get_results_as_numpy_array(
            parameter_space, result_parsing_function, runs=runs))

    def save_to_folders(self, parameter_space, folder_name, runs):
        """
        Save results to a folder structure.
        """
        self.space_to_folders(self.db.get_results(), {}, parameter_space, runs,
                              folder_name)

    def space_to_folders(self, current_result_list, current_query, param_space,
                         runs, current_directory):
        """
        Convert a parameter space specification to a directory tree with a
        nested structure.
        """
        # Base case: we iterate over the runs and copy files in the final
        # directory.
        if not param_space:
            for run, r in enumerate(current_result_list[:runs]):
                files = self.db.get_result_files(r)
                new_dir = os.path.join(current_directory, "run=%s" % run)
                os.makedirs(new_dir, exist_ok=True)
                for filename, filepath in files.items():
                    shutil.copyfile(filepath, os.path.join(new_dir, filename))
            return

        [key, value] = list(param_space.items())[0]
        # Iterate over dictionary values
        for v in value:
            next_query = deepcopy(current_query)
            temp_query = deepcopy(current_query)

            # For each list, recur 'fixing' that dimension.
            next_query[key] = v  # Update query

            # Create folder
            folder_name = ("%s=%s" % (key, v)).replace('/', '_')
            new_dir = os.path.join(current_directory, folder_name)
            os.makedirs(new_dir, exist_ok=True)

            next_param_space = deepcopy(param_space)
            del(next_param_space[key])

            temp_query[key] = v
            temp_result_list = [r for r in current_result_list if
                                self.satisfies_query(r, temp_query)]

            self.space_to_folders(temp_result_list, next_query,
                                  next_param_space, runs, new_dir)

    def get_results_as_xarray(self, parameter_space,
                              result_parsing_function,
                              output_labels, runs=None,
                              extract_complete_results=True):
        """
        Return the results relative to the desired parameter space in the form
        of an xarray data structure.

        Args:
            parameter_space (dict): The space of parameters to export.
            result_parsing_function (function): user-defined function, taking a
                result dictionary as argument, that can be used to parse the
                result files and return a list of values.
            output_labels (list): a list of labels to apply to the results
                dimensions, output by the result_parsing_function.
            runs (int): the number of runs to export for each parameter
                combination.
        """
        # Create a parameter space only containing the variable parameters
        clean_parameter_space = collections.OrderedDict(
            [(k, v) if isinstance(v, list) else (k, [v]) for k, v in parameter_space.items()])

        clean_parameter_space['runs'] = range(runs)

        if isinstance(output_labels, list):
            clean_parameter_space['metrics'] = output_labels

        data = self.get_space(
            self.db.get_results(), {},
            collections.OrderedDict([(k, v) for k, v in
                                     parameter_space.items()]),
            result_parsing_function, runs)
        xr_array = xr.DataArray(data, coords=clean_parameter_space,
                                dims=list(clean_parameter_space.keys()))

        return xr_array

    def files_in_dictionary(result):
        """
        Parsing function that returns a dictionary containing one entry for
        each file. Typically used to perform parsing externally.
        """
        return result['output']

    def get_space(self, current_result_list, current_query, param_space,
                  result_parsing_function,
                  runs=None,
                  extract_complete_results=True):
        """
        Convert a parameter space specification to a nested array structure
        representing the space. In other words, if the parameter space is::

            param_space = {
                'a': [1, 2],
                'b': [3, 4]
            }

        the function will return a structure like the following::

            [
                [
                    {'a': 1, 'b': 3},
                    {'a': 1, 'b': 4}
                ],
                [
                    {'a': 2, 'b': 3},
                    {'a': 2, 'b': 4}
                ]
            ]

        where the first dimension represents a, and the second dimension
        represents b. This nested-array structure can then be easily converted
        to a numpy array via np.array().

        Args:
            current_query (dict): the query to apply to the structure.
            param_space (dict): representation of the parameter space.
            result_parsing_function (function): user-defined function to call
                on results, typically used to parse data and outputting
                metrics.
            runs (int): the number of runs to query for each parameter
                combination.
        """
        if result_parsing_function is None:
            result_parsing_function = CampaignManager.files_in_dictionary
            # Note that this function operates recursively.

        # Base case
        if not param_space:
            results = [r for r in current_result_list if
                       self.satisfies_query(r, current_query)]
            parsed = []
            for r in results[:runs]:

                # Make results complete, by reading the output from file
                # TODO Extract this into a function
                r['output'] = {}
                available_files = self.db.get_result_files(r['meta']['id'])
                for name, filepath in available_files.items():
                    if extract_complete_results:
                        with open(filepath, 'r') as file_contents:
                            r['output'][name] = file_contents.read()
                    else:
                        r['output'][name] = filepath
                parsed.append(result_parsing_function(r))
                del r
            del results

            return parsed

        space = []
        [key, value] = list(param_space.items())[0]
        if not isinstance(value, list):
            value = [value]
        # Iterate over dictionary values
        for v in value:
            next_query = deepcopy(current_query)
            temp_query = deepcopy(current_query)
            # For each list, recur 'fixing' that dimension.
            next_query[key] = v
            next_param_space = deepcopy(param_space)
            del(next_param_space[key])
            temp_query[key] = v
            temp_result_list = [r for r in current_result_list if
                                self.satisfies_query(r, temp_query)]
            space.append(self.get_space(temp_result_list, next_query,
                                        next_param_space,
                                        result_parsing_function, runs,
                                        extract_complete_results))
        return space

    def satisfies_query(self, result, query):
        for current_param, current_value in query.items():
            if result['params'][current_param] != current_value:
                return False
        return True

    #############
    # Utilities #
    #############

    def __str__(self):
        """
        Return a human-readable representation of the campaign.
        """
        if self.runner:
            # if the campaign has a runner, print the db and the type of runner
            return "--- Campaign info ---\n%s\nRunner type: %s\n-----------" %\
                (self.db, type(self.runner))
        else:
            # the campaign has no runner, print only the db
            return "--- Campaign info ---\n%s\n-----------" % self.db

    def check_repo_ok(self):
        """
        Make sure that the ns-3 repository's HEAD commit is the same as the one
        saved in the campaign database, and that the ns-3 repository is clean
        (i.e., no untracked or modified files exist).
        """
        from git import Repo, exc
        # Check that git is at the expected commit and that the repo is not
        # dirty
        if self.runner is not None:
            path = self.runner.path
            try:
                repo = Repo(path)
            except(exc.InvalidGitRepositoryError):
                raise Exception("No git repository detected.\nIn order to "
                                "use SEM and its reproducibility enforcing "
                                "features, please create a git repository at "
                                "the root of your ns-3 project.")
            current_commit = repo.head.commit.hexsha
            campaign_commit = self.db.get_commit()

            if repo.is_dirty(untracked_files=True):
                raise Exception("ns-3 repository is not clean")

            if current_commit != campaign_commit:
                raise Exception("ns-3 repository is on a different commit "
                                "from the one specified in the campaign")
