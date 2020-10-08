import pytest
import six

from user_sync.config.sign_sync import SignConfigLoader
from user_sync.connector.directory import DirectoryConnector
from user_sync.engine.sign import SignSyncEngine
from user_sync.connector.connector_sign import SignConnector
import logging


@pytest.fixture
def example_engine(sign_config_file):
    args = {'config_filename': sign_config_file}
    config = SignConfigLoader(args)
    rule_config = config.get_engine_options()
    return SignSyncEngine(rule_config)


def test_load_users_and_groups(example_engine, example_user):
    dc = DirectoryConnector

    user = {'user@example.com': example_user}

    def dir_user_replacement(groups, extended_attributes, all_users):
        return six.itervalues(user)

    dc.load_users_and_groups = dir_user_replacement
    example_engine.read_desired_user_groups({'directory_group': 'adobe_group'}, dc)
    # if the user has an email attribute, the method will index the user dict by email, which is how it's passed
    # in in this test anyway
    assert example_engine.directory_user_by_user_key == user


def test_get_directory_user_key(example_engine, example_user):
    # user = {'user@example.com': example_user}
    # if the method is passed a dict with an email, it should return the email key
    assert example_engine.get_directory_user_key(example_user) == example_user['email']
    # if the user object passed in has no email value, it should return None
    assert example_engine.get_directory_user_key({'': {'username': 'user@example.com'}}) is None


# def test_insert_new_users(example_user):
#     sign_engine = SignSyncEngine
#     sign_connector = SignConnector
#     umapi_user = example_user
#     user_roles = ['NORMAL_USER']
#     group_id = 'somemumbojumbohexadecimalstring'
#     assignment_group = 'default group'
#     insert_data = {
#             "email": umapi_user['email'],
#             "firstName": umapi_user['firstname'],
#             "groupId": group_id,
#             "lastName": umapi_user['lastname'],
#             "roles": user_roles,
#         }
#     def insert_user(insert_data):
#         pass
#     sign_connector.insert_user = insert_user
#     sign_engine.logger = logging.getLogger()
#     sign_engine.insert_new_users(sign_engine, sign_connector, umapi_user, user_roles, group_id, assignment_group)
#     assert True
#     assert insert_data['email'] == 'user@example.com'

def test_deactivate_sign_users(example_user):
    sign_engine = SignSyncEngine
    sign_connector = SignConnector
    directory_users = {}
    directory_users['federatedID, example.user@signtest.com'] = {'email': 'example.user@signtest.com'}
    sign_users = {}
    sign_users['example.user@signtest.com'] = {'email':'example.user@signtest.com','userId':'somerandomhexstring'}
    def get_users():
        return sign_users
    def deactivate_user(insert_data):
        pass
    sign_connector.deactivate_user = deactivate_user
    sign_connector.get_users = get_users
    sign_engine.logger = logging.getLogger()
    sign_engine.deactivate_sign_users(sign_engine, directory_users, sign_connector)
    assert True
    assert sign_users['example.user@signtest.com']['email'] == 'example.user@signtest.com'
    
