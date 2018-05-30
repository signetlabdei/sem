import subprocess
import re
import sys
import glob
import os
from contextlib import redirect_stdout


class SimulationRunner(object):
    """
    The class tasked with running simulations and interfacing with the ns-3
    system.
    """

    ##################
    # Initialization #
    ##################

    def __init__(self, path, script):
        """
        Initialization function.
        """

        # Update path with the provided information
        sys.path += [path, glob.glob(path + '/.waf*')[0]]

        # Run waf (via its library)
        with redirect_stdout(open(os.devnull, "w")):
            os.chdir(path)
            from waflib import Scripting, Context
            Scripting.waf_entry_point(os.getcwd(), Context.WAFVERSION,
                                      glob.glob(path + '/.waf*')[0])

        # Get the program's executable filename, via the functions provided by
        # wutils.
        import wutils
        self.path = path
        self.script = script
        self.script_executable = wutils.get_run_program(script)[1][0]
        self.environment = wutils.get_proc_env()

    #############
    # Utilities #
    #############

    def configure_and_build(self, path, verbose=False):
        """
        Configure and build the ns-3 code.
        """

        # Check whether path points to a valid installation
        subprocess.run(['./waf', 'configure', '--enable-examples',
                        '--disable-gtk'], cwd=path, stdout=subprocess.PIPE if
                       not verbose else None, stderr=subprocess.PIPE if not
                       verbose else None)

        # Build ns-3
        subprocess.run(['./waf', 'build'], cwd=path, stdout=subprocess.PIPE if
                       not verbose else None, stderr=subprocess.PIPE if not
                       verbose else None)

    def get_available_parameters(self):
        """
        Return a list of the parameters made available by the script.
        """

        # At the moment, we rely on regex to extract the list of available
        # parameters. A tighter integration with waf would allow for a more
        # natural extraction of the information.

        result = subprocess.check_output([self.script_executable,
                                          '--PrintHelp'], env=self.environment,
                                         cwd=self.path).decode('utf-8')

        options = re.findall('.*Program\sArguments:(.*)General\sArguments.*',
                             result, re.DOTALL)

        if len(options):
            args = re.findall('.*--(.*?):.*', options[0], re.MULTILINE)
            return args
        else:
            return []

    ######################
    # Simulation running #
    ######################

    def run_simulations(self, parameter_list, verbose=False):
        """
        Run several simulations using a certain combination of parameters.

        Yields results once simulations are completed
        """

        for idx, parameter in enumerate(parameter_list):
            if verbose:
                print("\nSimulation %s/%s:\n%s" % (idx+1, len(parameter_list),
                                                   parameter))

            current_result = {}
            current_result.update(parameter)

            command = [self.script_executable] + ['--%s=%s' % (param, value)
                                                  for param, value in
                                                  parameter.items()]

            # TODO Run from dedicated temporary folder
            execution = subprocess.run(command, cwd=self.path,
                                       env=self.environment,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

            if execution.returncode > 0:
                print('Simulation exited with an error.'
                      '\nStderr: %s\nStdout: %s' % (execution.stderr,
                                                    execution.stdout))

            current_result['stdout'] = execution.stdout.decode('utf-8')

            yield current_result
