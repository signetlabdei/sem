from sem import CampaignManager
import os
import pytest


@pytest.fixture(scope='function')
def manager(ns_3_compiled, config):
    return CampaignManager.new(ns_3_compiled, config['script'],
                               config['campaign_dir'])

##################################
# Campaign creation from scratch #
##################################


def test_campaign_creation(ns_3_compiled, config):
    CampaignManager.new(ns_3_compiled, config['script'],
                        config['campaign_dir'])


def test_new_campaign_reload(ns_3_compiled, config, manager, result):
    # Insert a result in the already available CampaignManager
    manager.db.insert_result(result)

    # Try creating a new CampaignManager with the same settings
    new_campaign = CampaignManager.new(ns_3_compiled, config['script'],
                                       config['campaign_dir'], overwrite=False)

    # Result should still be there
    assert new_campaign.db.get_results()[0] == result


def test_new_campaign_reload_overwrite(ns_3_compiled, config, manager, result):
    # Insert a result in the already available CampaignManager
    manager.db.insert_result(result)

    # Try creating a new CampaignManager with the same settings
    new_campaign = CampaignManager.new(ns_3_compiled, config['script'],
                                       config['campaign_dir'], overwrite=True)

    # There should be no results
    assert len(new_campaign.db.get_results()) == 0


def test_load_campaign(manager, config):
    # Try loading the campaign that was created as fixture
    loaded_manager = CampaignManager.load(config['campaign_dir'])
    del config['campaign_dir']
    assert loaded_manager.db.get_config() == config
    # TODO Loading a campaign for which ns-3 is not at the right commit gives
    # an error


def test_check_repo_ok(manager, config, ns_3_compiled):
    # This should execute no problem
    manager.check_repo_ok()
    # Modify a file in the repository
    with open(os.path.join(ns_3_compiled, 'src/core/examples/hash-example.cc'),
              'a') as example:
        example.write('Garbage')
    # Now the same method should raise an exception
    with pytest.raises(Exception):
        manager.check_repo_ok()
