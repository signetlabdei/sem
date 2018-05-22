from .database import DatabaseManager
from .runner import SimulationRunner


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
    def new(cls, path, script, filename):
        """
        Initialize a campaign database based on a script and ns-3 path.
        """
        # Create a runner for the desired configuration
        runner = SimulationRunner(path, script)

        # Get list of available parameters
        params = runner.get_available_parameters()

        # Create a database manager from configuration
        config = {
            'script': script,
            'path': path,
            'params': params
        }

        db = DatabaseManager.new(config, filename)

        return cls(db, runner)

    @classmethod
    def load(cls, filename):
        """
        Read a filename and load the corresponding campaign database.
        """
        # Read from database
        db = DatabaseManager.load(filename)

        # Create a runner
        runner = SimulationRunner(db.get_path(), db.get_script())

        return cls(db, runner)


    ######################
    # Simulation running #
    ######################

    def run_simulations(self, parameter_space):
        """
        Run the missing simulations from a dictionary containing parameter -
        array of values pairs, defining the parameter space to explore.
        """
        # Offload simulation execution to self.runner

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
