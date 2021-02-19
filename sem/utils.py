import io
import math
import warnings
from itertools import product

import matplotlib.pyplot as plt
import numpy as np
import numpy.core.numeric as nx
import SALib.analyze.sobol
import SALib.sample.saltelli
from ipywidgets import interact

# For log viewing
import copy
import webbrowser
import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
from dash.dependencies import Input, Output, State
pio.renderers.default = "browser"
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

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
        command = "python waf --run \"" + script + " " + " ".join(
            ['--%s=%s' % (param, value) for param, value in
             result['params'].items()]) + "\""
    else:
        command = "python waf --run " + script + " --command-template=\"" +\
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
        [result_parsing_function(campaign.db.get_complete_results(p)[0])
         for p in sem_parameter_list])
    return salib_analyze_function(problem, results)


def interactive_plot(campaign, param_ranges, result_parsing_function, x_axis, runs=None):

    # Average over RngRuns if param_ranges does not contain RngRun
    if runs is not None:
        assert(not param_ranges.get('RngRun'))
        xarray = campaign.get_results_as_xarray(param_ranges,
                                                result_parsing_function,
                                                'Result',
                                                runs).reduce(np.mean, 'runs')
    else:
        assert(param_ranges.get('RngRun'))
        xarray = campaign.get_results_as_xarray(param_ranges,
                                                result_parsing_function,
                                                'Result',
                                                runs=1)

    def plot_line(**kwargs):
        # x goes on the x axis
        # Everything else goes as a parameter
        # plt.xlabel(x_axis)
        plt.ylim([np.min(xarray), np.max(xarray)])
        plt.plot(param_ranges[x_axis],
                 np.array(xarray.sel(**kwargs)).squeeze())

    interact(plot_line, **{k: v for k, v in param_ranges.items() if k != x_axis
                           and len(v) > 1})

def read_log_line(line):
    """
    Read the specified line into an array containing the following fields:
    - Time
    - Context
    - Class
    - Function
    - Arguments
    - Message
    """
    # Using Regex
    # groups = re.findall(r'(.*) (.*) (.*):(.*)\((.*)\)\s?(.*)$', line)
    # return groups[0] if len(groups) and len(groups[0]) == 6 else False

    # Just splitting
    # print(line)
    if line[0] != '+':
        return False
    # The [:-1] removes the newline
    groups = line.rstrip().split(')')
    if len(groups) < 2:
        return False
    groups[0] = groups[0].split('(')
    groups[0][0] = groups[0][0].split(' ')
    groups[0][0][-1].split(':')
    clsfunc = groups[0][0][-1]
    # print(groups)
    try:
        time = float(groups[0][0][0][:-1])
    except ValueError:
        return False
    return {
        'time': time,
        'context': int(groups[0][0][1]),
        'clsfunc': clsfunc,
        'args': groups[0][1].split(", "),
        'msg': groups[1]}

def parse_log(filename):
    """
    Parse the specified filename into a data structure.

    /param filename The name of the file where the log is stored.
    """

    # Create the data structure we will save the log into
    log = []
    current_lineno = 1

    with open(filename) as file_contents:
        for line in file_contents:
            # log.append(line)
            parsed = read_log_line(line)
            if parsed:
                parsed['lineno'] = current_lineno
                parsed['raw'] = line
                log.append(parsed)
            current_lineno += 1

    unique_clsfuncs = sorted({log_entry['clsfunc'] for log_entry in log})
    unique_contexts = sorted({log_entry['context'] for log_entry in log})

    unique_values = {
        'clsfunc': unique_clsfuncs,
        'context': unique_contexts,
    }

    return [unique_values, log]


