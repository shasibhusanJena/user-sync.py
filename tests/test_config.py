import os
from unittest import mock

import pytest
import yaml
import shutil
from util import update_dict
from user_sync.config import ConfigFileLoader, ConfigLoader, DictConfig
from user_sync import app
from user_sync.error import AssertionException


def load_ldap_config_options(args):
    from user_sync.connector.directory import DirectoryConnector
    from user_sync.connector.directory_ldap import LDAPDirectoryConnector

    config_loader = ConfigLoader(args)
    dc_mod_name = config_loader.get_directory_connector_module_name()
    dc_mod = __import__(dc_mod_name, fromlist=[''])
    dc = DirectoryConnector(dc_mod)
    dc_config_options = config_loader.get_directory_connector_options(dc.name)
    caller_config = DictConfig('%s configuration' % dc.name, dc_config_options)
    return LDAPDirectoryConnector.get_options(caller_config)


@pytest.fixture
def root_config_file(fixture_dir):
    return os.path.join(fixture_dir, 'user-sync-config.yml')


@pytest.fixture
def ldap_config_file(fixture_dir):
    return os.path.join(fixture_dir, 'connector-ldap.yml')


@pytest.fixture
def umapi_config_file(fixture_dir):
    return os.path.join(fixture_dir, 'connector-umapi.yml')


@pytest.fixture
def tmp_config_files(root_config_file, ldap_config_file, umapi_config_file, tmpdir):
    tmpfiles = []
    for fname in [root_config_file, ldap_config_file, umapi_config_file]:
        basename = os.path.split(fname)[-1]
        tmpfile = os.path.join(str(tmpdir), basename)
        shutil.copy(fname, tmpfile)
        tmpfiles.append(tmpfile)
    return tuple(tmpfiles)


@pytest.fixture
def modify_root_config(tmp_config_files):
    (root_config_file, _, _) = tmp_config_files

    def _modify_root_config(keys, val):
        conf = yaml.safe_load(open(root_config_file))
        conf = update_dict(conf, keys, val)
        yaml.dump(conf, open(root_config_file, 'w'))

        return root_config_file

    return _modify_root_config


@pytest.fixture
def modify_ldap_config(tmp_config_files):
    (_, ldap_config_file, _) = tmp_config_files

    def _modify_ldap_config(keys, val):
        conf = yaml.safe_load(open(ldap_config_file))
        conf = update_dict(conf, keys, val)
        yaml.dump(conf, open(ldap_config_file, 'w'))

        return ldap_config_file

    return _modify_ldap_config


def test_load_root(root_config_file):
    """Load root config file and test for presence of root-level keys"""
    config = ConfigFileLoader.load_root_config(root_config_file)
    assert isinstance(config, dict)
    assert ('adobe_users' in config and 'directory_users' in config and
            'logging' in config and 'limits' in config and
            'invocation_defaults' in config)


def test_max_adobe_percentage(modify_root_config, cli_args):
    root_config_file = modify_root_config(['limits', 'max_adobe_only_users'], "50%")
    config = ConfigFileLoader.load_root_config(root_config_file)
    assert ('limits' in config and 'max_adobe_only_users' in config['limits'] and
            config['limits']['max_adobe_only_users'] == "50%")

    args = cli_args({'config_filename': root_config_file})
    options = ConfigLoader(args).get_rule_options()
    assert 'max_adobe_only_users' in options and options['max_adobe_only_users'] == '50%'

    modify_root_config(['limits', 'max_adobe_only_users'], "error%")
    with pytest.raises(AssertionException):
        ConfigLoader(args).get_rule_options()


def test_additional_groups_config(modify_root_config, cli_args):
    addl_groups = [
        {"source": r"ACL-(.+)", "target": r"ACL-Grp-(\1)"},
        {"source": r"(.+)-ACL", "target": r"ACL-Grp-(\1)"},
    ]
    root_config_file = modify_root_config(['directory_users', 'additional_groups'], addl_groups)
    config = ConfigFileLoader.load_root_config(root_config_file)
    assert ('additional_groups' in config['directory_users'] and
            len(config['directory_users']['additional_groups']) == 2)

    args = cli_args({'config_filename': root_config_file})
    options = ConfigLoader(args).get_rule_options()
    assert addl_groups[0]['source'] in options['additional_groups'][0]['source'].pattern
    assert addl_groups[1]['source'] in options['additional_groups'][1]['source'].pattern


