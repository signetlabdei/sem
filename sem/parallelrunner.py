from .runner import SimulationRunner
from multiprocessing import Pool


class ParallelRunner(SimulationRunner):

    """
    A Runner which can perform simulations in parallel on the current machine.
    """

    def run_simulations(self, parameter_list, data_folder, stop_on_errors=False):
        """
        This function runs multiple simulations in parallel.

        Args:
            parameter_list (list): list of parameter combinations to simulate.
            data_folder (str): folder in which to create output folders.
        """
        self.data_folder = data_folder
        self.stop_on_errors = stop_on_errors
        with Pool(processes=self.max_parallel_processes) as pool:
            for result in pool.imap_unordered(self.launch_simulation,
                                              parameter_list):
                yield result

    def launch_simulation(self, parameter):
        """
        Launch a single simulation, using SimulationRunner's facilities.

        This function is used by ParallelRunner's run_simulations to map
        simulation running over the parameter list.

        Args:
            parameter (dict): the parameter combination to simulate.
        """
        return next(SimulationRunner.run_simulations(self, [parameter],
                                                     self.data_folder,
                                                     stop_on_errors=self.stop_on_errors))
