import io
import math
import copy
import warnings
from itertools import product
from functools import wraps
from abc import ABC, abstractmethod
from typing import Dict, Any

import matplotlib.pyplot as plt
import numpy as np
import numpy.core.numeric as nx
import SALib.analyze.sobol
import SALib.sample.saltelli

try:
    DRMAA_AVAILABLE = True
    import drmaa
except(RuntimeError):
    DRMAA_AVAILABLE = False

def output_labels(argument):
    def decorator(function):
        function.__dict__["output_labels"] = argument
        @wraps(function)
        def wrapper(*args, **kwargs):
            result = function(*args, **kwargs)
            return result
        return wrapper
    return decorator


def only_load_some_files(argument):
    def decorator(function):
        function.__dict__["files_to_load"] = argument
        @wraps(function)
        def wrapper(*args, **kwargs):
            result = function(*args, **kwargs)
            return result
        return wrapper
    return decorator


def yields_multiple_results(function):
    function.__dict__["yields_multiple_results"] = True
    @wraps(function)
    def wrapper(*args, **kwargs):
        result = function(*args, **kwargs)
        return result
    return wrapper


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
    param_ranges_copy = copy.deepcopy(param_ranges)
    # If we are passed a list, we want to expand each nested specification
    if isinstance(param_ranges_copy, list):
        return sum([list_param_combinations(x) for x in param_ranges_copy], [])
    # If it's a dictionary, we need to make sure lists with 1 item are reduced
    # to the item itself.
    if isinstance(param_ranges_copy, dict):
        # Convert non-list values to single-element lists
        for key, value in param_ranges_copy.items():
            if isinstance(value, list) and len(value) == 1:
                param_ranges_copy[key] = value[0]
    # If it's a dictionary and all items are lists, we need to expand it
    if isinstance(param_ranges_copy, dict):
        for key, value in param_ranges_copy.items():
            if isinstance(value, list):
                # Expand all values that are not functions
                new_dictionaries = []
                for v in value:
                    c = copy.deepcopy(param_ranges_copy)
                    c[key] = [v]
                    new_dictionaries += [c]
                # Iterate again to check
                return list_param_combinations(new_dictionaries)
    # If we get to this point, we have a dictionary and all items have length 1
    # Now it's time to expand the functions.
    if isinstance(param_ranges_copy, dict):
        for key, value in param_ranges_copy.items():
            if callable(value):
                param_ranges_copy[key] = value(param_ranges_copy)
                return list_param_combinations(param_ranges_copy)
    return [param_ranges_copy]


def get_command_from_result(script, result, debug=False):
    """
    Return the command that is needed to obtain a certain result.

    Args:
        params (dict): Dictionary containing parameter: value pairs.
        debug (bool): Whether the command should include the debugging
            template.
    """
    if not debug:
        command = "python3 waf --run \"" + script + " " + " ".join(
            ['--%s=%s' % (param, value) for param, value in
             result['params'].items()]) + "\""
    else:
        command = "python3 waf --run " + script + " --command-template=\"" +\
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

    # By default, if dtype is None, the order Numpy tries to convert a string
    # to a value is: bool, int, float. We don't like this, since it would give
    # us a mixture of integers and doubles in the output, if any integers
    # existed in the data. So, we modify the StringMapper's default mapper to
    # skip the int check and directly convert numbers to floats.
    oldmapper = np.lib._iotools.StringConverter._mapper
    np.lib._iotools.StringConverter._mapper = [(nx.bool_,
                                                np.lib._iotools.str2bool,
                                                False),
                                               (nx.floating, float, nx.nan),
                                               (nx.complexfloating, complex,
                                                nx.nan + 0j),
                                               (nx.longdouble, nx.longdouble,
                                                nx.nan)]

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

    # Here we restore the original mapper, so no side-effects remain.
    np.lib._iotools.StringConverter._mapper = oldmapper

    return parsed


def stdout_automatic_parser(result):
    """
    Try and automatically convert strings formatted as tables into a matrix.

    Under the hood, this function essentially applies the genfromtxt function
    to the stdout.

    Args:
      result (dict): the result to parse.
    """
    np.seterr(all='raise')
    parsed = {}

    # By default, if dtype is None, the order Numpy tries to convert a string
    # to a value is: bool, int, float. We don't like this, since it would give
    # us a mixture of integers and doubles in the output, if any integers
    # existed in the data. So, we modify the StringMapper's default mapper to
    # skip the int check and directly convert numbers to floats.
    oldmapper = np.lib._iotools.StringConverter._mapper
    np.lib._iotools.StringConverter._mapper = [(nx.bool_,
                                                np.lib._iotools.str2bool,
                                                False),
                                               (nx.floating, float, nx.nan),
                                               (nx.complexfloating, complex,
                                                nx.nan + 0j),
                                               (nx.longdouble, nx.longdouble,
                                                nx.nan)]

    file_contents = result['output']['stdout']

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        parsed = np.genfromtxt(io.StringIO(file_contents))

    # Here we restore the original mapper, so no side-effects remain.
    np.lib._iotools.StringConverter._mapper = oldmapper

    return parsed


#################################
# Code for sensitivity analysis #
#################################


def get_bounds(ranges):
    """
    Format bounds for SALib, starting from a dictionary of ranges for each
    parameter. The values for the parameters contained in ranges can be one of
    the following:
    1. A dictionary containing min and max keys, describing a range of possible
    values for the parameter.
    2. A list of allowed values for the parameter.
    """
    bounds = {}
    for i in ranges.items():
        if isinstance(i[1], dict):
            # Defined as range
            bounds[i[0]] = [i[1]['min'], i[1]['max']]
        elif len(i[1]) > 1:
            # Defined as list of possible values
            bounds[i[0]] = [0, len(i[1])]

    return bounds


