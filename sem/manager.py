from .database import DatabaseManager
from .runner import SimulationRunner
from .parallelrunner import ParallelRunner
from .utils import DRMAA_AVAILABLE
from git import Repo
from copy import deepcopy
from tqdm import tqdm
from random import shuffle
import numpy as np
import xarray as xr
from pathlib import Path

if DRMAA_AVAILABLE:
    from .gridrunner import GridRunner


class CampaignManager(object):
    """
    The main Simulation Execution Manager class can be used to load, save,
    execute and access the results of simulation campaigns.
    """

    #######################################
    # Campaign initialization and loading #
    #######################################

    def __init__(self, campaign_db, campaign_runner):
        """
        Initialize the Simulation Execution Manager.
        """
        self.db = campaign_db
        self.runner = campaign_runner

    @classmethod
    def new(cls, ns_path, script, campaign_dir, runner='SimulationRunner',
            overwrite=False):
        """
        Initialize a campaign database based on a script and ns-3 ns_path.

        If a database is already available at the ns_path described in the
        specified campaign_dir and its configuration matches config, this
        instance is used instead. If the overwrite argument is set to True
        instead, the specified directory is wiped and a new campaign is
        created in its place.

        runner can be either SimulationRunner (default) or ParallelRunner
        """
        # Verify if the specified campaign is already available
        if Path(campaign_dir).exists() and not overwrite:
            try:
                manager = CampaignManager.load(campaign_dir, runner=runner)
                same_path = manager.db.get_path() == ns_path
                same_script = manager.db.get_script() == script
                if same_path and same_script:
                    return manager
                else:
                    del manager
            except ValueError:
                # Go on with the database creation
                pass

        # Create a runner for the desired configuration
        if runner == 'SimulationRunner':
            runner = SimulationRunner(ns_path, script)
        elif runner == 'ParallelRunner':
            runner = ParallelRunner(ns_path, script)
        elif runner == 'GridRunner':
            runner = GridRunner(ns_path, script)
        else:
            raise ValueError('Unknown runner')

        # Get list of available parameters
        params = runner.get_available_parameters()

        # Get current commit
        commit = Repo(ns_path).head.commit.hexsha

        # Create a database manager from configuration
        config = {
            'script': script,
            'path': ns_path,
            'params': params,
            'commit': commit,
            'campaign_dir': campaign_dir,
        }

        db = DatabaseManager.new(**config, overwrite=overwrite)

        return cls(db, runner)

    @classmethod
    def load(cls, campaign_dir, runner='SimulationRunner'):
        # Read configuration into new DatabaseManager
        db = DatabaseManager.load(campaign_dir)
        ns_path = db.get_path()
        script = db.get_script()

        # Create a runner for the desired configuration
        if runner == 'SimulationRunner':
            runner = SimulationRunner(ns_path, script)
        elif runner == 'ParallelRunner':
            runner = ParallelRunner(ns_path, script)
        elif runner == 'GridRunner':
            runner = GridRunner(ns_path, script)
        else:
            raise ValueError('Unknown runner')

        return cls(db, runner)

    ######################
    # Simulation running #
    ######################

    def run_simulations(self, param_list, verbose=True):
        """
        Run several simulations specified by a list of parameters.

        This function does not verify whether we already have the required
        simulations in the database - it just runs all the parameter
        combinations that are specified in the list.
        """
        # Check that the current repo commit corresponds to the one specified
        # in the campaign
        self.check_repo_ok()

        # Configure and build ns-3 before running any simulations
        self.runner.configure_and_build(self.db.get_path())

        # Compute next RngRun value
        next_run = self.db.get_next_rngrun()
        for idx, param in enumerate(param_list):
            param['RngRun'] = next_run + idx

        # Shuffle simulations
        # This mixes up long and short simulations, and gives better time
        # estimates
        shuffle(param_list)

        # Offload simulation execution to self.runner
        # Note that this only creates a generator for the results, no
        # computation is performed on this line
        results = self.runner.run_simulations(param_list,
                                              self.db.get_data_dir())

        for result in tqdm(results, total=len(param_list), unit='simulation',
                           desc='Running simulations'):
            # Insert result object in db
            self.db.insert_result(result)

    def get_missing_simulations(self, param_list, runs):
        """
        Return a list of the simulations among the required ones that are not
        available in the database.

        Args:
            param_list (list): A list of dictionaries containing all the
                parameters combinations.
            runs (int): An integer representing how many repetitions are wanted
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

        This function makes sure that we have at least runs replications for
        each parameter combination.
        """
        self.run_simulations(self.get_missing_simulations(param_list, runs))

    #####################
    # Result management #
    #####################

    def get_results_as_numpy_array(self, parameter_space,
                                   result_parsing_function,
                                   run_averaging_function=None):
        """
        Return the results relative to the desired parameter space in the form
        of a numpy array.
        """
        return np.squeeze(np.array(self.get_space({}, parameter_space,
                                                  result_parsing_function,
                                                  run_averaging_function)))

    def get_results_as_xarray(self, parameter_space,
                              result_parsing_function,
                              output_labels, runs):
        """
        Return the results relative to the desired parameter space in the form
        of an xarray data structure.
        """
        np_array = np.squeeze(np.array(self.get_space({}, parameter_space,
                                                      result_parsing_function,
                                                      runs)))

        # Create a parameter space only containing the variable parameters
        clean_parameter_space = {}
        for key, value in parameter_space.items():
            if isinstance(value, list) and len(value) > 1:
                clean_parameter_space[key] = value

        if isinstance(output_labels, list):
            clean_parameter_space['metrics'] = output_labels

        clean_parameter_space['runs'] = range(runs)

        xr_array = xr.DataArray(np_array, coords=clean_parameter_space,
                                dims=list(clean_parameter_space.keys()))

        return xr_array

    def get_space(self, current_query, param_space, result_parsing_function,
                  runs):
        # print("Parameter space: %s" % param_space)
        # print("Current query: %s" % current_query)
        if not param_space:
            # print("Querying database with query:\n%s" % current_query)
            results = self.db.get_results(current_query)
            parsed = []
            for r in results[:runs]:
                parsed.append(result_parsing_function(r))

            return parsed

        space = []
        [key, value] = list(param_space.items())[0]
        for v in value:
            # print("Key: %s, Value: %s" % (key, v))
            next_query = deepcopy(current_query)
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
        return "--- Campaign info ---\n%s\n------------" % self.db

    def check_repo_ok(self):
        # Check that git is at the expected commit and that the repo is not
        # dirty
        path = self.db.get_path()
        repo = Repo(path)
        current_commit = repo.head.commit.hexsha
        campaign_commit = self.db.get_commit()

        if repo.is_dirty(untracked_files=True):
            raise Exception("ns-3 repository is not clean")

        if current_commit != campaign_commit:
            raise Exception("ns-3 repository is on a different commit from the"
                            "one specified in the campaign")
