import pytest
import shutil
import os
import subprocess
import collections
from git import Repo
from sem import CampaignManager

ns_3_examples = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../examples', 'ns-3')
ns_3_test = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ns-3')
ns_3_test_compiled = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                  'ns-3-compiled')
ns_3_test_compiled_debug = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                  'ns-3-compiled-debug')

def get_build_program(ns_3_dir):
    if os.path.exists(os.path.join(ns_3_dir, "ns3")):
        return "./ns3"
    else:
        return "./waf"

@pytest.fixture(scope='function')
def ns_3(tmpdir):
    # Copy the test ns-3 installation in the temporary directory
    ns_3_tempdir = tmpdir.join('ns-3')
    shutil.copytree(ns_3_test, str(ns_3_tempdir), symlinks=True,
                    # Do not copy cmake's cache, as it is directory-dependant 
                    ignore=shutil.ignore_patterns("cmake-cache"))  
    return ns_3_tempdir


@pytest.fixture(scope='function')
def ns_3_compiled(tmpdir):
    # Copy the test ns-3 installation in the temporary directory
    ns_3_tempdir = str(tmpdir.join('ns-3-compiled'))
    shutil.copytree(ns_3_test_compiled, ns_3_tempdir, symlinks=True, 
                    # Do not copy cmake's cache, as it is directory-dependant 
                    ignore=shutil.ignore_patterns("cmake-cache"))  

    build_program = get_build_program(ns_3_tempdir)

    # Relocate build by running the same command in the new directory
    if subprocess.call([build_program, 'configure', '--disable-gtk',
                        '--build-profile=optimized', '--enable-modules=core', '--enable-examples',
                        '--out=build/optimized'],
                       cwd=ns_3_tempdir,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL) > 0:
        raise Exception("Configuration failed")
    
    if subprocess.call([build_program, 'build'],
                       cwd=ns_3_tempdir,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL) > 0:
        raise Exception("Build failed")

    return ns_3_tempdir


@pytest.fixture(scope='function')
def ns_3_compiled_debug(tmpdir):
    # Copy the test ns-3 installation in the temporary directory
    ns_3_tempdir = str(tmpdir.join('ns-3-compiled-debug'))
    shutil.copytree(ns_3_test_compiled_debug, ns_3_tempdir, symlinks=True,
                    # Do not copy cmake's cache, as it is directory-dependant 
                    ignore=shutil.ignore_patterns("cmake-cache"))  

    build_program = get_build_program(ns_3_tempdir)

    # Relocate build by running the same command in the new directory
    if subprocess.call([build_program, 'configure', '--disable-gtk',
                        '--build-profile=debug', '--enable-modules=core', '--enable-examples',
                        '--out=build'],
                       cwd=ns_3_tempdir,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL) > 0:
        raise Exception("Configuration failed")
    
    if subprocess.call([build_program, 'build'],
                       cwd=ns_3_tempdir,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL) > 0:
        raise Exception("Build failed")

    return ns_3_tempdir

@pytest.fixture(scope='function')
def ns_3_compiled_examples():
    # Configure and build WAF-based ns-3
    build_program = get_build_program(ns_3_examples)

    if subprocess.call([build_program, 'configure', '--disable-gtk',
                        '--build-profile=optimized', '--enable-modules=core',
                        '--out=build/optimized'],
                       cwd=ns_3_examples,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.STDOUT) != 0:
        raise Exception("Examples configuration failed.")
    
    if subprocess.call([build_program, 'build'],
                       cwd=ns_3_examples,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL) > 0:
        raise Exception("Examples build failed.")
    
    return ns_3_examples

@pytest.fixture(scope='function')
def config(tmpdir, ns_3_compiled):
    return {
        'script': 'hash-example',
        'commit': Repo(ns_3_compiled).head.commit.hexsha,
        'params': {'dict': '/usr/share/dict/words', 'time': False},
        'campaign_dir': str(tmpdir.join('test_campaign')),
    }


@pytest.fixture(scope='function')
def result(config):
    r = {
        'params': collections.OrderedDict(
            [('dict', '/usr/share/dict/american-english'),
             ('time', False),
             ('RngRun', 10)]),
        'meta': {
            'elapsed_time': 10,
            'id': '98f89356-3682-4cb4-b6c3-3c792979a8fc',
        }
    }

    return r


