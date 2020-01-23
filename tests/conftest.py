import logging
import os
from copy import deepcopy

import pytest

from tests.util import ClearableStringIO
from user_sync import config


@pytest.fixture
def fixture_dir():
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), 'fixture'))


@pytest.fixture
def cli_args():
    def _cli_args(args_in):
        """
        :param dict args:
        :return dict:
        """

        args_out = {}
        for k in config.ConfigLoader.invocation_defaults:
            args_out[k] = None
        for k, v in args_in.items():
            args_out[k] = v
        return args_out

    return _cli_args


@pytest.fixture
def log_stream():
    stream = ClearableStringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger('test_logger')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    yield stream, logger
    handler.close()


@pytest.fixture()
def generate_mock_dir_user():
    def _directory_user_template(
            id,
            firstname=None,
            lastname=None,
            groups=None,
            country="US",
            id_type="federatedID",
            domain="example.com",
            username=None
    ):
        user_key = "{0},{1}@{2},".format(id_type, id, domain)
        identifier = id + "@" + domain
        first = firstname or id + " First"
        last = lastname or id + " Last"
        return {

            user_key:
                {
                    'identity_type': id_type,
                    'username': username or identifier,
                    'domain': domain,
                    'firstname': first,
                    'lastname': last,
                    'email': identifier,
                    'groups': groups or [],
                    'country': country,
                    'member_groups': [],
                    'source_attributes': {
                        'email': identifier,
                        'identity_type': None,
                        'username': None,
                        'domain': None,
                        'givenName': first,
                        'sn': last,
                        'c': country}}}

    return _directory_user_template


@pytest.fixture()
def mock_directory_users(generate_mock_dir_user):
    z = generate_mock_dir_user("user1")

    print()

    # def _mock_directory_users(number=5):
    #
    # return _mock_directory_users


@pytest.fixture
def mock_directory_user_data(mock_directory_users):
    return deepcopy({
        'federatedID,user1@example.com,':
            {
                'identity_type': 'federatedID',
                'username': 'user1@example.com',
                'domain': 'example.com',
                'firstname': 'user1',
                'lastname': 'last1',
                'email': 'user1@example.com',
                'groups': ['Group A'],
                'country': 'US',
                'member_groups': [],
                'source_attributes': {
                    'email': 'user1@example.com',
                    'identity_type': None,
                    'username': None,
                    'domain': None,
                    'givenName': 'user1',
                    'sn': 'one',
                    'c': 'US'}},
        'federatedID,user2@example.com,':
            {
                'identity_type': 'federatedID',
                'username': 'user2@example.com',
                'domain': 'example.com',
                'firstname': 'user2',
                'lastname': 'last2',
                'email': 'user2@example.com',
                'groups': ['Group A'],
                'country': 'US',
                'member_groups': [],
                'source_attributes': {
                    'email': 'user2@example.com',
                    'identity_type': None,
                    'username': None,
                    'domain': None,
                    'givenName': 'user2',
                    'sn': 'two',
                    'c': 'US'}},
        'federatedID,user3@example.com,':
            {
                'identity_type': 'federatedID',
                'username': 'user3@example.com',
                'domain': 'example.com',
                'firstname': 'user3',
                'lastname': 'last3',
                'email': 'user3@example.com',
                'groups': ['Group A'],
                'country': 'US',
                'member_groups': [],
                'source_attributes': {
                    'email': 'user3@example.com',
                    'identity_type': None,
                    'username': None,
                    'domain': None,
                    'givenName': 'user3',
                    'sn': 'three',
                    'c': 'US'}}
    })


@pytest.fixture
def mock_umapi_user_data():
    return deepcopy([
        {
            'email': 'user12@example.com',
            'status': 'active',
            'groups': ['group a', 'group b'],
            'username': 'user12@example.com',
            'adminRoles': ['org'],
            'domain': 'example.com',
            'country': 'US',
            'type': 'federatedID'},
        {
            'email': 'user2@example.com',
            'status': 'active',
            'groups': ['group a', 'group b'],
            'username': 'user2@example.com',
            'adminRoles': ['org'],
            'domain': 'example.com',
            'country': 'US',
            'type': 'federatedID'},
        {
            'email': 'user3@example.com',
            'status': 'active',
            'groups': ['group a'],
            'username': 'user3@example.com',
            'adminRoles': ['org'],
            'domain': 'example.com',
            'country': 'US',
            'type': 'federatedID'},
        {
            'email': 'user4@example.com',
            'status': 'active',
            'groups': ['group a', 'group b'],
            'username': 'user4@example.com',
            'adminRoles': ['org'],
            'domain': 'example.com',
            'country': 'US',
            'type': 'federatedID'},
        {
            'email': 'user5@example.com',
            'status': 'active',
            'groups': [],
            'username': 'user5@example.com',
            'adminRoles': ['org'],
            'domain': 'example.com',
            'country': 'US',
            'type': 'federatedID'}])


@pytest.fixture()
def mock_umapi_user(mock_umapi_user_data):
    return mock_umapi_user_data[0]


@pytest.fixture
def mock_directory_user(mock_directory_user_data):
    return list(mock_directory_user_data.values())[0]
