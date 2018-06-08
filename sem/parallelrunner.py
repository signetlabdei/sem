from .runner import SimulationRunner
from multiprocessing import Pool


class ParallelRunner(SimulationRunner):
    """
    A Runner which can perform simulations in parallel on the current machine.
    """
    def run_simulations(self, parameter_list, temp_folder, verbose=False):
        """
        This function runs multiple simulations in parallel.
        """
        self.temp_folder = temp_folder
        with Pool() as pool:
            for result in pool.imap_unordered(self.launch_simulation,
                                              parameter_list):
                yield result

    def launch_simulation(self, parameter):
        return next(SimulationRunner.run_simulations(self, [parameter],
                                                     self.temp_folder,
                                                     verbose=False))
