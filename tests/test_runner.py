from sem import SimulationRunner, ParallelRunner
import os
import pytest

###################
# Runner creation #
###################


@pytest.fixture(scope='function')
def runner(ns_3_compiled, config):
    return SimulationRunner(ns_3_compiled, config['script'])


@pytest.fixture(scope='function')
def parallel_runner(ns_3_compiled, config):
    return ParallelRunner(ns_3_compiled, config['script'])


def test_get_available_parameters(runner, parallel_runner, config):
    # Try getting the available parameters of the wifi-tcp script
    assert runner.get_available_parameters() == config['params']
    assert parallel_runner.get_available_parameters() == config['params']


def test_run_simulations(runner, parallel_runner, config,
                         parameter_combination):
    # Make sure that simulations run without any issue
    data_dir = os.path.join(config['campaign_dir'], 'data')
    list(runner.run_simulations([parameter_combination], data_dir))
    list(parallel_runner.run_simulations([parameter_combination], data_dir))