def parse_and_plot_log(filename):
    print("Parsing log...")
    unique_values, log = parse_log(filename)
    print("Done!")

    # Define the application layout
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    app.layout = html.Div(children=[
        html.H1(children='The ns-3 Log Explorer'),

        html.Button(id='deselect-all-clsfuncs', n_clicks=0, children='Deselect all'),
        html.Button(id='select-all-clsfuncs', n_clicks=0, children='Select all'),

        html.Label('Devices'),
        dcc.Checklist(
            id='selected-contexts',
            options=[{'label': "%s (%s)" % (i, len([j for j in log if j['context'] == i])), 'value': i}
                        for i in unique_values['context']],
            value=[]
        ),
        dcc.Checklist(
            id='selected-clsfuncs',
            options=[{'label': "%s (%s)" % (i, len([j for j in log if j['clsfunc'] == i])), 'value': i}
                        for i in unique_values['clsfunc']],
            value=[]
        ),
        dcc.Input(
            id="message-input",
            type="text",
            placeholder="Log message filter"
        ),
        dcc.Input(
            id="blacklist-message-input",
            type="text",
            placeholder="Message blacklist"
        ),
        dcc.Input(
            id="priority-message-input",
            type="text",
            placeholder="Priority"
        ),
        dcc.RangeSlider(
            id='time-slider',
            min=0,
            max=max([i['time'] for i in log]),
            step=max([i['time'] for i in log])/100,
            value=[0, max([i['time'] for i in log])]
        ),
        html.Button(id='update-plot', n_clicks=0, children='Update plot'),
        dcc.Graph(
            id='example-graph',
            style={'height': 800},
        ),
        # html.Div([html.P('%s %s %s %s %s' % (i['time'], i['context'], i['clsfunc'], i['args'], i['msg'])) for i in log[0:10]]),
    ])


    def jitter_log(log):
        """
        Takes log points that are overlapping on time and scatters them across the context axis.

        /param log The log to jitter
        """
        jittered_log = copy.deepcopy(log)
        for unique_time in {i['time'] for i in jittered_log}:
            # print("Unique time: %s" % unique_time)
            unique_time_items = [item for item in jittered_log if item['time'] ==
                                unique_time]
            for unique_context in {i['context'] for i in unique_time_items}:
                # print("Unique context: %s" % unique_context)
                unique_context_items = [item for item in unique_time_items if
                                        item['context'] == unique_context]
                if len(unique_context_items) > 1:
                    offsets = np.linspace(-0.2, 0.2, len(unique_context_items))
                    for idx, unique_context_item in enumerate(unique_context_items):
                        unique_context_item['context'] += offsets[idx]
        return jittered_log

    # Buttons to select/deselect all functions
    @app.callback([Output('selected-contexts', 'value'), Output('selected-clsfuncs', 'value')],
        [Input('deselect-all-clsfuncs', 'n_clicks_timestamp'),
            Input('select-all-clsfuncs', 'n_clicks_timestamp')])
    def update_functions(n_clicks_timestamp_deselect, n_clicks_timestamp_select):
        if not n_clicks_timestamp_deselect:
            n_clicks_timestamp_deselect = 0
        if not n_clicks_timestamp_select:
            n_clicks_timestamp_select = 0
        if n_clicks_timestamp_deselect >= n_clicks_timestamp_select:
            return ([], [])
        return (unique_values['context'], unique_values['clsfunc'])

    @app.callback(
        Output('example-graph', 'figure'),
        [Input('update-plot', 'n_clicks')],  # This triggers the event
        [State('selected-contexts', 'value'),
         State('selected-clsfuncs', 'value'),
         State('time-slider', 'value'),
         State('message-input', 'value'),
         State('blacklist-message-input', 'value'),
         State('priority-message-input', 'value')])
    def update_figure(n_clicks, selected_contexts, selected_clsfuncs, time_limits, message_input, blacklist_message_input, priority_message_input):
        """
        Update the figure.
        """

        print(selected_contexts)
        print(selected_clsfuncs)
        print("Filtering log...")

        filtered_log = [i for i in log if
                        i['clsfunc'] in selected_clsfuncs
                        and i['context'] in selected_contexts
                        and i['time'] >= time_limits[0]
                        and i['time'] <= time_limits[1]
                        and (message_input in i['msg'] if message_input else True)
                        and (blacklist_message_input not in i['msg'] if blacklist_message_input else True)
                        ]
        print("Done!")

        print("Jittering %s entries..." % len(filtered_log))

        jittered_log = jitter_log(filtered_log)

        print("Plotting %s entries..." % len(jittered_log))

        def is_priority(i):
            if priority_message_input is None:
                return False
            return (priority_message_input.upper().lower() in
                    i['raw'].upper().lower())

        # Plotting
        fig = go.Figure(
            data=go.Scattergl(
                x=[i['time'] for i in jittered_log],
                y=[i['context'] for i in jittered_log],
                marker=dict(
                    size=[16 if is_priority(i) else 10 for i in jittered_log],
                    color=['red' if is_priority(i) else round(i['context']) for i in jittered_log],
                    colorscale='Viridis',
                    opacity=[1 if is_priority(i) else 0.6 for i in jittered_log],
                ),
                mode='lines+markers',
                line=dict(width=0.4),
                hovertext=["%s(%s)</br>%s</br>Line %s" % (i['clsfunc'],
                                                        "</br>".join(i['args']),
                                                        i['msg'],
                                                        i['lineno']) for i in jittered_log]))

        return fig

    print("Running app...")
    app.run_server(debug=True)
