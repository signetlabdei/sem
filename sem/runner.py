class SimulationRunner(object):
    """
    The class tasked with running simulations.
    """

    ##################
    # Initialization #
    ##################

    def __init__(self, db):
        """
        Initialization, using a DatabaseManager.
        """
        self.db = db

    ######################
    # Simulation running #
    ######################

    def run_single_simulation(self, parameters):
        """
        Run a simulation using a certain combination of parameters.
        """

    def run_missing_simulations(self, parameter_space):
        """
        Run the simulations belonging to the parameter_space that are still
        missing from the database.
        """
