from .runner import SimulationRunner
from multiprocessing.pool import ThreadPool


class ParallelRunner(SimulationRunner):
    """
    A Runner which can perform simulations in parallel on the current machine.
    """
    def run_simulations(self, parameter_list, verbose=False):
        """
        This function runs multiple simulations in parallel.
        """
        with ThreadPool() as pool:
            for result in pool.map(self.launch_simulation, parameter_list):
                yield from result

    def launch_simulation(self, parameter):
        return list(SimulationRunner.run_simulations(self, [parameter],
                                                     verbose=False))
