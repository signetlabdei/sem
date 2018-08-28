from itertools import product
import io
import numpy as np
import warnings

try:
    DRMAA_AVAILABLE = True
    import drmaa
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

    Additionally, this function is robust in case values are not lists:

        >>> param_ranges = {'a': 1, 'b': [2, 3]}
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


def get_command_from_result(script, result, debug=False):
    """
    Return the command that is needed to obtain a certain result.

    Args:
        params (dict): Dictionary containing parameter: value pairs.
        debug (bool): Whether the command should include the debugging
            template.
    """
    if not debug:
        command = "./waf --run \"" + script + " " + " ".join(
            ['--%s=%s' % (param, value) for param, value in
             result['params'].items()]) + "\""
    else:
        command = "./waf --run " + script + " --command-template=\"" +\
            "gdb --args %s " + " ".join(['--%s=%s' % (param, value) for
                                         param, value in
                                         result['params'].items()]) + "\""
    return command


def constant_array_parser(result):
    """
    Dummy parser, used for testing purposes.
    """
    return [0, 1, 2, 3]


def automatic_parser(result, dtypes={}, converters={}):
    """
    Try and automatically convert strings formatted as tables into nested
    list structures.

    Under the hood, this function essentially applies the genfromtxt function
    to all files in the output, and passes it the additional kwargs.

    Args:
      result (dict): the result to parse.
      dtypes (dict): a dictionary containing the dtype specification to perform
        parsing for each available filename. See the numpy genfromtxt
        documentation for more details on how to format these.
    """
    np.seterr(all='raise')
    parsed = {}

    for filename, contents in result['output'].items():
        if dtypes.get(filename) is None:
            dtypes[filename] = None
        if converters.get(filename) is None:
            converters[filename] = None

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            parsed[filename] = np.genfromtxt(io.StringIO(contents),
                                             dtype=dtypes[filename],
                                             converters=converters[filename]
                                             ).tolist()

    return parsed
