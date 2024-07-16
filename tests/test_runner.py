from sem import SimulationRunner, ParallelRunner
import os
import pytest

###################
# Runner creation #
###################

"""
First param: Runner type
Second param: Whether to use optimized build
Third param: Whether to use the CMake-version of ns-3
"""
@pytest.fixture(scope='function', params=[['ParallelRunner', True, True],
                                          ['ParallelRunner', True, False]])
def runner(ns_3_compiled, ns_3_compiled_debug, ns_3_compiled_examples, config, request):
    ns_3_folder = ns_3_compiled 
    if request.param[1] is False:
        ns_3_folder = ns_3_compiled_debug
    if request.param[2] is True:
        assert(request.param[1] is True)
        ns_3_folder = ns_3_compiled_examples

    if request.param[0] == 'SimulationRunner':
        return SimulationRunner(ns_3_folder, config['script'],
                                optimized=request.param[1])
    elif request.param[0] == 'ParallelRunner':
        return ParallelRunner(ns_3_folder, config['script'],
                              optimized=request.param[1])

def test_get_available_parameters(runner, config):
    # Try getting the available parameters of the script
    assert runner.get_available_parameters() == config['params']


@pytest.mark.parametrize('runner',
                         [
                             ['SimulationRunner', True, True],
                             ['ParallelRunner', True, True],
                             ['ParallelRunner', True, False],
                          ],
                         indirect=True)
def test_run_simulations(runner, config,
                         parameter_combination):
    # Make sure that simulations run without any issue,
    # with CMake optimized and debug builds, and Waf optimized builds
    data_dir = os.path.join(config['campaign_dir'], 'data')
    list(runner.run_simulations([parameter_combination], data_dir))


def test_scratch_script(ns_3_compiled, config):
    data_dir = os.path.join(config['campaign_dir'], 'data')
    runner = ParallelRunner(ns_3_compiled, 'scratch-simulator')
    list(runner.run_simulations([{}], data_dir))


def test_scratch_script_in_subdir(ns_3_compiled, config):
    data_dir = os.path.join(config['campaign_dir'], 'data')
    runner = ParallelRunner(ns_3_compiled, 'subdir')
    list(runner.run_simulations([{}], data_dir))


def test_non_existent_script(ns_3_compiled):
    with pytest.raises(ValueError):
        ParallelRunner(ns_3_compiled, 'non_existing_script')


def test_script_without_args(ns_3_compiled):
    ParallelRunner(ns_3_compiled, 'sample-random-variable')
