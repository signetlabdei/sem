from os import environ
from .runner import SimulationRunner
from multiprocessing import Pool

MAX_PARALLEL_PROCESSES = None  # If None, the number of CPUs is used


class ParallelRunner(SimulationRunner):

    """
    A Runner which can perform simulations in parallel on the current machine.
    """
    def run_simulations(self, parameter_list, data_folder, environment=None):
        """
        This function runs multiple simulations in parallel.

        Args:
            parameter_list (list): list of parameter combinations to simulate.
            data_folder (str): folder in which to create output folders.
        """
        ps = [tuple((x,environment)) for x in parameter_list]
        # print(ps)
        
        self.data_folder = data_folder
        with Pool(processes=MAX_PARALLEL_PROCESSES) as pool:
            for result in pool.imap_unordered(self.launch_simulation,
                                              ps):
                yield result

    def launch_simulation(self, parameter_and_environment):
        """
        Launch a single simulation, using SimulationRunner's facilities.

        This function is used by ParallelRunner's run_simulations to map
        simulation running over the parameter list.

        Args:
            parameter (dict): the parameter combination to simulate.
        """
        # print('DC')
        # print(parameter_and_environment_zipped[0])
        # print(parameter_and_environment_zipped[1])

        # print("Environment2:")
        # print(environment)
        # print("Parameter")
        # print(parameter)
        # print()
        return next(SimulationRunner.run_simulations(self, [parameter_and_environment[0]],
                                                     self.data_folder,parameter_and_environment[1]))
