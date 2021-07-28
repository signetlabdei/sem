import os
import time
import re
import warnings

from copy import deepcopy
from pprint import pformat
from operator import and_, or_
from pathlib import Path
from functools import reduce

from tinydb import TinyDB, where, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware


def process_logs(log_file):
    """
    Create a TinyDB instance, parse the log file and insert the logs to a
    TinyDB instance.

    Returns a TinyDB instance containing the logs from the log file and the
    path to where that instance is stored.

    Args:
        log_file (str): Path to where the log file is stored
    """
    if not Path(log_file).exists():
        raise FileNotFoundError("Cannot access file '%s'\n" % log_file)

    logs = parse_logs(log_file)

    data_dir = os.path.join('/tmp/', str(time.strftime("%Y-%m-%d::%H-%M-%S")) + ':logs.json')
    if Path(data_dir).exists():
        raise FileExistsError("File path '%s' already exists" % data_dir)

    db = TinyDB(data_dir,
                storage=CachingMiddleware(JSONStorage))

    insert_logs(logs, db)
    return db, data_dir


def parse_logs(log_file):
    """
    Parse the logs from a log file.

    Return a list of dictionaries with each dictionary having the following
    format:
    dictionary = {
        'time': timestamp,  # float
        'context': context/nodeId,  # str
        'extended_Context': ,   #str
        'component': log component,  # str
        'function': function name,  # str
        'arguments': function arguments,  # str
        'severity_class': log severity class,  # str
        'message': log message  # str
    }
    Note: This function will skip the log lines that do not have the same
          structure as ns-3 logs with prefix level set to prefix_all.

    Args:
        log_file (string): Path to where the log file is stored
    """
    log_list = []

    # Regex for parsing the logs
    # time: Accepts string of form "[+-]'digits.digits's". The number of digits
    #       is variable as user can change time resolution.
    time_re = r'[\+\-]?(?P<time>\d+\.\d+)s '
    # context: Accepts string of form "digits" or "-digits".
    # extended_context: Accepts everything between [] followed by a space. i.e.
    #                   '[Extended Context] '.
    # Note: '.*?' will try to match minimum possible string. Or in other words,
    #       it is a non greedy match.
    context_extended_context_re = r'(?P<context>(?:\d+|-\d+)) (?:\[(?P<extended_context>.*?)\] )?'
    # component: Accepts string of form '[a-zA-Z0-9_]'
    # function: Accepts string of form '[a-zA-Z0-9_]'
    # arguments: Accepts everything between '()'(after function name).
    # Note: '.*?' will try to match minimum possible string. Or in other words,
    #       it is a non greedy match.
    component_function_arguments_re = r'(?P<component>\w+):(?P<function>\w+)\((?P<arguments>.*?)\)'
    # severity_class: Accepts string of form '[a-zA-Z0-9_]'
    # message: Accepts everything after 'severity_class '.
    # Note: '\s*' matches extra spaces if present after severity_class.
    # Note: 'severity_class_message_re' is optional as when
    #       severity_class=function severity_class and message are not present
    #       in the resultant log.
    severity_class_message_re = r'(?:: \[(?P<severity_class>\w+)\s*\] (?P<message>.*))?'

    # Note: '^$' - Ensures that the entire regex matches the entire log line.
    regex = re.compile(r'^' + time_re + context_extended_context_re + component_function_arguments_re + severity_class_message_re + r'$')

    with open(log_file) as f:
        for log in f:
            groups = regex.match(log)

            if groups is None:
                warnings.warn("Log format is not consistent with prefix_all. Skipping log '%s'" % log, RuntimeWarning, stacklevel=2)
                continue

            temp_dict = None
            # Remove trailing whitespaces after message
            message = groups.group('message')
            if message is not None:
                message = message.rstrip()

            # If level is function
            if groups.group('severity_class') is None and groups.group('message') is None:
                temp_dict = {
                    'time': float(groups.group('time')),
                    'context': groups.group('context'),
                    'extended_context': groups.group('extended_context'),
                    'component': groups.group('component'),
                    'function': groups.group('function'),
                    'arguments': groups.group('arguments'),
                    'severity_class': 'FUNCTION',
                    'message': ''
                }
            else:
                temp_dict = {
                    'time': float(groups.group('time')),
                    'context': groups.group('context'),
                    'extended_context': groups.group('extended_context'),
                    'component': groups.group('component'),
                    'function': groups.group('function'),
                    'arguments': groups.group('arguments'),
                    'severity_class': groups.group('severity_class'),
                    'message': message
                }
            log_list.append(temp_dict)

    return log_list


def insert_logs(logs, db):
    """
    Insert the logs in the TinyDB instance passed.

    Note: This function does not return anything.

    Args:
        logs (list): A list of logs to insert in database. Logs are described
                     as a python dict
        db (TinyDB instance): A TinyDB instance where the logs will be inserted.
    """
    if logs == [] or logs is None:
        return

    example_result = {
        k: ['...'] for k in ['time',
                             'context',
                             'component',
                             'extended_context',
                             'function',
                             'arguments',
                             'severity_class',
                             'message']
    }

    for log in logs:
        # Verify log format is correct
        # Only check if the keys are consistent
        if not(set(log.keys()) == set(example_result.keys())):
            raise ValueError(
                '%s:\nExpected: %s\nGot: %s' % (
                    "Log dictionary does not correspond to database format",
                    pformat(example_result, depth=2),
                    pformat(log, depth=2)))

    db.table('logs').insert_multiple(logs)


