from .database import DatabaseManager
from .runner import SimulationRunner
from .parallelrunner import ParallelRunner
from git import Repo
from copy import deepcopy


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
    def new(cls, path, script, filename, runner='SimulationRunner'):
        """
        Initialize a campaign database based on a script and ns-3 path.

        runner can be either SimulationRunner (default) or ParallelRunner
        """
        # Create a runner for the desired configuration
        if runner == 'SimulationRunner':
            runner = SimulationRunner(path, script)
        elif runner == 'ParallelRunner':
            runner = ParallelRunner(path, script)
        else:
            raise ValueError('Unknown runner')

        # Get list of available parameters
        params = runner.get_available_parameters()

        # Repository check
        # TODO Make sure there are no staged/unstaged changes
        # Get current commit
        commit = Repo(path).head.commit.hexsha

        # Create a database manager from configuration
        config = {
            'script': script,
            'path': path,
            'params': params,
            'commit': commit
        }

        db = DatabaseManager.new(config, filename)

        return cls(db, runner)

    @classmethod
    def load(cls, filename, runner='SimulationRunner'):
        """
        Read a filename and load the corresponding campaign database.
        """
        # Read from database
        db = DatabaseManager.load(filename)

        # Create a runner
        runner = ParallelRunner(db.get_path(), db.get_script())

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
        # Compute next RngRun value
        next_run = self.db.get_next_rngrun()
        for idx, param in enumerate(param_list):
            param['RngRun'] = next_run + idx

        # Offload simulation execution to self.runner
        results = self.runner.run_simulations(param_list, verbose)

        for result in results:
            self.db.insert_result(result)

    def get_missing_simulations(self, param_list, runs):
        """
        Return a list of the simulations among the required ones that are not
        available in the database.

        param_list is a list of dictionaries containing all the parameters,
        runs is an integer representing how many repetitions we need for each
        parameter combination.
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
        in the database. Make sure that we have at least runs replications for
        each parameter combination.
        """
        self.run_simulations(self.get_missing_simulations(param_list, runs))

    #####################
    # Result management #
    #####################

    def get_results_as_numpy_array(self, parameter_space):
        """
        Return the results relative to the desired parameter space in the form
        of a numpy array.
        """
        # Collect list of relevant results from DatabaseManager
        # Package results in a numpy array

    #############
    # Utilities #
    #############

    def __str__(self):
        return "--- Campaign info ---\n%s\n------------" % self.db