def test_twostep_config(tmp_config_files, modify_ldap_config, cli_args):
    (root_config_file, ldap_config_file, _) = tmp_config_files
    modify_ldap_config(['two_steps_lookup'], {})

    args = cli_args({'config_filename': root_config_file})

    # test invalid "two_steps_lookup" config
    with pytest.raises(AssertionException):
        load_ldap_config_options(args)

    # test valid "two_steps_lookup" config with "group_member_filter_format" still set
    modify_ldap_config(['two_steps_lookup', 'group_member_attribute_name'], 'member')
    with pytest.raises(AssertionException):
        load_ldap_config_options(args)

    # test valid "two_steps_lookup" setup
    modify_ldap_config(['two_steps_lookup', 'group_member_attribute_name'], 'member')
    modify_ldap_config(['group_member_filter_format'], "")
    options = load_ldap_config_options(args)
    assert 'two_steps_enabled' in options
    assert 'two_steps_lookup' in options
    assert 'group_member_attribute_name' in options['two_steps_lookup']
    assert options['two_steps_lookup']['group_member_attribute_name'] == 'member'


def test_adobe_users_config(tmp_config_files, modify_root_config, cli_args):
    (root_config_file, _, _) = tmp_config_files
    args = cli_args({'config_filename': root_config_file})

    # test default
    config_loader = ConfigLoader(args)
    options = config_loader.load_invocation_options()
    assert 'adobe_users' in options
    assert options['adobe_users'] == ['all']

    # test default invocation
    modify_root_config(['invocation_defaults', 'adobe_users'], "mapped")
    config_loader = ConfigLoader(args)
    options = config_loader.load_invocation_options()
    assert 'adobe_users' in options
    assert options['adobe_users'] == ['mapped']

    # test command line param
    modify_root_config(['invocation_defaults', 'adobe_users'], "all")
    args = cli_args({'config_filename': root_config_file, 'adobe_users': ['mapped']})
    config_loader = ConfigLoader(args)
    options = config_loader.load_invocation_options()
    assert 'adobe_users' in options
    assert options['adobe_users'] == ['mapped']


def test_get_rule_options_add(tmp_config_files, modify_root_config, cli_args):
    (root_config_file, _, _) = tmp_config_files
    args = cli_args({'config_filename': root_config_file})

    # Modify these values in the root_config file (user-sync-config.yml)
    modify_root_config(['adobe_users', 'exclude_identity_types'], ['adobeID'])
    modify_root_config(['directory_users', 'default_country_code'], "EU")
    modify_root_config(['directory_users', 'user_identity_type'], "enterpriseID")
    modify_root_config(['directory_users', 'additional_groups'], [{'source': 'ACL-(.+)', 'target': 'ACL-Grp-(\\1)'}])
    modify_root_config(['directory_users', 'group_sync_options'], {'auto_create': True})
    modify_root_config(['directory_users', 'groups'], [{'directory_group': 'DIR-1', 'adobe_groups': ['GRP-1']}, {'directory_group': 'DIR-2', 'adobe_groups': ['GRP-2.1', 'GRP-2.2']}])

    # Modify these values to override the default values from default_options (line 40 in rules.py)
    # conftest caller_options does not seem to have an effect on this process
    config_loader = ConfigLoader(args)
    options = config_loader.invocation_options
    options['exclude_adobe_groups'] = ['one', 'two']
    options['exclude_users'] = ['UserA', 'UserB']
    options['directory_group_mapped'] = True
    options['adobe_group_mapped'] = True

    # Run the method and set result as result
    result = config_loader.get_rule_options()

    # Assert the values made it into the options dictionary and are successfully returned
    assert result['new_account_type'] == 'enterpriseID'
    assert result['default_country_code'] == 'EU'
    assert result['additional_groups'][0]['source'].pattern == 'ACL-(.+)'
    assert result['directory_group_filter'] == {'DIR-1', 'DIR-2'}
    assert result['exclude_adobe_groups'] == ['one', 'two']
    assert result['exclude_users'] == ['UserA', 'UserB']

    modify_root_config(['directory_users'], None)
    with pytest.raises(AssertionException) as error:
        config_loader = ConfigLoader(args)
        config_loader.get_rule_options()
    assert "'directory_users' must be specified" in str(error.value)


