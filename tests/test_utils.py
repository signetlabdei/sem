from sem import list_param_combinations
import json
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
