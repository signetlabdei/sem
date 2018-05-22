from tinydb import TinyDB, Query
from pathlib import Path


class DatabaseManager(object):
    """
    The class tasked with interfacing to the simulation campaign database.
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
    def new(cls, config, filename, overwrite=False):
        """
        Initialize a new instance with a set filename.
        """
        # Create new TinyDB instance

        # We only accept absolute paths
        if not Path(filename).is_absolute():
            raise ValueError("Path is not absolute")

        # Make sure file does not exist already
        if Path(filename).exists():
            raise FileExistsError

        tinydb = TinyDB(filename)
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
        configuration = self.db.table('config').all()[0]
        return "ns-3 path: %s\nscript: %s\nparams: %s\ncommit: %s" % (
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

    def get_path(self):
        return self.db.table('config').all()[0]['path']

    def get_script(self):
        return self.db.table('config').all()[0]['script']

    def get_results(self, parameters):
        """
        Return the currently available results which correspond to the
        specified parameter space.

        parameters: dictionary containing name-value(s) pairs for each one of
        the available parameters.
        """

    def insert_config(self, config):
        """
        Insert a configuration in the database.
        """

    def insert_result(self, result):
        """
        Insert a new result in the database.
        """
