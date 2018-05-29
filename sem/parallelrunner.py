from .runner import SimulationRunner
import subprocess

class ParallelRunner(SimulationRunner):
    """
    A Runner which can perform simulations in parallel on the current machine.
    """
    def run_simulations(self, parameter_list, verbose=False):
        """
        This function runs multiple simulations in parallel.
        """

        procs = list()

        # Launch processes
        for idx, parameter in enumerate(parameter_list):
            result = {}
            result.update(parameter)

            command = ' '.join(['--%s=%s' % (param, value) for param, value in
                                parameter.items()])
            command = '%s %s' % (self.script, command)
            proc = subprocess.Popen(['./waf', '--run', command],
                                    cwd=self.path, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

            procs.append((proc, result))

        while True:
            if len(procs) == 0:
                break
            for proc in procs:
                if (proc[0].poll() is not None):  # Process finished
                    proc[1]['stdout'] = proc[0].communicate()[0].decode('utf-8')
                    procs.remove(proc)
                    yield proc[1]
