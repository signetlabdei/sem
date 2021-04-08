from .runner import SimulationRunner
from multiprocessing import Pool, Queue, Lock, Array, cpu_count
import queue
import numpy as np
from copy import deepcopy
import itertools


def have_same_combination(dict1, dict2):
    return len(set({i:v for i, v in dict1.items() if i!='RngRun'}.items()) ^
               set({i:v for i, v in dict2.items() if i!='RngRun'}.items())) == 0


class LptRunner(SimulationRunner):
    """
    A Runner which can perform simulations in parallel on the current machine,
    prioritizing longest tasks as to minimize the makespan time.

    Due to inheritance and code cleanliness reasons, as of now this runner does
    not query the database to get running statistics from previous runs, and
    only creates its statistics as it performs simulations.
    """

    def __init__(self, path, script, optimized, max_parallel_processes=None):
        SimulationRunner.__init__(self, path, script, optimized, max_parallel_processes)
        self.parameter_runtime_map = {}

    def run_simulations(self, parameter_list, data_folder):
        """
        This function runs multiple simulations in parallel.

        Args:
            parameter_list (list): list of parameter combinations to simulate.
            data_folder (str): folder in which to create output folders.
        """
        self.data_folder = data_folder

        # Group together parameter combinations that only differ for their RngRun
        unique_combos = []
        times = []

        # If the parameters don't have timing info, we make it so they have it
        # with an estimate of +Inf
        if not isinstance(parameter_list[0], list):
            parameter_list = [[p, float("Inf")] for p in parameter_list]

        for param1, timing_info in parameter_list:
            matched = False
            for idx, param2 in enumerate(unique_combos):
                same = have_same_combination(param1, param2[0])
                if same:
                    matched = True
                    unique_combos[idx] += [param1]
            if not matched:
                times.append(timing_info)
                unique_combos.append([param1])

        times = Array('f', times)

        def process(q, iolock, outq, times):
            while True:
                next_sim, index = q.get()
                if next_sim is None:
                    break
                # with iolock:
                    # print("processing", next_sim)
                result = next(SimulationRunner.run_simulations(self, [next_sim],
                                                               self.data_folder))
                times[index] = float(result['meta']['elapsed_time'])

                # with iolock:
                    # print("completed in ", result['meta']['elapsed_time'])

                outq.put(result)

        # Create queue and processing pool
        q = Queue(1)
        outq = Queue()
        iolock = Lock()
        pool = Pool(self.max_parallel_processes, initializer=process,
                    initargs=(q, iolock, outq, times))

        param_list = deepcopy(unique_combos)

        # This generates the tasks and adds them to the queue
        while True:
            # print("Checking for new results")
            while True:
                try:
                    yield outq.get_nowait()
                except queue.Empty:
                    break

            # print("Param list from main: %s" % param_list)
            available_times = [t if param_list[idx] else -1 for idx, t in
                               enumerate(times)]
            maximums = (np.squeeze((np.argwhere(available_times ==
                                              np.amax(available_times))))).tolist()
            # print("Times: %s" % [i for i in times])
            # print("Maximums: %s" % maximums)

            if isinstance(maximums, list):
                argmax = np.random.choice([i for i in maximums])
                # print("Times: %s" % [i for i in times])
                # print("Argmax: %s" % argmax)
                # print("Chosen parameter: %s" % param_list[argmax])
                if param_list[argmax]:
                    q.put((param_list[argmax].pop(), argmax))
            else:
                argmax = maximums
                # print("Times: %s" % [i for i in times])
                # print("Argmax: %s" % argmax)
                # print("Chosen parameter: %s" % param_list[argmax])
                if param_list[argmax]:
                    q.put((param_list[argmax].pop(), argmax))
            if all([p == [] for p in param_list]):
                break

        # print("Out of the main thread")

        # This closes everything
        for _ in range(pool._processes):
            q.put((None, 0), True)
        pool.close()
        pool.join()

        while True:
            try:
                yield outq.get_nowait()
            except queue.Empty:
                return
