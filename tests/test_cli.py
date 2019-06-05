import sem
# For testing the command line we leverage click facilities
from click.testing import CliRunner
import re
import pytest


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


def test_parameters_from_file(tmpdir, ns_3_compiled, config):
    runner = CliRunner()

    # Write parameter specification to file
    param_file = str(tmpdir.join("parameters.txt"))
    with open(param_file, 'w') as f:
        lines = [
            "dict: '/usr/share/dict/web2'\n",
            "time: [False, True]"
        ]
        f.writelines(lines)

    # Run some simulations
    runner.invoke(sem.cli,
                  ['run',
                   '--ns-3-path=%s' % ns_3_compiled,
                   '--results-dir=%s' % tmpdir.join('results'),
                   '--script=%s' % config['script'],
                   '--parameters=%s' % param_file],
                  input='1\n',  # Specify the runs
                  catch_exceptions=False)

    # View results
    runner.invoke(sem.cli,
                  ['view',
                   '--results-dir=%s' % tmpdir.join('results'),
                   '--parameters=%s' % param_file],
                  catch_exceptions=False)

    # Export results giving a parameter file as input
    runner.invoke(sem.cli, ['export', '--results-dir=%s' %
                            tmpdir.join('results'),
                            '--parameters=%s' % param_file, 'folder_output' ],
                  input="\n\n1\n",
                  catch_exceptions=False)



def test_cli_merge(tmpdir, ns_3_compiled, config):
    runner = CliRunner()
    runner.invoke(sem.cli, ['run', '--ns-3-path=%s' % ns_3_compiled,
                            '--results-dir=%s' % tmpdir.join('results_primary'),
                            '--script=%s' % config['script']],
                  input="'/usr/share/dict/web2'\n'false'\n1\n",
                  catch_exceptions=False)

    runner.invoke(sem.cli, ['run', '--ns-3-path=%s' % ns_3_compiled,
                            '--results-dir=%s' % tmpdir.join('results_secondary'),
                            '--script=%s' % config['script']],
                  input="'/usr/share/dict/web2'\n'false'\n1\n",
                  catch_exceptions=False)

    runner.invoke(sem.cli, ['merge', '--move=False', 'results_merged',
                            'results_primary', 'results_secondary'],
                  input="'/usr/share/dict/web2'\n'false'\n1\n",
                  catch_exceptions=False)

    runner.invoke(sem.cli, ['merge', '--move=True', 'results_merged_moved',
                            'results_primary', 'results_secondary'],
                  input="'/usr/share/dict/web2'\n'false'\n1\n",
                  catch_exceptions=False)

    # TODO Check that the new folders actually have all results we expect them
    # to have


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

    # View all results without simulation output
    runner.invoke(sem.cli, ['view', '--results-dir=%s' %
                            tmpdir.join('results'), '--show-all',
                            '--hide-simulation-output'],
                  input="q",
                  catch_exceptions=False)

    # Directly print all results to screen
    runner.invoke(sem.cli, ['view', '--results-dir=%s' %
                            tmpdir.join('results'), '--show-all',
                            '--no-pager'],
                  input="q",
                  catch_exceptions=False)

    # Without the simulation output
    runner.invoke(sem.cli,
                  ['view',
                   '--results-dir=%s' % tmpdir.join('results'),
                   '--show-all',
                   '--hide-simulation-output'],
                  input="q",
                  catch_exceptions=False)

    # Accept a query
    runner.invoke(sem.cli, ['view', '--results-dir=%s' %
                            tmpdir.join('results')],
                  input="['/usr/share/dict/web2']\n['false']\nq",
                  catch_exceptions=False)

    # Show results including simulation output
    result = runner.invoke(sem.cli, ['view', '--results-dir=%s' %
                                     tmpdir.join('results')])

    # Get result id to test id-based options
    result_id = re.findall(r'.*id\':\s\'(.*)\'', result.output)[0]

    # Show results from a single simulation
    result = runner.invoke(sem.cli, ['view', '--results-dir=%s' %
                                     tmpdir.join('results'),
                                     '--result-id=%s' % result_id])

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

    # Export results with parsing
    runner.invoke(sem.cli, ['export', '--results-dir=%s' %
                            tmpdir.join('results'), 'folder_output'],
                  input="\n\n1\n",
                  catch_exceptions=False)

    # Try using a non-existent file format
    with pytest.raises(Exception):
        runner.invoke(sem.cli, ['export', '--results-dir=%s' %
                                tmpdir.join('results'), '--do-not-try-parsing',
                                'output.fake_format'],
                      input="\n\n1\n",
                      catch_exceptions=False)
