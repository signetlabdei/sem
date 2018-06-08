from tinydb import TinyDB, Query
from pathlib import Path
from functools import reduce
from operator import and_, or_
import os


class DatabaseManager(object):
    """
    This class is tasked with interfacing to the simulation campaign database.

    A database can either be created from scratch or loaded, via the new and
    load @classmethods.

    """

    ##################
    # Initialization #
    ##################

    def __init__(self, db):
        """
        Initialize the DatabaseManager with a TinyDB instance.
        """
        self.db = db

    @classmethod
    def new(cls, config, campaign_dir, overwrite=False):
        """
        Initialize a new class instance with a set configuration and filename.

        Args:
            config (dict): A dictionary containing the campaign configuration.
            filename (str): The path of the file where to save the db.
            overwrite (bool): Whether or not existing filenames should be
                overwritten.

        """
        # Create new TinyDB instance

        # We only accept absolute paths
        if not Path(campaign_dir).is_absolute():
            raise ValueError("Path is not absolute")

        # Make sure the directory does not exist already
        if Path(campaign_dir).exists():
            raise FileExistsError("The specified directory already exists")

        # Create the directory
        os.makedirs(campaign_dir)

        tinydb = TinyDB(os.path.join(campaign_dir, "%s.json" %
                                     os.path.basename(campaign_dir)))

        tinydb.table('config').insert(config)

        return cls(tinydb)

    @classmethod
    def load(cls, filename):
        """
        Initialize from an existing database.
        """
        # We only accept absolute paths
        if not Path(filename).is_absolute():
            raise ValueError("Path is not absolute")

        # Verify file exists
        if not Path(filename).exists():
            raise ValueError("File does not exist")

        # Read TinyDB instance from file
        tinydb = TinyDB(filename)

        # Make sure the configuration is a valid dictionary
        if set(tinydb.table('config').all()[0].keys()) != set(['script',
                                                               'path',
                                                               'params',
                                                               'commit']):
            raise ValueError("Existing database is corrupt")

        return cls(tinydb)

    #############
    # Utilities #
    #############

    def __str__(self):
        configuration = self.get_config()
        return "ns-3: %s\nscript: %s\nparams: %s\ncommit: %s" % (
            configuration['path'], configuration['script'],
            configuration['params'], configuration['commit'])

    ###################
    # Database access #
    ###################

    def get_config(self):
        """
        Return the configuration dictionary of this DatabaseManager's campaign
        """

        # Read from self.db and return the config entry of the database
        return self.db.table('config').all()[0]

    def get_path(self):
        return self.get_config()['path']

    def get_data_dir(self):
        """
        Return the data directory, which is simply campaign_directory/data.
        """

        return os.path.join(self.get_config()['campaign_dir'], 'data')

    def get_commit(self):
        return self.get_config()['commit']

    def get_script(self):
        return self.get_config()['script']

    def get_params(self):
        return self.get_config()['params']

    def get_next_rngrun(self):
        if len(self.get_results()):
            return 1+max([result['RngRun'] for result in self.get_results()])
        else:
            return 1

    def insert_result(self, result):
        """
        Insert a new result in the database.

        This function also verifies that the result dictionaries saved in the
        database have the following fields:

        * One key for each available script parameter
        * A RngRun key (with the employed RngRun as a value)
        * A stdout key (with the output of the script as a value)
        """

        # Verify result format is correct
        expected = set(result.keys())
        got = (set(self.get_params()) | set(['RngRun', 'stdout', 'time',
                                             'id']))
        if (expected != got):
            raise ValueError(
                '%s:\nExpected: %s\nGot: %s' % (
                    "Result dictionary does not correspond to database format",
                    expected,
                    got))

        # Insert result
        self.db.table('results').insert(result)

    def get_results(self, params=None):
        """
        Get a list of all results corresponding to the specified parameter
        combination.

        If params is not specified or None, return all results.
        If params is specified, it must be a dictionary specifying the result
        values we are interested in, with multiple values specified as lists.

        For example, if the following params value is used the database will be
        queried for results having key1 equal to value1, and key2 equal to
        value2 or value3::

            params = {
            'key1': 'value1',
            'key2': ['value2', 'value3']
            }

        Returns:
            A list of database results matching the query.
        """

        # In this case, return all results
        if params is None:
            return self.db.table('results').all()

        # Verify parameter format is correct
        all_params = set(self.get_params())
        param_subset = set(params.keys())
        if (not all_params.issuperset(param_subset)):
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

        # Create the TinyDB query
        query = reduce(and_, [reduce(or_, [Query()[key] == v for v in value])
                              for key, value in query_params.items()])

        return self.db.table('results').search(query)

    def wipe_results(self):
        """ Removes all results from the database. """
        self.db.purge_table('results')
