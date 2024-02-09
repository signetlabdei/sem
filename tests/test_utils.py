from sem import list_param_combinations, automatic_parser, stdout_automatic_parser, get_command_from_result, CampaignManager
import json
import numpy as np
import pytest
from operator import getitem


@pytest.fixture(scope='function', params=[['compiled', False]])
def ns_3_compiled_folder_and_command(ns_3_compiled, ns_3_compiled_examples, request):
    if request.param[0] == 'compiled':
        if request.param[1] is False:
            return [ns_3_compiled, False, './ns3 run \"hash-example --dict=/usr/share/dict/american-english --time=False --RngRun=0\"']
        # elif request.param[1] is True:
        #     return [ns_3_compiled, True, './ns3 run \"hash-example --dict=/usr/share/dict/american-english --time=False --RngRun=0\"']
    elif request.param[0] == 'compiled_examples':
        if request.param[1] is False:
            return [ns_3_compiled_examples, False, 'python3 ./waf --run \"hash-example --dict=/usr/share/dict/american-english --time=False --RngRun=0\"']
        # elif request.param[1] is True:
        #     return [ns_3_compiled_examples, True, 'python3 ./waf --run \"hash-example --dict=/usr/share/dict/american-english --time=False --RngRun=0\"']


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


@pytest.mark.parametrize('ns_3_compiled_folder_and_command',
                         [
                             ['compiled', False],
                             ['compiled_examples', False]
                         ],
                         indirect=True)
def test_get_cmnd_from_result(ns_3_compiled_folder_and_command, config, parameter_combination):

    # Create an ns-3 campaign to run simulations and obtain a result
    ns_3_folder = ns_3_compiled_folder_and_command[0]
    hardcoded_command = ns_3_compiled_folder_and_command[2]

    cmpgn = CampaignManager.new(ns_3_folder,
                                config['script'],
                                config['campaign_dir'],
                                overwrite=True,
                                skip_configuration=True)

    cmpgn.run_simulations([parameter_combination], show_progress=False)

    # Retrieve the results, and compare the output of get_command_from_result
    # with the expected command
    result = cmpgn.db.get_complete_results()[0]
    cmnd = get_command_from_result(
        config['script'], ns_3_folder, result)
    assert (hardcoded_command == cmnd)
