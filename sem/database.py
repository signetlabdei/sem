import os
from functools import reduce
import itertools
from operator import and_, or_
from pathlib import Path
from copy import deepcopy
import re
import shutil
import collections
import glob
from pprint import pformat
from tinydb import TinyDB, where
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

REUSE_RNGRUN_VALUES = False

class DatabaseManager(object):
    """
    This serves as an interface with the simulation campaign database.

    A database can either be created from scratch or loaded, via the new and
    load @classmethods.
    """

    ##################
    # Initialization #
    ##################

    def __init__(self, db, campaign_dir):
        """
        Initialize the DatabaseManager with a TinyDB instance.

        This function assumes that the DB is already complete with a config
        entry, as created by the new and load classmethods, and should not be
        called directly. Use the CampaignManager.new() and
        CampaignManager.load() facilities instead.
        """
        self.campaign_dir = campaign_dir
        self.db = db

    @classmethod
    def new(cls, script, commit, params, campaign_dir, overwrite=False):
        """
        Initialize a new class instance with a set configuration and filename.

        The created database has the same name of the campaign directory.

        Args:
            script (str): the ns-3 name of the script that will be used in this
                campaign;
            commit (str): the commit of the ns-3 installation that is used to
                run the simulations.
            params (list): a list of the parameters that can be used on the
                script.
            campaign_dir (str): The path of the file where to save the DB.
            overwrite (bool): Whether or not existing directories should be
                overwritten.

        """

        # We only accept absolute paths
        if not Path(campaign_dir).is_absolute():
            raise ValueError("Path is not absolute")

        # Make sure the directory does not exist already
        if Path(campaign_dir).exists() and not overwrite:
            raise FileExistsError("The specified directory already exists")
        elif Path(campaign_dir).exists() and overwrite:
            # Verify we are not deleting files belonging to the user
            campaign_dir_name = os.path.basename(campaign_dir)
            folder_contents = set(os.listdir(campaign_dir))
            allowed_files = set(
                ['data', '%s.json' % campaign_dir_name] +
                # Allow hidden files (like .DS_STORE in macos)
                [os.path.basename(os.path.normpath(f)) for f in
                 glob.glob(os.path.join(campaign_dir, ".*"))])

            if(not folder_contents.issubset(allowed_files)):
                raise ValueError("The specified directory cannot be overwritten"
                                 " because it contains user files.")
            # This operation destroys data.
            shutil.rmtree(campaign_dir)

        # Create the directory and database file in it
        # The indent and separators ensure the database is human readable.
        os.makedirs(campaign_dir)
        tinydb = TinyDB(os.path.join(campaign_dir, "%s.json" %
                                     os.path.basename(campaign_dir)),
                        storage=CachingMiddleware(JSONStorage))

        # Save the configuration in the database
        config = {
            'script': script,
            'commit': commit,
            'params': params
        }

        tinydb.table('config').insert(config)

        tinydb.storage.flush()

        return cls(tinydb, campaign_dir)

    @classmethod
    def load(cls, campaign_dir):
        """
        Initialize from an existing database.

        It is assumed that the database json file has the same name as its
        containing folder.

        Args:
            campaign_dir (str): The path to the campaign directory.
        """

        # We only accept absolute paths
        if not Path(campaign_dir).is_absolute():
            raise ValueError("Path is not absolute")

        # Verify file exists
        if not Path(campaign_dir).exists():
            raise ValueError("Directory does not exist")

        # Extract filename from campaign dir
        filename = "%s.json" % os.path.split(campaign_dir)[1]
        filepath = os.path.join(campaign_dir, filename)

        try:
            # Read TinyDB instance from file
            tinydb = TinyDB(filepath,
                            storage=CachingMiddleware(JSONStorage))

            # Make sure the configuration is a valid dictionary
            assert set(
                tinydb.table('config').all()[0].keys()) == set(['script',
                                                                'params',
                                                                'commit'])
        except:
            # Remove the database instance created by tinydb
            os.remove(filepath)
            raise ValueError("Specified campaign directory seems corrupt")

        return cls(tinydb, campaign_dir)

    ###################
    # Database access #
    ###################

    def write_to_disk(self):
        self.db.storage.flush()

    def get_config(self):
        """
        Return the configuration dictionary of this DatabaseManager's campaign.

        This is a dictionary containing the following keys:

        * script: the name of the script that is executed in the campaign.
        * params: a list of the command line parameters that can be used on the
          script.
        * commit: the commit at which the campaign is operating.
        """

        # Read from self.db and return the config entry of the database
        return self.db.table('config').all()[0]

    def get_data_dir(self):
        """
        Return the data directory, which is simply campaign_directory/data.
        """
        return os.path.join(self.campaign_dir, 'data')

    def get_commit(self):
        """
        Return the commit at which the campaign is operating.
        """
        return self.get_config()['commit']

    def get_script(self):
        """
        Return the ns-3 script that is run in the campaign.
        """
        return self.get_config()['script']

    def get_params(self):
        """
        Return a list containing the parameters that can be toggled.
        """
        return self.get_config()['params']

    def get_next_rngruns(self):
        """
        Yield the next RngRun values that can be used in this campaign.
        """
        available_runs = [result['params']['RngRun'] for result in
                          self.get_results()]
        yield from DatabaseManager.get_next_values(self, available_runs)

    def insert_results(self, results):

        # This dictionary serves as a model for how the keys in the newly
        # inserted result should be structured.
        example_result = {
            'params': {k: ['...'] for k in list(self.get_params().keys()) + ['RngRun']},
            'meta': {k: ['...'] for k in ['elapsed_time', 'id', 'exitcode']},
        }

        for result in results:
            # Verify result format is correct
            if not(DatabaseManager.have_same_structure(result, example_result)):
                raise ValueError(
                    '%s:\nExpected: %s\nGot: %s' % (
                        "Result dictionary does not correspond to database format",
                        pformat(example_result, depth=2),
                        pformat(result, depth=2)))

        # Insert results
        self.db.table('results').insert_multiple(results)

    def insert_result(self, result):
        """
        Insert a new result in the database.

        This function also verifies that the result dictionaries saved in the
        database have the following structure (with {'a': 1} representing a
        dictionary, 'a' a key and 1 its value)::

            {
                'params': {
                            'param1': value1,
                            'param2': value2,
                            ...
                            'RngRun': value3
                           },
                'meta': {
                          'elapsed_time': value4,
                          'id': value5
                        }
            }

        Where elapsed time is a float representing the seconds the simulation
        execution took, and id is a UUID uniquely identifying the result, and
        which is used to locate the output files in the campaign_dir/data
        folder.
        """

        # This dictionary serves as a model for how the keys in the newly
        # inserted result should be structured.
        example_result = {
            'params': {k: ['...'] for k in list(self.get_params().keys()) +
                       ['RngRun']},
            'meta': {k: ['...'] for k in ['elapsed_time', 'id']},
        }

        # Verify result format is correct
        if not(DatabaseManager.have_same_structure(result, example_result)):
            raise ValueError(
                '%s:\nExpected: %s\nGot: %s' % (
                    "Result dictionary does not correspond to database format",
                    pformat(example_result, depth=1),
                    pformat(result, depth=1)))

        # Insert result
        self.db.table('results').insert(deepcopy(result))

    def get_results(self, params=None, result_id=None):
        """
        Return all the results available from the database that fulfill some
        parameter combinations.

        If params is None (or not specified), return all results.

        If params is specified, it must be a dictionary specifying the result
        values we are interested in, with multiple values specified as lists.

        For example, if the following params value is used::

            params = {
            'param1': 'value1',
            'param2': ['value2', 'value3']
            }

        the database will be queried for results having param1 equal to value1,
        and param2 equal to value2 or value3.

        Not specifying a value for all the available parameters is allowed:
        unspecified parameters are assumed to be 'free', and can take any
        value.

        Returns:
            A list of results matching the query. Returned results have the
            same structure as results inserted with the insert_result method.
        """

        # In this case, return all results
        # A cast to dict is necessary, since self.db.table() contains TinyDB's
        # Document object (which is simply a wrapper for a dictionary, thus the
        # simple cast).
        if result_id is not None:
            return [dict(i) for i in self.db.table('results').all() if
                    i['meta']['id'] == result_id]

        if params is None:
            return [dict(i) for i in self.db.table('results').all()]

        # If we are passed a list of parameter combinations, we concatenate
        # results for the queries corresponding to each dictionary in the list
        if isinstance(params, list):
            return sum([self.get_results(x) for x in params], [])

        # Verify parameter format is correct
        all_params = set(['RngRun'] + list(self.get_params().keys()))
        param_subset = set(params.keys())
        if not all_params.issuperset(param_subset):
            raise ValueError(
                '%s:\nParameters: %s\nQuery: %s' % (
                    'Specified parameter keys do not match database format',
                    all_params,
                    param_subset))

        # Convert values that are not lists into lists to later perform
        # iteration over values more naturally. Perform this on a new
        # dictionary not to modify the original copy.
        query_params = {}
        for key in params:
            if not isinstance(params[key], list):
                query_params[key] = [params[key]]
            else:
                query_params[key] = params[key]

        # Handle case where query params has no keys
        if not query_params.keys():
            return [dict(i) for i in self.db.table('results').all()]

        # Create the TinyDB query
        # In the docstring example above, this is equivalent to:
        # AND(OR(param1 == value1), OR(param2 == value2, param2 == value3))
        query = reduce(and_, [reduce(or_, [
            where('params')[key] == v for v in value]) for key, value in
                              query_params.items()])

        return [dict(i) for i in self.db.table('results').search(query)]

    def get_result_files(self, result):
        """
        Return a dictionary containing filename: filepath values for each
        output file associated with an id.

        Result can be either a result dictionary (e.g., obtained with the
        get_results() method) or a result id.
        """
        if isinstance(result, dict):
            result_id = result['meta']['id']
        else:  # Should already be a string containing the id
            result_id = result

        result_data_dir = os.path.join(self.get_data_dir(), result_id)

        filenames = next(os.walk(result_data_dir))[2]

        filename_path_pairs = [
            (f, os.path.join(self.get_data_dir(), result_id, f))
            for f in filenames]

        return {k: v for k, v in filename_path_pairs}

    def get_complete_results(self, params=None, result_id=None, files_to_load=r'.*'):
        """
        Return available results, analogously to what get_results does, but
        also read the corresponding output files for each result, and
        incorporate them in the result dictionary under the output key, as a
        dictionary of filename: file_contents.

        Args:
          params (dict): parameter specification of the desired parameter
            values, as described in the get_results documentation.

        In other words, results returned by this function will be in the form::

            {
                'params': {
                            'param1': value1,
                            'param2': value2,
                            ...
                            'RngRun': value3
                           },
                'meta': {
                          'elapsed_time': value4,
                          'id': value5
                        }
                'output': {
                            'stdout': stdout_as_string,
                            'stderr': stderr_as_string,
                            'file1': file1_as_string,
                            ...
                          }
            }

        Note that the stdout and stderr entries are always included, even if
        they are empty.
        """

        if result_id is not None:
            results = deepcopy(self.get_results(result_id=result_id))
        else:
            results = deepcopy(self.get_results(params))

        for r in results:
            r['output'] = {}
            available_files = self.get_result_files(r['meta']['id'])
            for name, filepath in available_files.items():
                if ((isinstance(files_to_load, str) and re.search(files_to_load, name)) or
                    (isinstance(files_to_load, list) and name in files_to_load)):
                    with open(filepath, 'r') as file_contents:
                        try:
                            r['output'][name] = file_contents.read()
                        except UnicodeDecodeError:
                            # If this is not decodable, we leave this output alone
                            # (but still insert its name in the result)
                            r['output'][name] = 'RAW'
        return results

    def wipe_results(self):
        """
        Remove all results from the database.

        This also removes all output files, and cannot be undone.
        """
        # Clean results table
        self.db.drop_table('results')
        self.write_to_disk()

        # Get rid of contents of data dir
        map(shutil.rmtree, glob.glob(os.path.join(self.get_data_dir(), '*.*')))

    def delete_result(self, result):
        """
        Remove the specified result from the database, based on its id.
        """
        # Get rid of contents of data dir
        shutil.rmtree(os.path.join(self.get_data_dir(), result['meta']['id']))
        # Remove entry from results table
        self.db.table('results').remove(where('meta')['id'] == result['meta']['id'])
        self.write_to_disk()

    #############
    # Utilities #
    #############

    def __str__(self):
        """
        Represent the database object as a human-readable string.
        """
        configuration = self.get_config()
        return "script: %s\nparams: %s\nHEAD: %s" % (
            configuration['script'], configuration['params'],
            configuration['commit'])

    def get_next_values(self, values_list):
        """
        Given a list of integers, this method yields the lowest integers that
        do not appear in the list.

        >>> import sem
        >>> v = [0, 1, 3, 4]
        >>> sem.DatabaseManager.get_next_values(v)

        [2, 5, 6, ...]
        """
        yield from filter(lambda x: x not in values_list,
                          itertools.count())

    def have_same_structure(d1, d2):
        """
        Given two dictionaries (possibly with other nested dictionaries as
        values), this function checks whether they have the same key structure.

        >>> from sem import DatabaseManager
        >>> d1 = {'a': 1, 'b': 2}
        >>> d2 = {'a': [], 'b': 3}
        >>> d3 = {'a': 4, 'c': 5}
        >>> DatabaseManager.have_same_structure(d1, d2)
        True
        >>> DatabaseManager.have_same_structure(d1, d3)
        False

        >>> d4 = {'a': {'c': 1}, 'b': 2}
        >>> d5 = {'a': {'c': 3}, 'b': 4}
        >>> d6 = {'a': {'c': 5, 'd': 6}, 'b': 7}
        >>> DatabaseManager.have_same_structure(d1, d4)
        False
        >>> DatabaseManager.have_same_structure(d4, d5)
        True
        >>> DatabaseManager.have_same_structure(d4, d6)
        False
        """
        # Keys of this level are the same
        if set(d1.keys()) != set(d2.keys()):
            return False

        # Check nested dictionaries
        for k1, k2 in zip(sorted(d1.keys()), sorted(d2.keys())):
            # If one of the values is a dictionary and the other is not
            if isinstance(d1[k1], dict) != isinstance(d2[k2], dict):
                return False
            # If both are dictionaries, recur
            elif isinstance(d1[k1], dict) and isinstance(d2[k2], dict):
                if not DatabaseManager.have_same_structure(d1[k1], d2[k2]):
                    return False

        return True

    def get_all_values_of_all_params(self):
        """
        Return a dictionary containing all values that are taken by all
        available parameters.

        Always returns the parameter list in alphabetical order.
        """

        values = collections.OrderedDict([[p, []] for p in
                                          sorted(self.get_params())])

        for result in self.get_results():
            for param in self.get_params():
                values[param] += [result['params'][param]]

        sorted_values = collections.OrderedDict([[k,
                                                 sorted(list(set(values[k])))]
                                                 for k in values.keys()])

        for k in sorted_values.keys():
            if sorted_values[k] == []:
                sorted_values[k] = None

        return sorted_values
