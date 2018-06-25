from .runner import SimulationRunner
import os
import re
import uuid
import drmaa


class GridRunner(SimulationRunner):
    """
    A Runner which can perform simulations in parallel on a Sun Grid Engine.
    """
    def run_simulations(self, parameter_list, data_folder, verbose=False):
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
            current_result = {}
            current_result.update(parameter)

            command = " ".join([self.script_executable] + ['--%s=%s' % (param,
                                                                        value)
                                                           for param, value in
                                                           parameter.items()])

            # Run from dedicated temporary folder
            current_result['id'] = str(uuid.uuid4())
            temp_dir = os.path.join(data_folder, current_result['id'])
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            jt = s.createJobTemplate()
            jt.remoteCommand = os.path.dirname(
                os.path.abspath(__file__)) + '/run_program.sh'
            jt.args = [command]
            jt.jobEnvironment = self.environment
            jt.workingDirectory = temp_dir
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
                        current_result['elapsed_time'] = 0

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

    def configure_and_build(self, path, verbose=False, progress=True, clean=False):

        clean = True
        if clean:
            clean_command = ('./waf distclean')
            print(self.run_program(clean_command, path))

        command = ('./waf configure --enable-examples --disable-gtk '
                   '--disable-python --build-profile=optimized '
                   '--out=build/optimized build')
        print(self.run_program(command, path))

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

        options = re.findall('.*Program\sArguments:(.*)General\sArguments.*',
                             stdout, re.DOTALL)

        if len(options):
            args = re.findall('.*--(.*?):.*', options[0], re.MULTILINE)
            return args
        else:
            return []

    def run_program(self, command, working_directory=os.getcwd(),
                    environment=None, cleanup_files=True):
        """
        Run a program through the grid, capturing the standard output.
        """
        s = drmaa.Session()
        s.initialize()
        jt = s.createJobTemplate()
        jt.remoteCommand = os.path.dirname(
            os.path.abspath(__file__)) + '/run_program.sh'
        jt.args = [command]

        if environment is not None:
            jt.jobEnvironment = environment

        jt.workingDirectory = working_directory
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

        s.deleteJobTemplate(jt)
        s.exit()

        return stdout
