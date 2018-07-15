import pytest
import shutil
import os
import subprocess
from git import Repo
from sem import CampaignManager

ns_3_examples = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../examples', 'ns-3')
ns_3_test = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ns-3')
ns_3_test_compiled = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                  'ns-3-compiled')


@pytest.fixture(scope='function')
def ns_3(tmpdir):
    # Copy the test ns-3 installation in the temporary directory
    ns_3_tempdir = tmpdir.join('ns-3')
    shutil.copytree(ns_3_test, str(ns_3_tempdir), symlinks=True)
    return ns_3_tempdir


@pytest.fixture(scope='function')
def ns_3_compiled(tmpdir):
    # Copy the test ns-3 installation in the temporary directory
    ns_3_tempdir = str(tmpdir.join('ns-3-compiled'))
    shutil.copytree(ns_3_test_compiled, ns_3_tempdir, symlinks=True)

    # Relocate build by running the same command in the new directory
    if subprocess.call(['./waf', 'configure', '--disable-gtk',
                        '--disable-python', '--build-profile=optimized',
                        '--out=build/optimized', 'build'],
                       cwd=ns_3_tempdir,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL) > 0:
        raise Exception("Build failed")
    return ns_3_tempdir


@pytest.fixture(scope='function')
def config(tmpdir, ns_3_compiled):
    return {
        'script': 'hash-example',
        'commit': 'cbcf4a24343c43bccec0af4c440ee27a1eec2796',
        'params': ['dict', 'time'],
        'campaign_dir': str(tmpdir.join('test_campaign')),
    }


@pytest.fixture(scope='function')
def result(config):
    r = {
        'params': {
            'dict': '/usr/share/dict/web2',
            'time': 'false',
            'RngRun': 10,
        },
        'meta': {
            'elapsed_time': 10,
            'id': '98f89356-3682-4cb4-b6c3-3c792979a8fc',
        }
    }

    return r


@pytest.fixture(scope='function')
def parameter_combination():
    return {
        'dict': '/usr/share/dict/web2',
        'time': 'false'
    }


@pytest.fixture(scope='function')
def manager(ns_3_compiled, config):
    return CampaignManager.new(ns_3_compiled, config['script'],
                               config['campaign_dir'])


def get_and_compile_ns_3():
    # Clone ns-3
    if not os.path.exists(ns_3_test):
        Repo.clone_from('http://github.com/DvdMgr/ns-3-dev.git', ns_3_test,
                        branch='sem-tests')
    # Compilation
    if not os.path.exists(ns_3_test_compiled):
        shutil.copytree(ns_3_test, ns_3_test_compiled, symlinks=True)

    if subprocess.call(['./waf', 'configure', '--disable-gtk',
                        '--disable-python', '--build-profile=optimized',
                        '--out=build/optimized', 'build'],
                       cwd=ns_3_test_compiled,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL) > 0:
        raise Exception("Test build failed")

    if subprocess.call(['./waf', 'configure', '--disable-gtk',
                        '--disable-python', '--build-profile=optimized',
                        '--out=build/optimized', 'build'],
                       cwd=ns_3_examples,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL) > 0:
        raise Exception("Examples build failed")

#########################################################################
# Clean up after each session                                           #
# Especially needed because we will copy ns-3 and disk space is limited #
#########################################################################


@pytest.yield_fixture(autouse=True, scope='function')
def setup_and_cleanup(tmpdir):
    yield
    shutil.rmtree(str(tmpdir))


def pytest_configure(config):
    print("Getting and compiling ns-3...")
    get_and_compile_ns_3()
