import importlib
import os
import re
import subprocess
import time
import uuid
import sem.utils
import sys
from importlib.machinery import SourceFileLoader
import types

from tqdm import tqdm


class SimulationRunner(object):
    """
    The class tasked with running simulations and interfacing with the ns-3
    system.
    """

    ##################
    # Initialization #
    ##################

    def __init__(self, path, script, optimized=True, skip_configuration=False,
                 max_parallel_processes=None):
        """
        Initialization function.

        Args:
            path (str): absolute path to the ns-3 installation this Runner
                should lock on.
            script (str): ns-3 script that will be used by this Runner.
            optimized (bool): whether this Runner should build ns-3 with the
                optimized profile.
            skip_configuration (bool): whether to skip the configuration step,
                and only perform compilation.
        """

        # Save member variables
        self.path = path
        self.script = script
        self.optimized = optimized
        self.max_parallel_processes = max_parallel_processes

        if optimized:
            # For old ns-3 installations, the library is in build, while for
            # recent ns-3 installations it's in build/lib. Both paths are
            # thus required to support all versions of ns-3.
            library_path = "%s:%s" % (
                os.path.join(path, 'build/optimized'),
                os.path.join(path, 'build/optimized/lib'))
        else:
            library_path = "%s:%s" % (
                os.path.join(path, 'build/'),
                os.path.join(path, 'build/lib'))

        # We use both LD_ and DYLD_ to support Linux and Mac OS.
        self.environment = {
            'LD_LIBRARY_PATH': library_path,
            'DYLD_LIBRARY_PATH': library_path}

        # Configure and build ns-3
        self.configure_and_build(path, optimized=optimized,
                                 skip_configuration=skip_configuration)

        # ns-3's build status output is used to get the executable path for the
        # specified script.
        if os.path.exists(os.path.join(self.path, "ns3")):
            # In newer versions of ns-3 (3.36+), the name of the build status file is 
            # platform-dependent
            build_status_fname = ".lock-ns3_%s_build" % sys.platform
            build_status_path = os.path.join(path, build_status_fname)
        else:
            build_status_fname = "build-status.py"
            if optimized:
                build_status_path = os.path.join(path,
                                                'build/optimized/build-status.py')
            else:
                build_status_path = os.path.join(path,
                                                'build/build-status.py')

        # By importing the file, we can naturally get the dictionary
        loader = importlib.machinery.SourceFileLoader(build_status_fname, build_status_path)
        mod = types.ModuleType(loader.name)
        loader.exec_module(mod)
            

        # Search is simple: we look for the script name in the program field.
        # Note that this could yield multiple matches, in case the script name
        # string is contained in another script's name.
        # matches contains [program, path] for each program matching the script
        matches = [{'name': program,
                    'path': os.path.abspath(os.path.join(path, program))} for
                   program in mod.ns3_runnable_programs if self.script
                   in program]

        if not matches:
            raise ValueError("Cannot find %s script" % self.script)

        # To handle multiple matches, we take the 'better matching' option,
        # i.e., the one with length closest to the original script name.
        match_percentages = map(lambda x: {'name': x['name'],
                                           'path': x['path'],
                                           'percentage':
                                           len(self.script)/len(x['name'])},
                                matches)

        self.script_executable = max(match_percentages,
                                     key=lambda x: x['percentage'])['path']

        # This step is not needed for CMake versions of ns-3
        if "scratch" in self.script_executable and not os.path.exists(os.path.join(self.path, "ns3")):
            path_with_subdir = self.script_executable.split("/scratch/")[-1]
            if ("/" in path_with_subdir):  # Script is in a subdir
                executable_subpath = "%s/%s" % (self.script, self.script)
            else:  # Script is in scratch root
                executable_subpath = self.script
            if optimized:
                self.script_executable = os.path.abspath(
                    os.path.join(path,
                                 "build/optimized/scratch",
                                 executable_subpath))
            else:
                self.script_executable = os.path.abspath(
                    os.path.join(path,
                                 "build/scratch",
                                 executable_subpath))

    #############
    # Utilities #
    #############

    def configure_and_build(self, show_progress=True, optimized=True,
                            skip_configuration=False):
        """
        Configure and build the ns-3 code.

        Args:
            show_progress (bool): whether or not to display a progress bar
                during compilation.
            optimized (bool): whether to use an optimized build. If False, use
                a standard configure.
            skip_configuration (bool): whether to skip the configuration step,
                and only perform compilation.
        """

        build_program = "./ns3" if os.path.exists(os.path.join(self.path, "ns3")) else "./waf"

        # Only configure if necessary
        if not skip_configuration:
            configuration_command = ['python3', build_program, 'configure',
                                     '--enable-examples', '--disable-gtk',
                                     '--disable-werror']

            if optimized:
                configuration_command += ['--build-profile=optimized',
                                          '--out=build/optimized']

            # Check whether path points to a valid installation
            subprocess.call(configuration_command, cwd=self.path,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Build ns-3
        j_argument = ['-j', str(self.max_parallel_processes)] if self.max_parallel_processes else []
        build_process = subprocess.Popen(['python3', build_program] + j_argument + ['build'],
                                         cwd=self.path,
                                         stdout=subprocess.PIPE)

        # Show a progress bar
        if show_progress:
            if build_program == "ns3":
                bar_format = '{desc}: {percentage:3.0f}%|{bar}| [{elapsed}<{remaining}]'
            else:
                bar_format = None
            line_iterator = self.get_build_output(build_process,
                                                  build_program)
            pbar = None
            try:
                [initial, total] = next(line_iterator)
                pbar = tqdm(initial=initial,
                            total=total,
                            unit='file',
                            desc='Building ns-3',
                            smoothing=0,
                            bar_format=bar_format)
                with pbar as progress_bar:
                    for current, total in line_iterator:
                        progress_bar.n = current
                        progress_bar.update(0)
                    progress_bar.n = progress_bar.total
            except (StopIteration):
                if pbar is not None:
                    pbar.n = pbar.total
        else:  # Wait for the build to finish anyway
            build_process.communicate()

    def get_build_output(self, process, build_program):
        """
        Parse the output of the ns-3 build process to extract the information
        that is needed to draw the progress bar.

        Args:
            process: the subprocess instance to listen to.
        """

        while True:
            output = process.stdout.readline()
            if output == b'' and process.poll() is not None:
                if process.returncode > 0:
                    raise Exception("Compilation ended with an error"
                                    ".\nSTDOUT\n%s" %
                                    (process.stdout.read()))
                return
            if output:
                if build_program == "ns3":
                    # Parse the output to get current and total tasks In
                    # case we are using ns3, the format will be as a
                    # percentage between square brackets:
                    matches = re.search(r'\[\s*(\d+?)%].*',
                                        output.strip().decode('utf-8'))
                    if matches is not None:
                        yield [int(matches.group(1)), 100]
                else:
                    # In case we are using waf, the progress is displayed
                    # in the form [current/total]
                    matches = re.search(r'\[\s*(\d+?)/(\d+)\].*',
                                        output.strip().decode('utf-8'))
                    if matches is not None:
                        yield [int(matches.group(1)), int(matches.group(2))]

    def get_available_parameters(self):
        """
        Return a list of the parameters made available by the script.
        """

        # At the moment, we rely on regex to extract the list of available
        # parameters. This solution will break if the format of the output
        # changes, but this is the best option that is currently available.

        result = subprocess.check_output([self.script_executable,
                                          '--PrintHelp'], env=self.environment,
                                         cwd=self.path).decode('utf-8')

        # Isolate the list of parameters
        options = re.findall(r'.*Program\s(?:Options|Arguments):'
                             r'(.*)General\sArguments.*',
                             result, re.DOTALL)

        global_options = subprocess.check_output([self.script_executable,
                                                  '--PrintGlobals'],
                                                 env=self.environment,
                                                 cwd=self.path).decode('utf-8')

        # Get the single parameter names
        params = {}
        if len(options):
            parsed = {}
            for line in options[0].splitlines():
                key = re.findall(r'.*--(.*?)[?::|=].*', line)
                value = re.findall(r'.*\[(.*?)]', line)
                if key:
                    if not value:
                        value = None
                    else:
                        value = value[0]
                    parsed[key[0]] = value
            for k, v in parsed.items():
                if v is None:
                    params[k] = None
                elif str(v).lower() == 'true':
                    params[k] = True
                elif str(v).lower() == 'false':
                    params[k] = False
                else:
                    try:
                        params[k] = float(v)
                    except ValueError:
                        # Keep it as a (possibly empty) string
                        params[k] = str(v)
        if len(global_options):
            params.update({k:v for k, v in re.findall(r'.*--(.*?)[?::|=].*\[(.*?)\]',
                                                      global_options, re.MULTILINE) if k
                     not in ['RngRun', 'RngSeed', 'SchedulerType',
                             'SimulatorImplementationType', 'ChecksumEnabled']})
        return params  # Return a sorted list

    ######################
    # Simulation running #
    ######################

    def run_simulations(self, parameter_list, data_folder, stop_on_errors=False):
        """
        Run several simulations using a certain combination of parameters.

        Yields results as simulations are completed.

        Args:
            parameter_list (list): list of parameter combinations to simulate.
            data_folder (str): folder in which to save subfolders containing
                simulation output.
        """

        for _, parameter in enumerate(parameter_list):

            current_result = {
                'params': {},
                'meta': {}
                }
            current_result['params'].update(parameter)

            command = [self.script_executable] + ['--%s=%s' % (param, value)
                                                  for param, value in
                                                  parameter.items()]

            # Run from dedicated temporary folder
            current_result['meta']['id'] = str(uuid.uuid4())
            temp_dir = os.path.join(data_folder, current_result['meta']['id'])
            os.makedirs(temp_dir)

            start = time.time()  # Time execution
            stdout_file_path = os.path.join(temp_dir, 'stdout')
            stderr_file_path = os.path.join(temp_dir, 'stderr')
            with open(stdout_file_path, 'w') as stdout_file, open(
                    stderr_file_path, 'w') as stderr_file:
                return_code = subprocess.call(command, cwd=temp_dir,
                                              env=self.environment,
                                              stdout=stdout_file,
                                              stderr=stderr_file)
            end = time.time()  # Time execution

            if return_code != 0:
                with open(stdout_file_path, 'r') as stdout_file, open(
                        stderr_file_path, 'r') as stderr_file:
                    complete_command = sem.utils.get_command_from_result(self.script, current_result)
                    complete_command_debug = sem.utils.get_command_from_result(self.script, current_result, debug=True)
                    error_message = ('\nSimulation exited with an error.\n'
                                     'Params: %s\n'
                                     'Stderr: %s\n'
                                     'Stdout: %s\n'
                                     'Use this command to reproduce:\n'
                                     '%s\n'
                                     'Debug with gdb:\n'
                                     '%s'
                                     % (parameter,
                                        stderr_file.read(),
                                        stdout_file.read(),
                                        complete_command,
                                        complete_command_debug))
                    if stop_on_errors:
                        raise Exception(error_message)
                    print(error_message)

            current_result['meta']['elapsed_time'] = end-start
            current_result['meta']['exitcode'] = return_code

            yield current_result
