import logging

import pytest

from user_sync.config.sign_sync import SignConfigLoader
from user_sync.config.user_sync import DictConfig
from user_sync.engine.common import AdobeGroup
from user_sync.engine.sign import SignSyncEngine
from user_sync.error import AssertionException


def test_loader_attributes(sign_config_file):
    """ensure that initial load of Sign config is correct"""
    args = {'config_filename': sign_config_file}
    config = SignConfigLoader(args)
    assert isinstance(config.logger, logging.Logger)
    assert config.args == args
    assert 'users' in config.invocation_options
    assert 'config_filename' in config.invocation_options
    assert isinstance(config.main_config, DictConfig)


def test_config_structure(sign_config_file):
    """ensure that Sign config test fixture is structured correctly"""
    args = {'config_filename': sign_config_file}
    _ = SignConfigLoader(args)
    # nothing to assert here, if the config object is constructed without exceptions, then the test passes


# NOTE: tmp_sign_connector_config and tmp_config_files are needed to prevent the ConfigFileLoader
# from complaining that there are no temporary sign connector or ldap connector files
def test_invocation_defaults(modify_sign_config, tmp_sign_connector_config, tmp_config_files):
    """ensure that invocation defaults are resolved correctly"""
    sign_config_file = modify_sign_config(['invocation_defaults', 'users'], 'all')
    args = {'config_filename': sign_config_file}
    config = SignConfigLoader(args)
    assert 'users' in config.invocation_options
    assert config.invocation_options['users'] == ['all']
    args = {'config_filename': sign_config_file, 'users': ['mapped']}
    config = SignConfigLoader(args)
    assert 'users' in config.invocation_options
    assert config.invocation_options['users'] == ['mapped']


# NOTE: tmp_sign_connector_config and tmp_config_files are needed to prevent the ConfigFileLoader
# from complaining that there are no temporary sign connector or ldap connector files
def test_group_config(modify_sign_config, tmp_sign_connector_config, tmp_config_files):

    def load_sign_groups(group_config):
        sign_config_file = modify_sign_config(['user_management'], group_config)
        args = {'config_filename': sign_config_file}
        config = SignConfigLoader(args)
        return config.get_directory_groups()

    def check_mapping(mappings, name, priority, roles, sign_groups):
        assert name in mappings
        assert mappings[name]['priority'] == priority
        for r in roles:
            assert r in mappings[name]['roles']
        for g in sign_groups:
            assert AdobeGroup.create(g) in mappings[name]['groups']

    group_config = [
        {'directory_group': 'Test Group 1', 'sign_group': 'Sign Group 1'},
        {'directory_group': 'Test Group Admins 1', 'sign_group': None, 'group_admin': True, 'account_admin': False}
    ]
    group_mappings = load_sign_groups(group_config)
    check_mapping(group_mappings, 'Test Group 1', 0, [], ['Sign Group 1'])
    check_mapping(group_mappings, 'Test Group Admins 1', 1, ['GROUP_ADMIN'], [])

    group_config = [
        {'directory_group': 'Test Group Admins 1', 'sign_group': None, 'group_admin': True},
    ]
    group_mappings = load_sign_groups(group_config)
    check_mapping(group_mappings, 'Test Group Admins 1', 0, ['GROUP_ADMIN'], [])

    group_config = [
        {'directory_group': 'Test Group 1', 'sign_group': 'Sign Group 1', 'group_admin': True},
        {'directory_group': 'Test Group 1', 'sign_group': 'Sign Group 1', 'account_admin': True}
    ]
    group_mappings = load_sign_groups(group_config)
    check_mapping(group_mappings, 'Test Group 1', 0, ['GROUP_ADMIN', 'ACCOUNT_ADMIN'], ['Sign Group 1'])

    group_config = [
        {'directory_group': 'Test Group 1', 'sign_group': 'Sign Group 1'},
        {'directory_group': 'Test Group 2', 'sign_group': 'Sign Group 1'},
        {'directory_group': 'Test Group 2', 'sign_group': None, 'group_admin': True},
        {'directory_group': 'Test Group 2', 'sign_group': None, 'account_admin': True},
        {'directory_group': 'Test Group Admins 2', 'sign_group': None, 'account_admin': True}
    ]
    group_mappings = load_sign_groups(group_config)
    check_mapping(group_mappings, 'Test Group 1', 0, [], ['Sign Group 1'])
    check_mapping(group_mappings, 'Test Group 2', 1, ['GROUP_ADMIN', 'ACCOUNT_ADMIN'], ['Sign Group 1'])
    check_mapping(group_mappings, 'Test Group Admins 2', 4, ['ACCOUNT_ADMIN'], [])

    group_config = [
        {'directory_group': 'Test Group 1'},
        {'directory_group': 'Test Group 2', 'sign_group': 'Sign Group 1'},
        {'directory_group': 'Test Group 1', 'sign_group': 'Sign Group 2'},
        {'directory_group': 'Test Group 2', 'sign_group': 'Sign Group 2'},
    ]
    group_mappings = load_sign_groups(group_config)
    check_mapping(group_mappings, 'Test Group 1', 0, [], ['Sign Group 2'])
    check_mapping(group_mappings, 'Test Group 2', 1, [], ['Sign Group 1', 'Sign Group 2'])