def wipe_results(db, db_path):
    """
    Remove all logs from the database.

    This also removes all output files, and cannot be undone.

    Note: This function does not return anything.

    Args:
        db (TinyDB instance): A TinyDB instance where the logs are inserted.
        db_path (str): Path to where the TinyDB instance is stored
    """

    # Clean logs table
    db.drop_table('logs')
    db.storage.flush()

    # Get rid of contents of data dir
    try:
        if db_path.lower().endswith('.json'):
            os.remove(db_path)
        else:
            warnings.warn("TinyDB instance is stored in a JSON file. File '%s' will not be removed." % db_path, stacklevel=2)
    except OSError as error:
        print(error)
        print("File path '%s' can not be removed" % db_path)


def filter_logs(db,
                severity_class=None,
                components=None,
                function=None,
                context=None,
                time_begin=None,
                time_end=None):
    """
    Filter the logs stored in the database.

    Filters are applied on context, function name, log severity class and time.
    Additionally the user can also filter each log component based on a
    particular severity class using components dictionary.
    For example, if the user specifies Context = [0, 1] and Function = [A, B]
    the function will output logs in which (context == 0 or context == 1) and
    (function == a or function == b).

    Return a list of logs that satisfy all the passed filters. Each log is
    represented by a dictionary.

    Args:
        db (TinyDB instance): The TinyDB instance contaning the logs to filter.
        context (list, str, int): A list of context based on which the logs
            will be filtered. If only one context is to be provided, then this
            parameter can also be a string or an int.
        function (list, str): A list of function names based on which the logs
            will be filtered. If only one function name is to be provided, then
            this parameter can also be a string.
        time_begin (float, int,  str): Start timestamp (in seconds) of the time
            window.
        time_end (float, int, str): End timestamp (in seconds) of the time window.
        severity_class (list, str): A list of log severity classes based on
            which the logs will be filtered. If only one log severity class is
            to be provided, then this parameter can also be a string.
        components (dict): A dictionary having structure
            {
                components:['class1','class2']
            }
            based on which the logs will be filtered.
    """
    query_final = []

    # Make copies of the arguments passed to avoid modifying the parameters
    # passed by the user.
    severity_class_copy = deepcopy(severity_class)
    components_copy = deepcopy(components)
    function_copy = deepcopy(function)
    context_copy = deepcopy(context)

    # Assert that the passed parameters are of valid type.
    if severity_class_copy is not None:
        if isinstance(severity_class_copy, str):
            severity_class_copy = [severity_class_copy]
        elif isinstance(severity_class_copy, list):
            for cls in severity_class_copy:
                if not isinstance(cls, str):
                    raise TypeError("severity_class can only be a list of string or a string (if only one value is passed).")
        else:
            raise TypeError("severity_class can only be a list of string or a string (if only one value is passed).")

    if components_copy is not None:
        for key, value in components_copy.items():
            if isinstance(value, str):
                components_copy[key] = [value]
            elif isinstance(value, list):
                for val in value:
                    if not isinstance(val, str):
                        raise TypeError("values in components dictionary can only be a list of string or a string (if only one value is passed).")

            else:
                raise TypeError("values in components dictionary can only be a list of string or a string (if only one value is passed).")

    if function_copy is not None:
        if isinstance(function_copy, str):
            function_copy = [function_copy]
        elif isinstance(function_copy, list):
            for func in function_copy:
                if not isinstance(func, str):
                    raise TypeError("function can only be a list of string or a string (if only one value is passed).")

        else:
            raise TypeError("function can only be a list of string or a string (if only one value is passed).")

    if context_copy is not None:
        if isinstance(context_copy, str) or isinstance(context_copy, int):
            context_copy = [str(context_copy)]
        elif isinstance(context_copy, list):
            for ctx in context_copy:
                if not (isinstance(ctx, str) or isinstance(ctx, int)):
                    raise TypeError("context can only be a list of string/integer or a string (if only one value is passed).")

        else:
            raise TypeError("context can only be a list of string/integer or a string (if only one value is passed).")

    if time_begin is not None:
        if not (isinstance(time_begin, float) or isinstance(time_begin, str) or isinstance(time_begin, int)):
            raise TypeError("time_begin can only be a float or a string")

    if time_end is not None:
        if not (isinstance(time_end, float) or isinstance(time_end, str) or isinstance(time_end, int)):
            raise TypeError("time_end can only be a float or a string")

    # Build TinyDB query based on the passed parameters
    if severity_class_copy is not None or components_copy is not None:
        query_list = []
        if severity_class_copy is not None:
            query = reduce(or_, [
                           where('severity_class') == lvl.upper()
                           for lvl in severity_class_copy
                           ])
            query_list.append(query)
        # If components is provided apply the specified log severity classes
        # to the specified log components in addition to the log severity
        # classes passed with 'severity_class'. In other words, log severity
        # classes passed with 'severity_class' is treated as a global filter.
        if components_copy is not None:
            query = reduce(or_, [reduce(or_, [
                    Query().fragment({'component': component,
                                      'severity_class': cls.upper()})
                    for cls in classes])
                    for component, classes in components_copy.items()])
            query_list.append(query)

        query_final.append(reduce(or_, query_list))

    if function_copy is not None:
        query = reduce(or_, [where('function') == fnc for fnc in function_copy])
        query_final.append(query)

    if context_copy is not None:
        query = reduce(or_, [where('context') == str(ctx) for ctx in context_copy])
        query_final.append(query)

    if time_begin is not None:
        query = where('time') >= float(time_begin)
        query_final.append(query)

    if time_end is not None:
        query = where('time') <= float(time_end)
        query_final.append(query)

    if query_final is not None:
        query = reduce(and_, query_final)
        return [dict(i) for i in db.table('logs').search(query)]
    else:
        return []
