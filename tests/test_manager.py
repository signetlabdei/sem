import sem
import os
import pytest
import numpy as np
import shutil
import git


##################################
# Campaign creation from scratch #
##################################


def test_campaign_creation(ns_3_compiled, config):
    sem.CampaignManager.new(ns_3_compiled, config['script'],
                            config['campaign_dir'])


def test_new_campaign_reload(ns_3_compiled, config, manager, result):
    # Insert a result in the already available sem.CampaignManager
    manager.db.insert_result(result)
    manager.db.write_to_disk()

    # Try creating a new sem.CampaignManager with the same settings
    new_campaign = sem.CampaignManager.new(ns_3_compiled, config['script'],
                                           config['campaign_dir'],
                                           overwrite=False)

    # Result should still be there
    assert new_campaign.db.get_results()[0] == result


def test_new_campaign_reload_fail(ns_3_compiled, config, manager, result):
    # Insert a result in the already available sem.CampaignManager
    manager.db.insert_result(result)

    # Try creating a new sem.CampaignManager with the same settings and
    # different script. This should fail.
    with pytest.raises(FileExistsError):
        sem.CampaignManager.new(ns_3_compiled,
                                'hello-simulator',
                                config['campaign_dir'],
                                overwrite=False)


def test_new_campaign_reload_overwrite(ns_3_compiled, config, manager, result):
    # Insert a result in the already available sem.CampaignManager
    manager.db.insert_result(result)

    # Try creating a new sem.CampaignManager with the same settings
    new_campaign = sem.CampaignManager.new(ns_3_compiled,
                                           config['script'],
                                           config['campaign_dir'],
                                           overwrite=True)

    # There should be no results
    assert len(new_campaign.db.get_results()) == 0


def test_load_campaign(manager, config, parameter_combination):
    # Try loading the campaign that was created as fixture
    loaded_manager = sem.CampaignManager.load(config['campaign_dir'])
    del config['campaign_dir']
    assert loaded_manager.db.get_config() == config
    # This campaign should not be able to run simulations
    with pytest.raises(Exception):
        loaded_manager.run_simulations([parameter_combination])


def test_wrong_parameter_combination(manager, parameter_combination):
    # Try running a parameter combination for which a parameter is missing
    del parameter_combination['time']
    with pytest.raises(ValueError):
        manager.run_simulations([parameter_combination])


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


def test_non_existing_repo(manager, config, ns_3_compiled,
                           parameter_combination):
    # Remove git directory
    shutil.rmtree(os.path.join(ns_3_compiled, '.git'))

    # Try running simulations
    with pytest.raises(Exception):
        manager.run_simulations([parameter_combination])


def test_repo_on_wrong_commit(manager, config, ns_3_compiled,
                              parameter_combination):
    # Check out the previous commit (in detached HEAD state)
    repo = git.Repo(ns_3_compiled)
    repo.create_head('past_branch', 'HEAD~1')
    repo.heads.past_branch.checkout()

    # Try running simulations
    with pytest.raises(Exception):
        manager.run_simulations([parameter_combination])


def test_get_results_as_numpy_array(tmpdir, manager,
                                    parameter_combination_no_rngrun,
                                    parameter_combination,
                                    parameter_combination_2,
                                    parameter_combination_range):
    # Insert a first parameter combination
    manager.run_missing_simulations(parameter_combination_no_rngrun, 1)
    array = manager.get_results_as_numpy_array(
        parameter_combination_no_rngrun,
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

def test_run_logging_simulation(ns_3_compiled_debug,config): 
    params = {
        'backboneNodes': 10,
        'infraNodes': 2,
        'lanNodes': 2,
        'stopTime': 20,
        'useCourseChangeCallback': False
    }
    log_component = {
        'MixedWireless' : 'info'
    }
    new_campaign = sem.CampaignManager.new(ns_3_compiled_debug,
                                            'mixed-wired-wireless',
                                            config['campaign_dir'],
                                            overwrite=True,
                                            optimized=False)

    #Ensure that the simulations run fine                                            
    new_campaign.run_missing_simulations(params,log_component=log_component)                                        

    #Assert the log file generated is correct