# NOTE: tmp_sign_connector_config and tmp_config_files are needed to prevent the ConfigFileLoader
# from complaining that there are no temporary sign connector or ldap connector files
def test_identity_module(sign_config_file, modify_sign_config, tmp_sign_connector_config, tmp_config_files):
    """ensure directory module name is correct"""
    args = {'config_filename': sign_config_file}
    config = SignConfigLoader(args)
    assert config.get_directory_connector_module_name() == 'user_sync.connector.directory_ldap'

    sign_config_file = modify_sign_config(['identity_source', 'type'], 'okta')
    args = {'config_filename': sign_config_file}
    config = SignConfigLoader(args)
    assert config.get_directory_connector_module_name() == 'user_sync.connector.directory_okta'


def test_identity_connector_options(sign_config_file):
    """ensure sign connector options are retrieved from Sign config handler"""
    options = {'username': 'ldapuser@example.com', 'password': 'password', 'host': 'ldap://host', 'base_dn': 'DC=example,DC=com', 'search_page_size': 200,
               'require_tls_cert': False, 'all_users_filter': '(&(objectClass=user)(objectCategory=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))',
               'group_filter_format': '(&(|(objectCategory=group)(objectClass=groupOfNames)(objectClass=posixGroup))(cn={group}))',
               'group_member_filter_format': '(memberOf={group_dn})', 'user_email_format': '{mail}'}
    args = {'config_filename': sign_config_file}
    config = SignConfigLoader(args)
    assert config.get_directory_connector_options('ldap') == options

    with pytest.raises(AssertionException):
        config.get_directory_connector_options('okta')


# NOTE: tmp_sign_connector_config and tmp_config_files are needed to prevent the ConfigFileLoader
# from complaining that there are no temporary sign connector or ldap connector files
def test_target_config_options(sign_config_file, modify_sign_config, tmp_sign_connector_config, tmp_config_files):
    """ensure directory module name is correct"""
    # simple case
    args = {'config_filename': sign_config_file}
    config = SignConfigLoader(args)
    primary_options, _ = config.get_target_options()
    assert primary_options['host'] == 'api.echosignstage.com'
    assert primary_options['integration_key'] == '[Sign API Key]'
    assert primary_options['admin_email'] == 'user@example.com'

    # complex case
    sign_config_file = modify_sign_config(['sign_orgs'], {'primary': 'connector-sign.yml', 'org2': 'connector-sign.yml'})
    args = {'config_filename': sign_config_file}
    config = SignConfigLoader(args)
    primary_options, secondary_options = config.get_target_options()
    assert 'org2' in secondary_options
    assert secondary_options['org2']['host'] == 'api.echosignstage.com'
    assert secondary_options['org2']['integration_key'] == '[Sign API Key]'
    assert secondary_options['org2']['admin_email'] == 'user@example.com'

    # invalid case
    sign_config_file = modify_sign_config(['sign_orgs'], {'org1': 'connector-sign.yml'})
    args = {'config_filename': sign_config_file}
    config = SignConfigLoader(args)
    # 'sign_orgs' must specify a config with the key 'primary'
    with pytest.raises(AssertionException):
        config.get_target_options()


def test_logging_config(sign_config_file):
    args = {'config_filename': sign_config_file}
    config = SignConfigLoader(args)
    logging_config = config.get_logging_config()
    assert logging_config.get_bool('log_to_file') is True
    assert logging_config.get_string('file_log_directory').endswith('sign_logs')
    assert logging_config.get_string('file_log_name_format') == '{:%Y-%m-%d}-sign.log'
    assert logging_config.get_string('file_log_level') == 'info'
    assert logging_config.get_string('console_log_level') == 'debug'


def test_engine_options(sign_config_file, modify_sign_config, tmp_sign_connector_config, tmp_config_files):
    sign_config_file = modify_sign_config(['user_sync'], {'sign_only_limit': 1000})
    args = {'config_filename': sign_config_file}
    config = SignConfigLoader(args)
    options = config.get_engine_options()
    # ensure rule options dict is initialized from default_options
    for k in SignSyncEngine.default_options:
        assert k in options
    # ensure rule options dict is updated with invocation_options
    for k in config.invocation_options:
        assert k in options
    # ensure that we didn't accidentally introduce any new keys in get_engine_options()
    assert not (set(SignSyncEngine.default_options.keys()) | set(config.invocation_options.keys())) - set(options.keys())
    assert options['create_users'] == False
    assert options['sign_only_limit'] == 1000


def test_load_invocation_options(sign_config_file, modify_sign_config, tmp_sign_connector_config, tmp_config_files):
    sign_config_file = modify_sign_config(['invocation_defaults'], {'users': 'mapped', 'test_mode': False})
    args = {'config_filename': sign_config_file}
    config = SignConfigLoader(args)
    options = config.load_invocation_options()
    assert options['directory_group_mapped'] is True

