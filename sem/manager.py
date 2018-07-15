from .database import DatabaseManager
from .runner import SimulationRunner
from .parallelrunner import ParallelRunner
from .utils import DRMAA_AVAILABLE, list_param_combinations
from git import Repo, exc
from copy import deepcopy
from tqdm import tqdm
from random import shuffle
import numpy as np
import xarray as xr
import os
from pathlib import Path
if DRMAA_AVAILABLE:
    from .gridrunner import GridRunner


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

    def __init__(self, campaign_db, campaign_runner):
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

    @classmethod
    def new(cls, ns_path, script, campaign_dir, runner_type='ParallelRunner',
            overwrite=False, optimized=True):
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
                a DRMAA-compatible parallel task scheduler)
            overwrite (bool): whether to overwrite already existing
                campaign_dir folders
            optimized (bool): whether to configure the runner to employ an
                optimized ns-3 build.
        """
        # Convert paths to be absolute
        ns_path = os.path.abspath(ns_path)
        campaign_dir = os.path.abspath(campaign_dir)

        # Verify if the specified campaign is already available
        if Path(campaign_dir).exists() and not overwrite:
            try:
                manager = CampaignManager.load(campaign_dir, ns_path,
                                               runner_type=runner_type,
                                               optimized=optimized)

                if manager.db.get_script() == script:
                    return manager
                else:
                    del manager

            except ValueError:
                pass  # Go on with the database creation

        # Initialize runner
        runner = CampaignManager.create_runner(ns_path, script,
                                               runner_type=runner_type,
                                               optimized=optimized)

        # Get list of parameters to save in the DB
        params = runner.get_available_parameters()

        # Get current commit
        commit = Repo(ns_path).head.commit.hexsha

        # Create a database manager from the configuration
        db = DatabaseManager.new(script=script,
                                 params=params,
                                 commit=commit,
                                 campaign_dir=campaign_dir,
                                 overwrite=overwrite)

        return cls(db, runner)

    @classmethod
    def load(cls, campaign_dir, ns_path=None, runner_type='ParallelRunner',
             optimized=True):
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
                a DRMAA-compatible parallel task scheduler)
            optimized (bool): whether to configure the runner to employ an
                optimized ns-3 build.
        """
        # Read the existing configuration into the new DatabaseManager
        db = DatabaseManager.load(campaign_dir)
        script = db.get_script()

        runner = None
        if ns_path is not None:
            runner = CampaignManager.create_runner(ns_path, script,
                                                   runner_type, optimized)

        return cls(db, runner)

    def create_runner(ns_path, script, runner_type='ParallelRunner',
                      optimized=True):
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
                a DRMAA-compatible parallel task scheduler)
            optimized (bool): whether to configure the runner to employ an
                optimized ns-3 build.
        """
        # locals() contains a dictionary pairing class names with class
        # objects: we can create the object using the desired class starting
        # from its name.
        return locals().get(runner_type,
                            globals().get(runner_type))(
                                ns_path, script, optimized=optimized)

    ######################
    # Simulation running #
    ######################

    def run_simulations(self, param_list, show_progress=True):
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

        # Check that the current repo commit corresponds to the one specified
        # in the campaign
        self.check_repo_ok()

        # Build ns-3 before running any simulations
        # At this point, we can assume the project was already configured
        self.runner.configure_and_build(skip_configuration=True)

        # Compute next RngRun values for the simulations we need to perform
        next_runs = self.db.get_next_rngruns(len(param_list))
        for r, param in zip(next_runs, param_list):
            param['RngRun'] = r

        # Shuffle simulations
        # This mixes up long and short simulations, and gives better time
        # estimates.
        shuffle(param_list)

        # Offload simulation execution to self.runner
        # Note that this only creates a generator for the results, no
        # computation is performed on this line.
        results = self.runner.run_simulations(param_list,
                                              self.db.get_data_dir())

        # Wrap the result generator in the progress bar generator.
        if show_progress:
            result_generator = tqdm(results, total=len(param_list),
                                    unit='simulation',
                                    desc='Running simulations')
        else:
            result_generator = results

        # Insert result object in db. Using the generator here ensures we
        # save results as they are finalized by the SimulationRunner, and
        # that they are kept even if execution is terminated abruptly by
        # crashes or by a KeyboardInterrupt.
        for result in result_generator:
            self.db.insert_result(result)

    def get_missing_simulations(self, param_list, runs):
        """
        Return a list of the simulations among the required ones that are not
        available in the database.

        Args:
            param_list (list): a list of dictionaries containing all the
                parameters combinations.
            runs (int): an integer representing how many repetitions are wanted
                for each parameter combination.
        """

        params_to_simulate = []

        for param_comb in param_list:
            available_sims = self.db.get_results(param_comb)
            needed_runs = runs - len(available_sims)
            # Here it's important that we make copies of the dictionaries, so
            # that if we modify one we don't modify the others. This is
            # necessary because after this step, typically, we will add the
            # RngRun key which must be different for each copy.
            params_to_simulate += [deepcopy(param_comb) for i in
                                   range(needed_runs)]

        return params_to_simulate

    def run_missing_simulations(self, param_list, runs):
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
            runs (int): the number of runs to perform for each simulation.
        """
        if isinstance(param_list, dict):
            param_list = list_param_combinations(param_list)

        self.run_simulations(
            self.get_missing_simulations(param_list, runs))

    #####################
    # Result management #
    #####################

    def get_results_as_numpy_array(self, parameter_space,
                                   result_parsing_function):
        """
        Return the results relative to the desired parameter space in the form
        of a numpy array.

        Note that the input parameter space can contain lists of any length,
        but any single-element list will have the corresponding dimension
        collapsed via the numpy.squeeze function.

        Args:
            parameter_space (dict): dictionary containing
                parameter/list-of-values pairs.
            result_parsing_function (function): user-defined function, taking a
                result dictionary as argument, that can be used to parse the
                result files and return a list of values.
        """
        return np.squeeze(np.array(self.get_space({},
                                                  parameter_space,
                                                  result_parsing_function)))

    def get_results_as_xarray(self, parameter_space,
                              result_parsing_function,
                              output_labels, runs):
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
        np_array = np.squeeze(np.array(self.get_space({}, parameter_space,
                                                      result_parsing_function,
                                                      runs)))

        # Create a parameter space only containing the variable parameters
        clean_parameter_space = {}
        for key, value in parameter_space.items():
            if isinstance(value, list) and len(value) > 1:
                clean_parameter_space[key] = value

        clean_parameter_space['runs'] = range(runs)

        if isinstance(output_labels, list):
            clean_parameter_space['metrics'] = output_labels

        xr_array = xr.DataArray(np_array, coords=clean_parameter_space,
                                dims=list(clean_parameter_space.keys()))

        return xr_array

    def get_space(self, current_query, param_space, result_parsing_function,
                  runs):
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
        # Note that this function operates recursively.

        # Base case
        if not param_space:
            results = self.db.get_complete_results(current_query)
            parsed = []
            for r in results[:runs]:
                parsed.append(result_parsing_function(r))

            return parsed

        space = []
        [key, value] = list(param_space.items())[0]
        # Iterate over dictionary values
        for v in value:
            next_query = deepcopy(current_query)
            # For each list, recur 'fixing' that dimension.
            next_query[key] = v
            next_param_space = deepcopy(param_space)
            del(next_param_space[key])
            space.append(self.get_space(next_query, next_param_space,
                                        result_parsing_function, runs))
        return space

    #############
    # Utilities #
    #############

    def __str__(self):
        """
        Return a human-readable representation of the campaign.
        """
        return "--- Campaign info ---\n%s\n------------" % self.db

    def check_repo_ok(self):
        """
        Make sure that the ns-3 repository's HEAD commit is the same as the one
        saved in the campaign database, and that the ns-3 repository is clean
        (i.e., no untracked or modified files exist).
        """
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
