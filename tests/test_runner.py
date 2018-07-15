from sem import SimulationRunner, ParallelRunner
import os
import pytest

###################
# Runner creation #
###################


@pytest.fixture(scope='function', params=[['ParallelRunner', True]])
def runner(ns_3_compiled, config, request):
    if request.param[0] == 'SimulationRunner':
        return SimulationRunner(ns_3_compiled, config['script'],
                                optimized=request.param[1])
    elif request.param[0] == 'ParallelRunner':
        return ParallelRunner(ns_3_compiled, config['script'],
                              optimized=request.param[1])


def test_get_available_parameters(runner, config):
    # Try getting the available parameters of the wifi-tcp script
    assert runner.get_available_parameters() == config['params']


@pytest.mark.parametrize('runner',
                         [
                             ['SimulationRunner', False],
                             ['ParallelRunner', False],
                             ['SimulationRunner', True],
                             ['ParallelRunner', True],
                          ],
                         indirect=True)
def test_run_simulations(runner, config,
                         parameter_combination):
    # Make sure that simulations run without any issue
    data_dir = os.path.join(config['campaign_dir'], 'data')
    list(runner.run_simulations([parameter_combination], data_dir))


def test_non_existent_script(ns_3_compiled):
    with pytest.raises(ValueError):
        ParallelRunner(ns_3_compiled, 'non_existing_script')


def test_empty_param_list(ns_3_compiled, config, parameter_combination):
    runner = SimulationRunner(ns_3_compiled, 'error-throwing-example')
    data_dir = os.path.join(config['campaign_dir'], 'data')
    with pytest.raises(Exception):
        list(runner.run_simulations([parameter_combination], data_dir))
