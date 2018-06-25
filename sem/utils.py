from itertools import product

try:
    DRMAA_AVAILABLE = True
    import drmaa
except(RuntimeError):
    DRMAA_AVAILABLE = False


def list_param_combinations(param_ranges):
    # Convert non-list values to single-element lists
    # This is required to make sure product work.
    for key in param_ranges:
        if not isinstance(param_ranges[key], list):
            param_ranges[key] = [param_ranges[key]]

    return [dict(zip(param_ranges, v)) for v in
            product(*param_ranges.values())]