@pytest.fixture(scope='function')
def parameter_combination_no_rngrun():
    # We need to explicitly state we want an OrderedDict here in order to
    # support Python < 3.6 - since Python 3.6, dicts are ordered by default
    return collections.OrderedDict([('dict', '/usr/share/dict/american-english'),
                                    ('time', False)])

@pytest.fixture(scope='function')
def parameter_combination():
    # We need to explicitly state we want an OrderedDict here in order to
    # support Python < 3.6 - since Python 3.6, dicts are ordered by default
    return collections.OrderedDict([('dict', '/usr/share/dict/american-english'),
                                    ('time', False),
                                    ('RngRun', '0')])


@pytest.fixture(scope='function')
def parameter_combination_2():
    return collections.OrderedDict([('dict', '/usr/share/dict/british-english'),
                                    ('time', True),
                                    ('RngRun', '0')])


@pytest.fixture(scope='function')
def parameter_combination_range():
    return collections.OrderedDict([('dict', ['/usr/share/dict/american-english',
                                              '/usr/share/dict/british-english']),
                                    ('time', [False, True])])


@pytest.fixture(scope='function')
def manager(ns_3_compiled, config):
    return CampaignManager.new(ns_3_compiled, config['script'],
                               config['campaign_dir'])


def get_and_compile_ns_3():
    # Clone latest ns-3
    if not os.path.exists(ns_3_test):
        Repo.clone_from('https://gitlab.com/nsnam/ns-3-dev.git', ns_3_test)

    # Copy folder to compile in optimized mode
    if not os.path.exists(ns_3_test_compiled):
        shutil.copytree(ns_3_test, ns_3_test_compiled, symlinks=True,
                        # Do not copy cmake's cache, as it is directory-dependant 
                        ignore=shutil.ignore_patterns("cmake-cache"))  

    # Copy folder to compile in debug mode
    if not os.path.exists(ns_3_test_compiled_debug):
        shutil.copytree(ns_3_test, ns_3_test_compiled_debug, symlinks=True,
                        # Do not copy cmake's cache, as it is directory-dependant 
                        ignore=shutil.ignore_patterns("cmake-cache"))    

    build_program = get_build_program(ns_3_test_compiled)

    if subprocess.call([build_program, 'configure', '--disable-gtk',
                        '--build-profile=optimized', '--enable-modules=core',
                        '--out=build/optimized'],
                       cwd=ns_3_test_compiled,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.STDOUT) != 0:
        raise Exception("Optimized test configuration failed.")
    
    if subprocess.call([build_program, 'build'],
                       cwd=ns_3_test_compiled,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL) > 0:
        raise Exception("Optimized test build failed.")

    build_program = get_build_program(ns_3_test_compiled_debug)

    if subprocess.call([build_program, 'configure', '--disable-gtk',
                        '--build-profile=debug', '--enable-modules=core',
                        '--out=build'],
                       cwd=ns_3_test_compiled_debug,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.STDOUT) != 0:
        raise Exception("Debug test configuration failed.")
    
    if subprocess.call([build_program, 'build'],
                       cwd=ns_3_test_compiled_debug,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL) > 0:
        raise Exception("Debug test build failed.")

    # Configure and build WAF-based ns-3
    build_program = get_build_program(ns_3_examples)

    if subprocess.call([build_program, 'configure', '--disable-gtk',
                        '--build-profile=optimized', '--enable-modules=core',
                        '--out=build/optimized'],
                       cwd=ns_3_examples,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.STDOUT) != 0:
        raise Exception("Examples configuration failed.")
    
    if subprocess.call([build_program, 'build'],
                       cwd=ns_3_examples,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL) > 0:
        raise Exception("Examples build failed.")

#########################################################################
# Clean up after each session                                           #
# Especially needed because we will copy ns-3 and disk space is limited #
#########################################################################


@pytest.fixture(autouse=True, scope='function')
def setup_and_cleanup(tmpdir):
    yield
    shutil.rmtree(str(tmpdir))

def pytest_configure(config):
    print("Getting and compiling ns-3...")
    get_and_compile_ns_3()