def test_get_rule_options_exceptions(tmp_config_files, modify_root_config, cli_args):
    (root_config_file, _, _) = tmp_config_files
    args = cli_args({'config_filename': root_config_file})

    # Set an exclude_identity_types to a list with an invalid id type to throw an error
    modify_root_config(['adobe_users', 'exclude_identity_types'], ['adobeID', 'UnknownID'])
    with pytest.raises(AssertionException) as error:
        config_loader = ConfigLoader(args)
        config_loader.get_rule_options()
    assert 'Illegal value in exclude_identity_types: Unrecognized identity type: "UnknownID"' in str(error.value)

    # Reset exclude_identity_types and set additional_groups to an invalid key:value
    modify_root_config(['adobe_users', 'exclude_identity_types'], ['adobeID'])
    modify_root_config(['directory_users', 'additional_groups'], [{'nothing': None}])
    with pytest.raises(AssertionException) as error:
        config_loader = ConfigLoader(args)
        config_loader.get_rule_options()
    assert 'Additional group rule error:' in str(error.value)

    modify_root_config(['directory_users', 'additional_groups'], [{'source': 'ACL-(.+)', 'target': 'ACL-Grp-(\\1)'}])
    modify_root_config(['adobe_users', 'exclude_adobe_groups'], [''])
    with pytest.raises(AssertionException) as error:
        config_loader = ConfigLoader(args)
        config_loader.get_rule_options()
    assert 'Illegal value for exclude_groups in config file:  (Not a legal group name)' in str(error.value)

    # Reset additional groups and set regex to invalid regex pattern
    modify_root_config(['adobe_users', 'exclude_adobe_groups'], ['null'])
    modify_root_config(['adobe_users', 'exclude_users'], ['.***@error.com*.'])
    with pytest.raises(AssertionException) as error:
        config_loader = ConfigLoader(args)
        config_loader.get_rule_options()
    assert 'Illegal regular expression (.***@error.com*.) in exclude_identity_types' in str(error.value)

    # Set directory_users to None
    modify_root_config(['directory_users'], None)
    with pytest.raises(AssertionException) as error:
        config_loader = ConfigLoader(args)
        config_loader.get_rule_options()
    assert "'directory_users' must be specified" in str(error.value)


def test_get_rule_options_regex(tmp_config_files, modify_root_config, cli_args):
    (root_config_file, _, _) = tmp_config_files
    args = cli_args({'config_filename': root_config_file})
    # Set exclude_users to a regex to verify it compiles correctly
    modify_root_config(['adobe_users', 'exclude_users'], ['.*@special.com', "freelancer-[0-9]+.*"])
    config_loader = ConfigLoader(args)
    result = config_loader.get_rule_options()
    assert result['exclude_users'][0].pattern == '\\A.*@special.com\\Z'
    assert result['exclude_users'][1].pattern == '\\Afreelancer-[0-9]+.*\\Z'


def test_get_rule_options_percent(tmp_config_files, modify_root_config, cli_args):
    (root_config_file, _, _) = tmp_config_files
    args = cli_args({'config_filename': root_config_file})
    modify_root_config(['limits', 'max_adobe_only_users'], '101%')
    with pytest.raises(AssertionException) as error:
        config_loader = ConfigLoader(args)
        config_loader.get_rule_options()
    assert 'max_adobe_only_users value must be less or equal than 100%' in str(error.value)



