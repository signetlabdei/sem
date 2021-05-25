from .runner import SimulationRunner
from multiprocessing import Pool, Queue, Lock, Array, cpu_count
import queue
import copy
import numpy as np
from copy import deepcopy
import itertools
from tqdm import tqdm


class ConditionalRunner(SimulationRunner):
    # TODO Update documentation
    """
    A Runner which can perform simulations in parallel on the current machine,
    prioritizing longest tasks as to minimize the makespan time.

    Due to inheritance and code cleanliness reasons, as of now this runner does
    not query the database to get running statistics from previous runs, and
    only creates its statistics as it performs simulations.
    """

    def __init__(self, path, script, optimized, skip_configuration=False, max_parallel_processes=None):
        SimulationRunner.__init__(self, path, script, optimized,
                                  skip_configuration, max_parallel_processes)
        self.parameter_runtime_map = {}

    def run_simulations(self, parameter_list, data_folder, stop_on_errors=True):
        """
        This function runs multiple simulations in parallel.

        Args:
            parameter_list (list): list of parameter combinations to simulate.
            data_folder (str): folder in which to create output folders.
        """

        # print("Running simulations...")

        self.data_folder = data_folder

        # Create a copy of the parameter list
        unique_param_list = copy.deepcopy(parameter_list)
        param_list_with_check = [
            list(i) for i in zip(unique_param_list,
                                 [False for _ in unique_param_list])]

        def process(q, iolock, outq):
            while True:
                next_sim = q.get()
                if next_sim is None:
                    break
                # with iolock:
                    # print("processing", next_sim)
                result = next(
                    SimulationRunner.run_simulations(self,
                                                     [next_sim],
                                                     self.data_folder,
                                                     stop_on_errors=False))
                outq.put(result)

        # Create queue and processing pool
        q = Queue(1)
        outq = Queue()
        iolock = Lock()
        pool = Pool(self.max_parallel_processes,
                    initializer=process,
                    initargs=(q, iolock, outq))

        progress = tqdm(total=len(param_list_with_check),
                        unit='parameter combination',
                        desc='Running Simulations')

        # This generates the tasks and adds them to the queue
        while True:
            # print("Checking for new results")
            while True:
                try:
                    yield outq.get_nowait()
                except queue.Empty:
                    break

            # Update which simulations converged
            for idx, item in enumerate(param_list_with_check):
                if not item[1]:
                    param_list_with_check[idx][1] = self.stopping_function(item[0])

            # print("Converged: %s" % sum(list(zip(*param_list_with_check))[1]))
            progress.n = sum(list(zip(*param_list_with_check))[1]) - 1
            progress.update()

            if all(list(zip(*param_list_with_check))[1]):
                break
            else:
                # Push simulations that still haven't converged in the queue
                new_simulations = [copy.deepcopy(p)
                                   for p, converged in param_list_with_check
                                   if not converged]
                # Assign an RngRun value to all the simulations we need to
                # run.
                for s in new_simulations:
                    s['RngRun'] = next(self.next_runs)
                for p in new_simulations:
                    q.put(p, block=True)

        progress.close()

        # This closes everything
        for _ in range(pool._processes):
            q.put(None, True)
        pool.close()
        pool.join()

        while True:
            try:
                yield outq.get_nowait()
            except queue.Empty:
                return
