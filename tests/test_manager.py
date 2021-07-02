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
    manager.db.insert_results([result])
    manager.db.write_to_disk()

    # Try creating a new sem.CampaignManager with the same settings
    new_campaign = sem.CampaignManager.new(ns_3_compiled, config['script'],
                                           config['campaign_dir'],
                                           overwrite=False)

    # Result should still be there
    assert new_campaign.db.get_results()[0] == result


def test_new_campaign_reload_fail(ns_3_compiled, config, manager, result):
    # Insert a result in the already available sem.CampaignManager
    manager.db.insert_results([result])

    # Try creating a new sem.CampaignManager with the same settings and
    # different script. This should fail.
    with pytest.raises(FileExistsError):
        sem.CampaignManager.new(ns_3_compiled,
                                'hello-simulator',
                                config['campaign_dir'],
                                overwrite=False)


def test_new_campaign_reload_overwrite(ns_3_compiled, config, manager, result):
    # Insert a result in the already available sem.CampaignManager
    manager.db.insert_results([result])

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
    manager.run_missing_simulations(parameter_combination)
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


def test_run_logging_simulation(ns_3_compiled_debug, config):
    log_components = {
        'Logger': 'all'
    }
    # This should raise an exception as the campaign in built in optimized
    # mode and logging is enabled
    new_campaign = sem.CampaignManager.new(ns_3_compiled_debug,
                                           'logging-ns3-script',
                                           config['campaign_dir'],
                                           overwrite=True)

    with pytest.raises(Exception):
        log_path = new_campaign.run_missing_simulations({},
                                                        runs=1,
                                                        log_components=log_components)   

    new_campaign = sem.CampaignManager.new(ns_3_compiled_debug,
                                           'logging-ns3-script',
                                           config['campaign_dir'],
                                           overwrite=True,
                                           optimized=False)

    # This should run fine as the campaign in built in debug mode and logging
    # is enabled
    log_path = new_campaign.run_missing_simulations({},
                                                    runs=1,
                                                    log_components=log_components)

    # Assert log_path list contains exctly one entry as only one parameter
    # combination is passed
    assert len(log_path) == 1

    # Assert the log file generated is correct

    sample_logs = ['+0.000000000s -1 Logger:main(): [DEBUG] Debug',
                   '+0.000000000s -1 Logger:main(): [INFO ] Info',
                   '+0.000000000s -1 Logger:main(): [WARN ] Warn',
                   '+0.000000000s -1 Logger:main(): [ERROR] Error',
                   '+0.000000000s -1 Logger:main(): [LOGIC] Logic',
                   '+0.000000000s -1 Logger:main("Function")'
                   ]

    with open(log_path[0]) as f:
        logs = f.readlines()
    actual_logs = [x.strip() for x in logs]

    assert (sample_logs == actual_logs)


def test_only_load_some_files_decorator(tmpdir, manager, result, parameter_combination_no_rngrun):
    def parsing_function(result):
        assert len(result['output'].keys()) == 2
        return [0]

    # Insert a first parameter combination
    manager.run_missing_simulations(parameter_combination_no_rngrun, 1)
    dataframe = manager.get_results_as_dataframe(
        parsing_function,
        columns=['Label'],
        params=parameter_combination_no_rngrun,
        runs=1)  # Get one run per combination

    @sem.utils.only_load_some_files(['stdout'])
    def decorated_parsing_function(result):
        assert list(result['output'].keys()) == ['stdout']
        return [0]

    dataframe = manager.get_results_as_dataframe(
        decorated_parsing_function,
        columns=['Label'],
        params=parameter_combination_no_rngrun,
        runs=1)  # Get one run per combination

    @sem.utils.only_load_some_files(r'.*err')
    def another_decorated_parsing_function(result):
        assert list(result['output'].keys()) == ['stderr']
        return [0]

    dataframe = manager.get_results_as_dataframe(
        another_decorated_parsing_function,
        columns=['Label'],
        params=parameter_combination_no_rngrun,
        runs=1)  # Get one run per combination

    @sem.utils.only_load_some_files(['stderr', 'garbage'])
    def yet_another_decorated_parsing_function(result):
        assert list(result['output'].keys()) == ['stderr']
        return [0]

    dataframe = manager.get_results_as_dataframe(
        yet_another_decorated_parsing_function,
        columns=['Label'],
        params=parameter_combination_no_rngrun,
        runs=1)  # Get one run per combination


def test_convert_str_to_dict(manager):
    # Valid examples along with wildcards
    env_variable = 'NS_LOG="***"'
    log_components = sem.convert_environment_str_to_dict(env_variable)
    assert(log_components == {
        '*': 'all'
    })

    env_variable = 'NS_LOG="*=**"'
    log_components = sem.convert_environment_str_to_dict(env_variable)
    assert(log_components == {
        '*': '**'
    })

    env_variable = 'NS_LOG="*=*|*"'
    log_components = sem.convert_environment_str_to_dict(env_variable)
    assert(log_components == {
        '*': '*|*'
    })

    env_variable = 'NS_LOG="*=all|*"'
    log_components = sem.convert_environment_str_to_dict(env_variable)
    assert(log_components == {
        '*': 'all|*'
    })

    env_variable = 'NS_LOG="*=level_all|*"'
    log_components = sem.convert_environment_str_to_dict(env_variable)
    assert(log_components == {
        '*': 'level_all|*'
    })

    env_variable = 'NS_LOG="*=*|all"'
    log_components = sem.convert_environment_str_to_dict(env_variable)
    assert(log_components == {
        '*': '*|all'
    })

    env_variable = 'NS_LOG="*=*|prefix_all"'
    log_components = sem.convert_environment_str_to_dict(env_variable)
    assert(log_components == {
        '*': '*|prefix_all'
    })

    env_variable = 'NS_LOG="component"'
    log_components = sem.convert_environment_str_to_dict(env_variable)
    assert(log_components == {
        'component': 'all'
    })

    # Invalid examples

    env_variable = 'NS_LOG="component="'
    with pytest.raises(ValueError):
        log_components = sem.convert_environment_str_to_dict(env_variable)

    env_variable = 'NS_LOG="*=*|***"'
    with pytest.raises(ValueError):
        log_components = sem.convert_environment_str_to_dict(env_variable)

    env_variable = 'NS_LOG="component=info=warn"'
    with pytest.raises(ValueError):
        log_components = sem.convert_environment_str_to_dict(env_variable)

    env_variable = 'NS_LOG="NetDevice=**;Simulator:Node=level_info-prefix_time"'
    with pytest.raises(ValueError):
        log_components = sem.convert_environment_str_to_dict(env_variable)
