from itertools import product

try:
    import drmaa
    DRMAA_AVAILABLE = True
except(RuntimeError):
    DRMAA_AVAILABLE = False


def list_param_combinations(param_ranges):
    """
    Create a list of all parameter combinations from a dictionary specifying
    desired parameter values as lists.

    Example:
    >>> param_ranges = {'a': [1], 'b': [2, 3]}
    >>> list_param_combinations(param_ranges)
    [{'a': 1, 'b': 2}, {'a': 1, 'b': 3}]
    """
    # Convert non-list values to single-element lists
    # This is required to make sure product work.
    for key in param_ranges:
        if not isinstance(param_ranges[key], list):
            param_ranges[key] = [param_ranges[key]]

    return [dict(zip(param_ranges, v)) for v in
            product(*param_ranges.values())]
