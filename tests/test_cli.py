import sem
# For testing the command line we leverage click facilities
from click.testing import CliRunner
import re


def test_cli_help():
    runner = CliRunner()
    runner.invoke(sem.cli, '--help')


def test_cli_run(tmpdir, ns_3_compiled, config):
    runner = CliRunner()
    runner.invoke(sem.cli, ['run', '--ns-3-path=%s' % ns_3_compiled,
                            '--results-dir=%s' % tmpdir.join('results'),
                            '--script=%s' % config['script']],
                  input="'/usr/share/dict/web2'\n'false'\n1\n",
                  catch_exceptions=False)


def test_cli_workflow(tmpdir, ns_3_compiled, config):
    runner = CliRunner()

    # Run some simulations
    runner.invoke(sem.cli, ['run', '--ns-3-path=%s' % ns_3_compiled,
                            '--results-dir=%s' % tmpdir.join('results'),
                            '--script=%s' % config['script']],
                  input="'/usr/share/dict/web2'\n'false'\n1\n",
                  catch_exceptions=False)

    # Run again, this time defaults should be shown since we have already some
    # simulations in the database
    runner.invoke(sem.cli, ['run', '--ns-3-path=%s' % ns_3_compiled,
                            '--results-dir=%s' % tmpdir.join('results'),
                            '--script=%s' % config['script']],
                  input="\n\n1\n",
                  catch_exceptions=False)

    # View all results
    runner.invoke(sem.cli, ['view', '--results-dir=%s' %
                            tmpdir.join('results'), '--show-all'],
                  input="q",
                  catch_exceptions=False)

    # Accept a query
    runner.invoke(sem.cli, ['view', '--results-dir=%s' %
                            tmpdir.join('results')],
                  input="['/usr/share/dict/web2']\n['false']\nq",
                  catch_exceptions=False)

    # Show results including simulation output
    result = runner.invoke(sem.cli, ['view', '--results-dir=%s' %
                                     tmpdir.join('results'),
                                     '--show-simulation-output'])

    # Get result id to test id-based options
    result_id = re.findall('.*id\':\s\'(.*)\'', result.output)[0]

    # Test command printing sub-command
    runner.invoke(sem.cli, ['command', '--results-dir=%s' %
                            tmpdir.join('results'),
                            result_id])

    # Export results
    runner.invoke(sem.cli, ['export', '--results-dir=%s' %
                            tmpdir.join('results'), '--do-not-try-parsing',
                            'matlab_output.mat'],
                  input="\n\n1\n",
                  catch_exceptions=False)
    runner.invoke(sem.cli, ['export', '--results-dir=%s' %
                            tmpdir.join('results'), '--do-not-try-parsing',
                            'numpy_output.npy'],
                  input="\n\n1\n",
                  catch_exceptions=False)
    runner.invoke(sem.cli, ['export', '--results-dir=%s' %
                            tmpdir.join('results'), '--do-not-try-parsing',
                            'folder_output'],
                  input="\n\n1\n",
                  catch_exceptions=False)
