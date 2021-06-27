import sem
from math import log
from sem import list_param_combinations, automatic_parser, stdout_automatic_parser, parse_log_component
import json
import numpy as np
import pytest
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


def test_parse_log_component(ns_3_compiled_debug, config):
    log_component = {
                'component1': 'info|prefix_level',
                'component2': 'level_debug|info',
                'component3': 'all|prefix_all',
                'component4': '**',
                'component5': '*|info',
                'component6': 'info|*',
                'component7': 'prefix_all'
            }

    new_component = parse_log_component(log_component=log_component)

    assert new_component == {
        'component1': 'info',
        'component2': 'error|warn|debug|info',
        'component3': 'error|warn|debug|info|function|logic',
        'component4': 'error|warn|debug|info|function|logic',
        'component5': 'error|warn|debug|info|function|logic',
        'component6': 'info',
        'component7': ''
    }

    log_component = {
        'component1': 'info|err'
    }

    with pytest.raises(ValueError):
        new_component = parse_log_component(log_component=log_component)

    new_campaign = sem.CampaignManager.new(ns_3_compiled_debug,
                                           'logging-ns3-script',
                                           config['campaign_dir'],
                                           overwrite=True,
                                           optimized=False)

    log_component = {
        '*': 'info',
        'Simulator': 'level_info'
    }

    with pytest.raises(ValueError):
        new_component = parse_log_component(log_component=log_component)

    ns3_log_components = new_campaign.runner.get_available_log_components()

    new_component = parse_log_component(log_component=log_component,
                                        ns3_log_components=ns3_log_components)

    assert new_component['Simulator'] == 'error|warn|debug|info'

    log_component = {
        'NonExistentLogComponent': 'info'
    }

    with pytest.raises(ValueError):
        new_component = parse_log_component(log_component=log_component,
                                            ns3_log_components=ns3_log_components)
