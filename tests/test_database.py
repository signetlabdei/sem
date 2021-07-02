from sem import DatabaseManager
import pytest
import os
from copy import deepcopy
import itertools


############
# Fixtures #
############

@pytest.fixture(scope='function')
def db(config):
    """
    Provide a valid database, initialized with an example configuration.
    """
    db = DatabaseManager.new(**config)
    return db

#################################
# Database creation and loading #
#################################


def test_db_creation_from_scratch(tmpdir, config, ns_3):
    # This should be ok
    DatabaseManager.new(**config)
    # This should raise FileExistsError because directory already exists
    with pytest.raises(FileExistsError):
        DatabaseManager.new(**config)
    # This should execute no problem because we overwrite the database
    config['overwrite'] = True
    DatabaseManager.new(**config)


def test_db_loading(config, db, tmpdir):
    campaign_path = config['campaign_dir']

    # Note that the db fixture initializes a db for us
    # Load the database file
    db = DatabaseManager.load(config['campaign_dir'])

    # Make sure campaign dir is correct
    assert db.campaign_dir == config['campaign_dir']

    # Check for a correctly loaded configuration
    del config['campaign_dir']
    assert db.get_config() == config

    # Modify the campaign database, removing an entry
    db.db.drop_table('config')
    db.db.storage.flush()

    # Wrong database format is currently detected
    with pytest.raises(Exception):
        DatabaseManager.load(campaign_path)


def test_db_does_not_delete_user_data(config, db, tmpdir):
    # Add a file to the test_campaign folder
    with open(
            os.path.join(
                config['campaign_dir'],
                'precious_file.txt'),
            'a') as my_file:
        my_file.write("Precious content")

    # Try creating another database overwriting this one
    config['overwrite'] = True
    with pytest.raises(Exception):
        DatabaseManager.new(**config)


def test_exception_throwing(config, db):
    with pytest.raises(ValueError):
        DatabaseManager.load('./non_absolute_path')
    with pytest.raises(ValueError):
        DatabaseManager.load('/abs/path/to/non/existing/file')
    with pytest.raises(ValueError):
        config['campaign_dir'] = './non_absolute_path'
        DatabaseManager.new(**config)

#####################
# Utility functions #
#####################


def test_getters(db, tmpdir, config):
    # Saved configuration should not include the campaign directory
    del config['campaign_dir']
    assert db.get_config() == config
    assert db.get_data_dir() == str(tmpdir.join('test_campaign', 'data'))


def test_get_next_rngruns(db, result):
    # First rngrun of a new campaign should be 0
    assert next(db.get_next_rngruns()) == 0

    # If we add a result with RngRun 2, this should still return a 0
    result['params']['RngRun'] = 2
    db.insert_results([result])
    assert next(db.get_next_rngruns()) == 0

    # After inserting a run with index 0, we still expect a 1
    result['params']['RngRun'] = 0
    db.insert_results([result])
    assert next(db.get_next_rngruns()) == 1

    # Finally, if we ask for three more available runs, this should return
    # [1, 3, 4]
    assert list(itertools.islice(db.get_next_rngruns(), 3)) == [1, 3, 4]


def test_results(db, result):
    # Test insertion of valid result
    db.insert_results([result])

    # Test insertion of result missing a parameter
    with pytest.raises(ValueError):
        nonvalid_result = deepcopy(result)
        nonvalid_result['params'].pop('dict')
        db.insert_results([nonvalid_result])

    # Test insertion of result missing any other key
    for k in result.keys():
        with pytest.raises(ValueError):
            db.insert_results([{i: result[i] for i in result.keys()
                                if i != k}])

    # All inserted results are returned by get_results
    assert list(db.get_results()) == [result]

    db.insert_results([result])
    db.insert_results([result])
    db.insert_results([result])

    assert list(db.get_results()) == [result, result, result, result]

    # Ask for a non-existing parameter
    with pytest.raises(ValueError):
        list(db.get_results({'non-existing': 0}))

    # An empty dictionary returns all results
    assert list(db.get_results({})) == [result, result, result, result]

    # wipe_results actually empties result list
    db.wipe_results()
    assert list(db.get_results()) == []

    # Insert a valid non-logging result
    db.insert_results([result])
    db.insert_results([result])
    log_components = {
        'component1': 'level_info',
    }
    result['meta']['log_components'] = log_components

    # Insert a valid logging result
    db.insert_results([result])

    # This should return only the logging result
    assert list(db.get_results(log_components=log_components)) == [result]

    # This should also return the logging result as level_info is same as
    # info|error|warn|debug
    assert list(db.get_results(log_components={'component1': 'info|error|warn|debug'})) == [result]

    # This should return an empty list as there are no results that match the
    # provided log_components
    assert not list(db.get_results(log_components={'component1': 'logic'}))

    result['meta']['log_components'] = None
    # This should return all the non-logging results
    assert list(db.get_results()) == [result, result]


