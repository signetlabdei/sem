import sem
import os
import pytest
import numpy as np


##################################
# Campaign creation from scratch #
##################################


def test_campaign_creation(ns_3_compiled, config):
    sem.CampaignManager.new(ns_3_compiled, config['script'],
                            config['campaign_dir'])


def test_new_campaign_reload(ns_3_compiled, config, manager, result):
    # Insert a result in the already available sem.CampaignManager
    manager.db.insert_result(result)

    # Try creating a new sem.CampaignManager with the same settings
    new_campaign = sem.CampaignManager.new(ns_3_compiled, config['script'],
                                           config['campaign_dir'],
                                           overwrite=False)

    # Result should still be there
    assert new_campaign.db.get_results()[0] == result


def test_new_campaign_reload_overwrite(ns_3_compiled, config, manager, result):
    # Insert a result in the already available sem.CampaignManager
    manager.db.insert_result(result)

    # Try creating a new sem.CampaignManager with the same settings
    new_campaign = sem.CampaignManager.new(ns_3_compiled, config['script'],
                                           config['campaign_dir'], overwrite=True)

    # There should be no results
    assert len(new_campaign.db.get_results()) == 0


def test_load_campaign(manager, config):
    # Try loading the campaign that was created as fixture
    loaded_manager = sem.CampaignManager.load(config['campaign_dir'])
    del config['campaign_dir']
    assert loaded_manager.db.get_config() == config


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


def test_get_results_as_numpy_array(tmpdir, manager, parameter_combination,
                                    parameter_combination_2,
                                    parameter_combination_range):
    # Insert a first parameter combination
    manager.run_missing_simulations(parameter_combination, 1)
    array = manager.get_results_as_numpy_array(
        parameter_combination,
        sem.utils.constant_array_parser, 1)  # Get one run per combination
    assert(np.all(array == sem.utils.constant_array_parser(None)))

    # Insert another run with different parameters
    manager.run_missing_simulations(parameter_combination_range, 2)
    array = manager.get_results_as_numpy_array(
        parameter_combination_range,
        sem.utils.constant_array_parser, 2)  # Get two runs per combination
    # 2 parameters, and we get the first and second runs
    assert(np.all(array[0, 0, 0] == sem.utils.constant_array_parser(None)))


def test_save_to_mat_file(tmpdir, manager, result, parameter_combination):
    mat_file = str(tmpdir.join('results.mat'))
    manager.run_missing_simulations(parameter_combination, 1)
    manager.save_to_mat_file({'time': 'false', 'dict': '/usr/share/dict/web2'},
                             sem.utils.constant_array_parser,
                             mat_file, 1)
    # Just check the file was created
    assert os.path.exists(mat_file)


def test_save_to_folders(tmpdir, manager, result, parameter_combination_range):
    manager.run_missing_simulations(parameter_combination_range, 3)
    manager.save_to_folders(parameter_combination_range,
                            str(tmpdir.join('folder_export')),
                            2)
