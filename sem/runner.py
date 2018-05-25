import subprocess
import re
import sys


class SimulationRunner(object):
    """
    The class tasked with running simulations.
    """

    ##################
    # Initialization #
    ##################

    def __init__(self, path, script):
        """
        Initialization function.
        """

        # Check whether path points to a valid installation
        if subprocess.run(
                "./waf", cwd=path, stdout=subprocess.PIPE).returncode != 0:
            raise ValueError(
                "Path does not point to a valid ns-3 installation")

        # Check script is available
        if script not in str(subprocess.run(["./waf", 'list'], cwd=path,
                                            stdout=subprocess.PIPE).stdout):
            raise ValueError(
                "Script is not a valid ns-3 program name")

        self.path = path
        self.script = script

    #############
    # Utilities #
    #############

    def get_available_parameters(self):
        """
        Return a list of the parameters made available by the script.
        """
        result = subprocess.check_output(['./waf', '--run', '%s --PrintHelp' %
                                          self.script], cwd=self.path).decode(
                                             'utf-8')
        options = re.findall('.*Program\sOptions:(.*)General\sArguments.*',
                             result, re.DOTALL)
        if len(options):
            args = re.findall('.*--(.*?):.*', options[0], re.MULTILINE)
            return args
        else:
            return []

    ######################
    # Simulation running #
    ######################

    def run_single_simulation(self, parameters):
        """
        Run a simulation using a certain combination of parameters.
        """
        command = ' '.join(['--%s=%s' % (param, value) for param, value in parameters.items()])
        command = '%s %s' % (self.script, command)

        print(command)
        print(self.path)

        return subprocess.run(['./waf', '--run', command], cwd=self.path,
                              stdout=subprocess.PIPE).stdout

    def run_missing_simulations(self, parameter_space):
        """
        Run the simulations belonging to the parameter_space that are still
        missing from the database.
        """
