import sem
# For testing the command line we leverage click facilities
from click.testing import CliRunner


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


def test_cli_view(tmpdir, ns_3_compiled, config):
    # NOTE For these tests, we rely on the fact that fixture dictionaries are
    # ordered, in order to support Python 3.4 and 3.5.

    runner = CliRunner()

    # Run some simulations
    runner.invoke(sem.cli, ['run', '--ns-3-path=%s' % ns_3_compiled,
                            '--results-dir=%s' % tmpdir.join('results'),
                            '--script=%s' % config['script']],
                  input="'/usr/share/dict/web2'\n'false'\n1\n",
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