def test_results_queries(db, result):
    # Insert multiple runs for a set parameter combination
    first_round_of_results = []
    for runIdx in range(10):
        result['params']['RngRun'] = runIdx
        first_round_of_results.append(result)
        db.insert_results([result])

    # Query should return the previously saved results
    results = list(db.get_results())
    assert len(results) == 10
    assert sorted([d['params']['RngRun'] for d in results]) == list(range(10))

    # Insert other runs for a different parameter combination
    result['params']['dict'] = '/usr/share/dict/web2a'
    for runIdx in range(10, 20, 1):
        result['params']['RngRun'] = runIdx
        db.insert_results([result])

    # This query should return all results
    results = list(db.get_results({'dict': ['/usr/share/dict/web2a',
                                            '/usr/share/dict/web2']}))
    assert len(results) == 20
    assert sorted([d['params']['RngRun'] for d in results]) == list(range(20))

    # This one should only return the second batch
    results = list(db.get_results({'dict': ['/usr/share/dict/web2a']}))
    assert len(results) == 10
    assert sorted([d['params']['RngRun'] for d in results]) == list(range(10,
                                                                          20,
                                                                          1))

    # result['params']['dict'] = '/usr/share/dict/web2b'
    result['meta']['log_components'] = {'Hasher': 'debug'}
    for runIdx in range(20, 30, 1):
        result['params']['RngRun'] = runIdx
        db.insert_results([result])

    result['meta']['log_components'] = {'HasherB': 'info'}
    for runIdx in range(30, 40, 1):
        result['params']['RngRun'] = runIdx
        db.insert_results([result])

    result['meta']['log_components'] = {'Hasher': 'debug',
                                       'HasherB': 'info'}
    for runIdx in range(40, 50, 1):
        result['params']['RngRun'] = runIdx
        db.insert_results([result])

    # This query should return all results except the last three batches
    results = list(db.get_results({'dict': ['/usr/share/dict/web2a',
                                            '/usr/share/dict/web2']}))
    assert len(results) == 20
    assert sorted([d['params']['RngRun'] for d in results]) == list(range(20))

    # This query should return all results where logging is enabled
    results = list(db.get_results({'dict': ['/usr/share/dict/web2a',
                                            '/usr/share/dict/web2']},
                                  log_components={}))
    assert len(results) == 30
    assert sorted([d['params']['RngRun'] for d in results]) == list(range(20,
                                                                          50,
                                                                          1))

    # This query should only return the third batch
    results = list(db.get_results({'dict': ['/usr/share/dict/web2a']},
                                  log_components='NS_LOG="HasherB=info"'))
    assert len(results) == 20
    assert sorted([d['params']['RngRun'] for d in results]) == list(range(30,
                                                                          50,
                                                                          1))

    # This query should not return any match
    results = list(db.get_results({'dict': ['/usr/share/dict/web2a']},
                                  log_components={'Hasher': 'info',
                                                 'HasherB': 'info'}))
    assert len(results) == 0


def test_get_complete_results(manager, parameter_combination):
    manager.run_simulations([parameter_combination], show_progress=False)
    assert manager.db.get_complete_results()[0].get('output').get('stdout') is not None
    # Try getting complete results via id
    result = manager.db.get_complete_results()[0]
    result_id = result['meta']['id']
    assert manager.db.get_complete_results(
        result_id=result_id)[0].get('output').get('stdout') is not None


def test_get_result_files(manager, parameter_combination):
    manager.run_simulations([parameter_combination], show_progress=False)
    # Try querying result files via id
    result = manager.db.get_complete_results()[0]
    result_id = result['meta']['id']
    assert manager.db.get_result_files(result_id) is not None

    # Try querying with a wrong data structure
    with pytest.raises(Exception):
        manager.db.get_result_files(['stuff', 'other_stuff'])


def test_have_same_structure():
    d1 = {'a': 1, 'b': 2}
    d2 = {'a': [], 'b': 3}
    d3 = {'a': 4, 'c': 5}
    assert DatabaseManager.have_same_structure(d1, d2) is True
    assert DatabaseManager.have_same_structure(d1, d3) is False

    d4 = {'a': {'c': 1}, 'b': 2}
    d5 = {'a': {'c': 3}, 'b': 4}
    d6 = {'a': {'c': 5, 'd': 6}, 'b': 7}
    assert DatabaseManager.have_same_structure(d1, d4) is False
    assert DatabaseManager.have_same_structure(d4, d5) is True
    assert DatabaseManager.have_same_structure(d4, d6) is False
