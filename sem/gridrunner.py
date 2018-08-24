from .runner import SimulationRunner
import os
import re
import uuid
import drmaa


class GridRunner(SimulationRunner):
    """
    A Runner which can perform simulations in parallel on a DRMAA-compatible
    cluster architecture.
    """

    def __init__(self, path, script, optimized=True, param_string="-l cputype=intel"):
        """
        Initialization function, which also calls the initialization of
        SimulationRunner.

        Args:
            path (str): absolute path to the ns-3 installation this Runner
                should lock on.
            script (str): ns-3 script that will be used by this Runner.
            optimized (bool): whether this Runner should build ns-3 with the
                optimized profile.
            param_string (str): a string with the parameters of the jobs for the
                cluster
        """
        self.gridParam = param_string
        SimulationRunner.__init__(self, path, script, optimized)

    def run_simulations(self, parameter_list, data_folder):
        """
        This function runs multiple simulations in parallel.
        """

        # Open up a session
        s = drmaa.Session()
        s.initialize()

        # Create a job template for each parameter combination
        jobs = {}
        for parameter in parameter_list:
            # Initialize result
            current_result = {
                'params': {},
                'meta': {}
            }
            current_result['params'].update(parameter)

            command = " ".join([self.script_executable] + ['--%s=%s' % (param,
                                                                        value)
                                                           for param, value in
                                                           parameter.items()])

            # Run from dedicated temporary folder
            current_result['meta']['id'] = str(uuid.uuid4())
            temp_dir = os.path.join(data_folder, current_result['meta']['id'])
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            jt = s.createJobTemplate()
            jt.remoteCommand = os.path.dirname(
                os.path.abspath(__file__)) + '/run_program.sh'
            jt.args = [command]
            jt.jobEnvironment = self.environment
            jt.workingDirectory = temp_dir
            jt.nativeSpecification = self.gridParam
            output_filename = os.path.join(temp_dir, 'stdout')
            error_filename = os.path.join(temp_dir, 'stderr')
            jt.outputPath = ':' + output_filename
            jt.errorPath = ':' + error_filename

            jobid = s.runJob(jt)

            # Save the template in our dictionary
            jobs[jobid] = {
                'template': jt,
                'result': current_result,
                'output': output_filename,
                'error': error_filename,
                }

        # Check for job completion, yield results when they are ready
        try:

            while True:
                if len(jobs) == 0:
                    # Clean up
                    raise StopIteration

                for curjob in jobs.keys():
                    if s.jobStatus(curjob) is drmaa.JobState.DONE:

                        current_result = jobs[curjob]['result']

                        # TODO Actually compute time elapsed in the running
                        # state
                        current_result['meta']['elapsed_time'] = 0

                        s.deleteJobTemplate(jobs[curjob]['template'])
                        del jobs[curjob]

                        yield current_result

                        break

        finally:
            try:
                for v in jobs.values():
                    s.deleteJobTemplate(v['template'])
                s.control(drmaa.JOB_IDS_SESSION_ALL,
                          drmaa.JobControlAction.TERMINATE)
                s.synchronize([drmaa.JOB_IDS_SESSION_ALL], dispose=True)
                s.exit()
            except(drmaa.errors.NoActiveSessionException):
                pass

    def configure_and_build(self, show_progress=True, optimized=True,
                            skip_configuration=False):

        clean_before = False
        if clean_before:
            clean_command = './waf distclean'
            self.run_program((clean_command), self.path)

        if not skip_configuration:
            configuration_command = './waf configure --enable-examples '
            '--disable-gtk --disable-python'
            if optimized:
                configuration_command += '--build-profile=optimized '
                '--out=build/optimized'

            self.run_program((configuration_command), self.path)

        self.run_program(('./waf build'), self.path)

    def get_available_parameters(self):
        """
        Return a list of the parameters made available by the script.
        """

        # At the moment, we rely on regex to extract the list of available
        # parameters. A tighter integration with waf would allow for a more
        # natural extraction of the information.

        stdout = self.run_program("%s %s" % (self.script_executable,
                                             '--PrintHelp'),
                                  environment=self.environment)

        options = re.findall('.*Program\s(?:Arguments|Options):(.*)'
                             'General\sArguments.*',
                             stdout, re.DOTALL)

        if len(options):
            args = re.findall('.*--(.*?):.*', options[0], re.MULTILINE)
            return args
        else:
            return []

    def set_grid_parameters(self, param_string="-l cputype=intel"):
        """
        Set the relevant parameters for the jobs

        Args:
            param_string (str): a string with the parameters
        """
        self.gridParam = param_string

    def run_program(self, command, working_directory=os.getcwd(),
                    environment=None, cleanup_files=True):
        """
        Run a program through the grid, capturing the standard output.
        """
        try:
            s = drmaa.Session()
            s.initialize()
            jt = s.createJobTemplate()
            jt.remoteCommand = os.path.dirname(
                os.path.abspath(__file__)) + '/run_program.sh'
            jt.args = [command]

            if environment is not None:
                jt.jobEnvironment = environment

            jt.workingDirectory = working_directory
            jt.nativeSpecification = self.gridParam
            output_filename = os.path.join(working_directory, 'output.txt')
            jt.outputPath = ':' + output_filename
            jt.joinFiles = True

            jobid = s.runJob(jt)

            s.wait(jobid, drmaa.Session.TIMEOUT_WAIT_FOREVER)

            with open(output_filename, 'r') as output:
                stdout = output.read()

            # Clean up
            if cleanup_files:
                os.remove(output_filename)

        finally:
            try:
                s.control(drmaa.JOB_IDS_SESSION_ALL,
                          drmaa.JobControlAction.TERMINATE)
                s.synchronize([drmaa.JOB_IDS_SESSION_ALL], dispose=True)
                s.exit()
            except(drmaa.errors.NoActiveSessionException):
                pass

        return stdout
