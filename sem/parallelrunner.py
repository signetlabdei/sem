from .runner import SimulationRunner
from .utils import CallbackBase
from multiprocessing.pool import ThreadPool as Pool
# TODO if this is creating issues a more grain-fined solution may contemplate to check


class ParallelRunner(SimulationRunner):

    """
    A Runner which can perform simulations in parallel on the current machine.
    """
    data_folder: str = None
    stop_on_errors: bool = False
    callbacks: [CallbackBase] = []

    def run_simulations(self, parameter_list, data_folder, callbacks: [CallbackBase] = None, stop_on_errors=False):
        """
        This function runs multiple simulations in parallel.

        Args:
            parameter_list (list): list of parameter combinations to simulate.
            data_folder (str): folder in which to create output folders.
            callbacks (list): list of callbacks to be triggered
            stop_on_errors (bool): check whether simulation has to stop on errors or not
        """
        
        if callbacks is not None:
            for cb in callbacks:
                cb.on_simulation_start(len(list(enumerate(parameter_list))))
                cb.controlled_by_parent = True

        self.data_folder = data_folder
        self.stop_on_errors = stop_on_errors
        self.callbacks = callbacks
        with Pool(processes=self.max_parallel_processes) as pool:
            for result in pool.imap_unordered(self.launch_simulation,
                                              parameter_list):
                yield result

        if callbacks is not None:
            for cb in callbacks:
                cb.on_simulation_end()

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
                                                     callbacks=self.callbacks,
                                                     stop_on_errors=self.stop_on_errors))
