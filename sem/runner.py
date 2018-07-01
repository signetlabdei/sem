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

    def __init__(self, path, script, optimized=True):
        """
        Initialization function.
        """
        # Save member variables
        self.path = path
        self.script = script
        if optimized:
            self.environment = {
                'LD_LIBRARY_PATH': os.path.join(path, 'build/optimized'),
                'DYLD_LIBRARY_PATH': os.path.join(path, 'build/optimized')}
        else:
            self.environment = {
                'LD_LIBRARY_PATH': os.path.join(path, 'build'),
                'DYLD_LIBRARY_PATH': os.path.join(path, 'build')}

        # Configure and build ns-3
        self.configure_and_build(path, optimized=optimized)

        # Build status is used to get the executable path for the specified
        # script
        if optimized:
            build_status_path = os.path.join(path,
                                             'build/optimized/build-status.py')
        else:
            build_status_path = os.path.join(path,
                                             'build/build-status.py')
        spec = importlib.util.spec_from_file_location('build_status',
                                                      build_status_path)
        build_status = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build_status)

        self.script_executable = next((os.path.join(path, program) for program
                                       in build_status.ns3_runnable_programs if
                                       self.script in program), None)

        if self.script_executable is None:
            raise ValueError("Cannot find %s script" % self.script)

    #############
    # Utilities #
    #############

    def configure_and_build(self, show_progress=True, optimized=True):
        """
        Configure and build the ns-3 code.
        """

        if optimized:
            # Check whether path points to a valid installation
            subprocess.run(['./waf', 'configure', '--enable-examples',
                            '--disable-gtk', '--disable-python',
                            '--build-profile=optimized',
                            '--out=build/optimized'], cwd=self.path,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
        else:
            # Check whether path points to a valid installation
            subprocess.run(['./waf', 'configure', '--enable-examples',
                            '--disable-python'], cwd=self.path,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)

        # Build ns-3
        build_process = subprocess.Popen(['./waf', 'build'], cwd=self.path,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)

        # Show a progress bar
        if show_progress:
            line_iterator = self.get_output(build_process)
            pbar = None
            try:
                [initial, total] = next(line_iterator)
                pbar = tqdm(line_iterator, initial=initial, total=total,
                            unit='file', desc='Building ns-3', smoothing=0)
                for current, total in pbar:
                    pbar.n = current
            except (StopIteration):
                if pbar is not None:
                    pbar.n = pbar.total
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
        # parameters. This solution will break if the format of the output
        # changes, but I know of no better way to do this.

        result = subprocess.check_output([self.script_executable,
                                          '--PrintHelp'], env=self.environment,
                                         cwd=self.path).decode('utf-8')

        # Isolate the list of parameters
        options = re.findall('.*Program\s(?:Options|Arguments):'
                             '(.*)General\sArguments.*',
                             result, re.DOTALL)

        # Get the single parameter names
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
            stdout_file_path = os.path.join(temp_dir, 'stdout')
            stderr_file_path = os.path.join(temp_dir, 'stderr')
            with open(stdout_file_path, 'w') as stdout_file, open(
                    stderr_file_path, 'w') as stderr_file:
                execution = subprocess.run(command, cwd=temp_dir,
                                           env=self.environment,
                                           stdout=stdout_file,
                                           stderr=stderr_file)
            end = time.time()  # Time execution

            if execution.returncode > 0:
                complete_command = [self.script]
                complete_command.extend(command[1:])
                complete_command = "./waf --run \"%s\"" % (
                    ' '.join(complete_command))

                with open(stdout_file_path, 'r') as stdout_file, open(
                        stderr_file_path, 'r') as stderr_file:
                    raise Exception(('Simulation exited with an error.\n'
                                     'Params: %s\n'
                                     '\nStderr: %s\n'
                                     'Stdout: %s\n'
                                     'Use this command to reproduce:\n'
                                     '%s'
                                     % (parameter, stderr_file.read(),
                                        stdout_file.read(), complete_command)))

            current_result['elapsed_time'] = end-start

            yield current_result