def salib_param_values_to_params(ranges, values):
    """
    Convert SALib's parameter specification to a SEM-compatible parameter
    specification.
    """
    sem_params = []
    for value in values:
        v_idx = 0
        params = {}
        for rang in ranges.items():
            if isinstance(rang[1], dict):
                # Defined as range, leave as it is
                params[rang[0]] = value[v_idx]
                v_idx += 1
            elif len(rang[1]) > 1:
                # Defined as list of possible values
                params[rang[0]] = ranges[rang[0]][math.floor(value[v_idx])]
                v_idx += 1
            else:
                # Defined as single value
                params[rang[0]] = rang[1][0]
        sem_params.append(params)
    return sem_params


def compute_sensitivity_analysis(
        campaign, result_parsing_function, ranges,
        salib_sample_function=SALib.sample.saltelli.sample,
        salib_analyze_function=SALib.analyze.sobol.analyze,
        samples=100):
    """
    Compute sensitivity analysis on a campaign using the passed SALib sample
    and analyze functions.
    """
    bounds = get_bounds(ranges)

    problem = {
        'num_vars': len(bounds),
        'names': list(bounds.keys()),
        'bounds': list(bounds.values())}
    param_values = salib_sample_function(problem, samples)
    sem_parameter_list = salib_param_values_to_params(ranges, param_values)

    if not bounds.get('RngRun'):
        # If we don't have RngRun parameter specified, we just assign a new
        # value to each combination
        next_runs = campaign.db.get_next_rngruns()
        for p in sem_parameter_list:
            p['RngRun'] = next(next_runs)

    # TODO Make a copy of all available results, search a result for each item
    # in sem_parameter_list, remove the result from the copied list, assign new
    # RngRun value in case we don't find anything.

    campaign.run_missing_simulations(sem_parameter_list)
    results = np.array(
        [result_parsing_function(campaign.db.get_complete_results(p)[0])[0]
         for p in sem_parameter_list])
    return salib_analyze_function(problem, results)


class CallbackBase(ABC):
    """
    Base class for SEM callbacks.
    :param verbose: Verbosity level: 0 for no output, 1 for info messages, 2 for debug messages
    """

    def __init__(self, verbose: int = 0):
        super().__init__()
        # Number of time the callback was called
        self.controlled_by_parent = False  # type: bool
        self.n_runs_over = 0  # type: int
        self.n_runs_over_no_errors = 0  # type: int
        self.n_runs_over_errors = 0  # type: int
        self.n_runs_total = 0  # type: int
        self.run_sim_times = []
        self.verbose = verbose

    def init_callback(self, controlled_by_parent) -> None:
        """
        Initialize the callback.
        """
        self.controlled_by_parent = controlled_by_parent

    def is_controlled_by_parent(self) -> bool:
        """
        Whether this runner is aware of all simulations (false)
        or it has been triggered by a multithread runner and is thus
        aware of a subset of all runs only (true).
        """
        return self.controlled_by_parent

    def on_simulation_start(self, n_runs_total) -> None:
        self.n_runs_total = n_runs_total
        self._on_simulation_start()

    @abstractmethod
    def _on_simulation_start(self) -> None:
        pass

    def on_run_start(self, configuration, sim_uuid) -> None:
        """
        Args:
            configuration (dict): dictionary representing the combination of parameters simulated in this specific
            sim_uuid (str): unique identifier string for the simulation. This value is used to name the result folder,
                            and it is referenced in the result JSON file.
        """
        self._on_run_start(configuration, sim_uuid)

    @abstractmethod
    def _on_run_start(self, configuration: dict, sim_uuid: str) -> None:
        pass

    @abstractmethod
    def _on_run_end(self, sim_uuid: str, return_code: int, sim_time: int) -> bool:
        """
        :return: If the callback returns False, training is aborted early.
        # TODO maybe it does not make a lot of sense since this will be eventually overridden by the callback user
        """
        return True

    def on_run_end(self, sim_uuid: str, return_code: int, sim_time: int) -> bool:
        """
        This method will be called when each simulation run finishes
        # TODO maybe it does not make a lot of sense since this will be eventually overridden by the callback user
        :return: If the callback returns False, a run has failed.
        """
        self.n_runs_over += 1
        self.run_sim_times.append(sim_time)
        if return_code == 0:
            self.n_runs_over_no_errors += 1  # type: int
        else:
            self.n_runs_over_errors += 1  # type: int

        return self._on_run_end(sim_uuid, return_code, sim_time)

    def on_simulation_end(self) -> None:
        self._on_simulation_end()

    @abstractmethod
    def _on_simulation_end(self) -> None:
        pass

# def interactive_plot(campaign, param_ranges, result_parsing_function, x_axis,
#                      runs=None):
#     # Average over RngRuns if param_ranges does not contain RngRun
#     if runs is not None:
#         assert(not param_ranges.get('RngRun'))
#         xarray = campaign.get_results_as_xarray(param_ranges,
#                                                 result_parsing_function,
#                                                 'Result',
#                                                 runs).reduce(np.mean, 'runs')
#     else:
#         assert(param_ranges.get('RngRun'))
#         xarray = campaign.get_results_as_xarray(param_ranges,
#                                                 result_parsing_function,
#                                                 'Result',
#                                                 runs=1)

#     def plot_line(**kwargs):
#         # x goes on the x axis
#         # Everything else goes as a parameter
#         # plt.xlabel(x_axis)
#         plt.ylim([np.min(xarray), np.max(xarray)])
#         plt.plot(param_ranges[x_axis],
#                  np.array(xarray.sel(**kwargs)).squeeze())
#     interact(plot_line, **{k: v for k, v in param_ranges.items() if k != x_axis
#                            and len(v) > 1})
