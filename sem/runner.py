import subprocess
import re
import os
import uuid
import time
from tqdm import tqdm
import importlib


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

        # Configure and build ns-3
        self.configure_and_build(path)

        self.path = path
        self.script = script
        build_status_path = os.path.join(path,
                                         'build/optimized/build-status.py')
        spec = importlib.util.spec_from_file_location('build_status',
                                                      build_status_path)
        build_status = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build_status)

        self.script_executable = next((os.path.join(path, program) for program
                                       in build_status.ns3_runnable_programs if
                                       self.script in program), None)

        if self.script_executable is None:
            raise ValueError("Cannot find %s script" % self.script)

        self.environment = {
            'LD_LIBRARY_PATH': os.path.join(path, 'build/optimized'),
            'DYLD_LIBRARY_PATH': os.path.join(path, 'build/optimized')}

    #############
    # Utilities #
    #############

    def configure_and_build(self, path, verbose=False, progress=True):
        """
        Configure and build the ns-3 code.
        """

        # Check whether path points to a valid installation
        subprocess.run(['./waf', 'configure', '--enable-examples',
                        '--disable-gtk', '--disable-python',
                        '--build-profile=optimized', '--out=build/optimized'],
                       cwd=path, stdout=subprocess.PIPE if not verbose else
                       None, stderr=subprocess.PIPE if not verbose else None)

        # Build ns-3
        build_process = subprocess.Popen(['./waf', 'build'], cwd=path,
                                         stdout=subprocess.PIPE if not verbose
                                         else None, stderr=subprocess.PIPE if
                                         not verbose else None)

        # Show a progress bar
        if progress and not verbose:
            line_iterator = self.get_output(build_process)
            try:
                [initial, total] = next(line_iterator)
                pbar = tqdm(line_iterator, initial=initial, total=total,
                            unit='file', desc='Building ns-3', smoothing=0)
                for current, total in pbar:
                    pbar.n = current
            except (StopIteration):
                pass
        else:  # Wait for the build to finish anyway
            build_process.communicate()

    def get_output(self, process):
        """Get the output of a process"""
        while True:
            output = process.stdout.readline()
            if output == b'' and process.poll() is not None:
                if process.returncode > 0:
                    raise Exception("Compilation ended with an error.")
                raise StopIteration
            if output:
                # Parse the output to get current and total tasks
                # print("Raw output: %s" % output.strip())
                # print("Doing task %s out of %s" % (current, total))
                matches = re.search('\[\s*(\d+?)/(\d+)\].*',
                                    output.strip().decode('utf-8'))
                if matches is not None:
                    yield [int(matches.group(1)), int(matches.group(2))]

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

    def run_simulations(self, parameter_list, data_folder, verbose=False):
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

            # Run from dedicated temporary folder
            current_result['id'] = str(uuid.uuid4())
            temp_dir = os.path.join(data_folder, current_result['id'])
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            start = time.time()  # Time execution
            execution = subprocess.run(command, cwd=temp_dir,
                                       env=self.environment,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            end = time.time()  # Time execution

            if execution.returncode > 0:
                complete_command = [self.script]
                complete_command.extend(command[1:])
                complete_command = "./waf --run \"%s\"" % (
                    ' '.join(complete_command))

                raise Exception(('Simulation exited with an error.\n'
                                 'Params: %s\n'
                                 '\nStderr: %s\n'
                                 'Stdout: %s\n'
                                 'Use the following command to reproduce:\n%s'
                                 % (parameter, execution.stderr,
                                    execution.stdout, complete_command)))

            current_result['elapsed_time'] = end-start

            current_result['stdout'] = execution.stdout.decode('utf-8')

            yield current_result
