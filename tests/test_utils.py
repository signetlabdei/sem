from sem import list_param_combinations, automatic_parser, stdout_automatic_parser, CallbackBase, CampaignManager
import json
import numpy as np
from operator import getitem


def test_list_param_combinations():
    # Two possible combinations
    d1 = {'a': [1, 2]}
    assert set(map(lambda x: getitem(x, 'a'),
                   list_param_combinations(d1))) == set([1, 2])

    # Two possible combinations with two specified values
    d2 = {'b': [3], 'c': [4, 5]}
    assert set(map(lambda x: getitem(x, 'b'),
                   list_param_combinations(d2))) == set([3, 3])
    assert set(map(lambda x: getitem(x, 'c'),
                   list_param_combinations(d2))) == set([4, 5])

    # Four combinations with two specified values
    d3 = {'d': [6, 7], 'e': [8, 9]}
    assert sorted(map(lambda x: json.dumps(x, sort_keys=True),
                      list_param_combinations(d3))) == sorted(
                          map(lambda x: json.dumps(x, sort_keys=True),
                              [{'d': 6, 'e': 8}, {'d': 7, 'e': 8},
                               {'d': 6, 'e': 9}, {'d': 7, 'e': 9}]))

    params = {
        'a': [1],
        'b': [1, 2, 3],
    }
    params_more = {
        'a': [3],
        'b': [1, 2, 3],
    }
    params_same_as_above = {
        'a': [1, 3],
        'b': [1, 2, 3],
    }
    assert (sorted(map(lambda x: json.dumps(x, sort_keys=True),
                       list_param_combinations(params_same_as_above)))
            ==
            sorted(map(lambda x: json.dumps(x, sort_keys=True),
                       list_param_combinations([params, params_more]))))

    params_with_lambda = {
        'a': [1, 3],
        'b': lambda p: [10 * p['a']]
    }
    assert (sorted(map(lambda x: json.dumps(x, sort_keys=True),
                       list_param_combinations(params_with_lambda)))
            ==
            sorted(map(lambda x: json.dumps(x, sort_keys=True),
                       [{'a': 1, 'b': 10}, {'a': 3, 'b': 30}])))

    params_with_lambda_returning_list = {
        'a': [1, 3],
        'b': lambda p: list(range(p['a'])),
    }
    assert (sorted(map(lambda x: json.dumps(x, sort_keys=True),
                       list_param_combinations(params_with_lambda_returning_list)))
            ==
            sorted(map(lambda x: json.dumps(x, sort_keys=True),
                       [{'a': 1, 'b': 0}, {'a': 3, 'b': 0},
                        {'a': 3, 'b': 1}, {'a': 3, 'b': 2}])))

    params_with_two_lambdas = {
        'a': [1, 3],
        'b': lambda p: list(range(p['a'])),
        'c': lambda p: [10 * p['b']]
    }
    assert (sorted(map(lambda x: json.dumps(x, sort_keys=True),
                       list_param_combinations(params_with_two_lambdas)))
            ==
            sorted(map(lambda x: json.dumps(x, sort_keys=True),
                       [{'a': 1, 'b': 0, 'c': 0}, {'a': 3, 'b': 0, 'c': 0},
                        {'a': 3, 'b': 1, 'c': 10}, {'a': 3, 'b': 2, 'c': 20}])))


def test_stdout_automatic_parser(result):
    # Create a dummy result
    result['output'] = {}
    result['output']['stderr'] = ''
    result['output']['stdout'] = '1 2 3 4 5\n6 7 8 9 10'

    parsed = stdout_automatic_parser(result)

    assert np.all(parsed == [[1, 2, 3, 4, 5],
                             [6, 7, 8, 9, 10]])


def test_automatic_parser(result):
    # Create a dummy result
    result['output'] = {}
    result['output']['stderr'] = ''
    result['output']['stdout'] = '1 2 3 4 5\n6 7 8 9 10'

    parsed = automatic_parser(result)

    assert np.all(parsed['stdout'] == [[1, 2, 3, 4, 5],
                                       [6, 7, 8, 9, 10]])
    assert parsed['stderr'] == []

class TestCallback(CallbackBase):
    def __init__(self):
        CallbackBase.__init__(self, verbose=2)
        self.output = ''

    def _on_simulation_start(self) -> None:
        self.output += 'Starting the simulations!\n'

    def _on_simulation_end(self) -> None:
        self.output += 'Simulations are over!\n'

    def _on_run_start(self, configuration: dict, sim_uuid: str) -> None:
        self.output += 'Start single run!\n'

    def _on_run_end(self, sim_uuid: str, return_code: int, sim_time: int) -> bool:
        self.output += f'Run ended! {return_code}\n'
        return True


def test_callback(ns_3_compiled, config, parameter_combination):
    cb = TestCallback()
    n_runs = 10
    expected_output = 'Starting the simulations!\n' + f'Start single run!\nRun ended {0}\n' * n_runs + 'Simulations are over!\n'

    campaign = CampaignManager.new(ns_3_compiled, config['script'], config['campaign_dir'], runner_type='SimulationRunner',#, overwrite=True,
                                       skip_configuration=True,
                                       check_repo=False 
                                       #, optimized=True, max_parallel_processes=max_parallel_processes
                                       )
    
    parameter_combination['RngRun'] = [run for run in range(n_runs)]
    campaign.run_simulations(parameter_combination, callbacks=[cb], stop_on_errors=False)

    assert expected_output == cb.output
