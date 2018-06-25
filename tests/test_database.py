from sem import DatabaseManager
import pytest
import os


############
# Fixtures #
############

@pytest.fixture(scope='function')
def db(config):
    """
    Provide a valid database, initialized with an example configuration.
    """
    return DatabaseManager.new(**config)

#################################
# Database creation and loading #
#################################


def test_db_creation_from_scratch(tmpdir, ns_3):
    # Creation through the new method
    config = {
        'script': 'wifi-tcp',
        'path': ns_3,
        'commit': 'whatever',
        'params': ['param1', 'param2'],
        'campaign_dir': os.path.join(tmpdir, 'test_campaign'),
    }
    # This should be ok
    DatabaseManager.new(**config)
    # This should raise FileExistsError because directory already exists
    with pytest.raises(FileExistsError):
        DatabaseManager.new(**config)
    # This should execute no problem because we overwrite the database
    DatabaseManager.new(**config, overwrite=True)


def test_db_loading(config, db, tmpdir):
    # Note that the db fixture initializes a db for us
    # Load the database file
    db = DatabaseManager.load(config['campaign_dir'])

    # Make sure campaign dir is correct
    assert db.campaign_dir == config['campaign_dir']

    # Check for a correctly loaded configuration
    del config['campaign_dir']
    assert db.get_config() == config


#####################
# Utility functions #
#####################


def test_getters(db, tmpdir, config):
    # Saved configuration should not include the campaign directory
    del config['campaign_dir']
    assert db.get_config() == config
    assert db.get_data_dir() == os.path.join(tmpdir, 'test_campaign', 'data')


def test_get_next_rngrun(db):
    # First rngrun of a new campaign should be 1
    assert db.get_next_rngrun() == 1


def test_results(db, result):
    # Test insertion of valid result
    db.insert_result(result)

    # Test insertion of result missing a parameter
    with pytest.raises(ValueError):
        db.insert_result({i: result[i] for i in result if i != 'dict'})

    # Test insertion of result missing any other key
    for k in result.keys():
        with pytest.raises(ValueError):
            db.insert_result({i: result[i] for i in result if i != k})

    # All inserted results are returned by get_results
    assert db.get_results() == [result]

    db.insert_result(result)
    db.insert_result(result)
    db.insert_result(result)

    assert db.get_results() == [result, result, result, result]

    # wipe_results actually empties result list
    db.wipe_results()
    assert db.get_results() == []


def test_get_result_files(manager, parameter_combination):
    manager.run_simulations([parameter_combination])
    assert manager.db.get_result_files(
        manager.db.get_results()[0]['id']).get('stdout') is not None
