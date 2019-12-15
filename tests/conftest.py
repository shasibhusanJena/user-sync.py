import logging
import os

import pytest

from copy import deepcopy
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


@pytest.fixture
def mock_directory_user():
    return deepcopy({
        'identity_type': 'federatedID',
        'username': 'nameless@example.com',
        'domain': 'example.com',
        'firstname': 'One',
        'lastname': 'Six',
        'email': 'nameless@example.com',
        'groups': ['All Sea of Carag'],
        'country': 'US',
        'member_groups': [],
        'source_attributes': {
            'email': 'nameless@example.com',
            'identity_type': None,
            'username': None,
            'domain': None,
            'givenName': 'One',
            'sn': 'Six',
            'c': 'US'}})


@pytest.fixture()
def mock_umapi_user():
    return deepcopy({
        'email': 'bsisko@example.com',
        'status': 'active',
        'groups': ['Group A', '_admin_Group A', 'Group A_1924484-provisioning'],
        'username': 'bsisko@example.com',
        'domain': 'example.com',
        'firstname': 'Benjamin',
        'lastname': 'Sisko',
        'country': 'CA',
        'type': 'federatedID'
    })


@pytest.fixture
def mock_user_directory_data():
    return deepcopy({
        'federatedID,both1@example.com,':
            {
                'identity_type': 'federatedID',
                'username': 'both1@example.com',
                'domain': 'example.com',
                'firstname': 'both1',
                'lastname': 'one',
                'email': 'both1@example.com',
                'groups': ['All Sea of Carag'],
                'country': 'US',
                'member_groups': [],
                'source_attributes': {
                    'email': 'both1@example.com',
                    'identity_type': None,
                    'username': None,
                    'domain': None,
                    'givenName': 'both1',
                    'sn': 'one',
                    'c': 'US'}},
        'federatedID,both2@example.com,':
            {
                'identity_type': 'federatedID',
                'username': 'both2@example.com',
                'domain': 'example.com',
                'firstname': 'both2',
                'lastname': 'one',
                'email': 'both2@example.com',
                'groups': ['All Sea of Carag'],
                'country': 'US',
                'member_groups': [],
                'source_attributes': {
                    'email': 'both2@example.com',
                    'identity_type': None,
                    'username': None,
                    'domain': None,
                    'givenName': 'both2',
                    'sn': 'two',
                    'c': 'US'}},
        'federatedID,both3@example.com,':
            {
                'identity_type': 'federatedID',
                'username': 'both3@example.com',
                'domain': 'example.com',
                'firstname': 'both3',
                'lastname': 'one',
                'email': 'both3@example.com',
                'groups': ['All Sea of Carag'],
                'country': 'US',
                'member_groups': [],
                'source_attributes': {
                    'email': 'both3@example.com',
                    'identity_type': None,
                    'username': None,
                    'domain': None,
                    'givenName': 'both3',
                    'sn': 'three',
                    'c': 'US'}},
        'federatedID,directory.only1@example.com,':
            {
                'identity_type': 'federatedID',
                'username': 'directory.only1@example.com',
                'domain': 'example.com',
                'firstname': 'dir1',
                'lastname': 'one',
                'email': 'directory.only1example.com',
                'groups': ['All Sea of Carag'],
                'country': 'US',
                'member_groups': [],
                'source_attributes': {
                    'email': 'directory.only1@example.com',
                    'identity_type': None,
                    'username': None,
                    'domain': None,
                    'givenName': 'dir1',
                    'sn': 'one',
                    'c': 'US'}}
    })


@pytest.fixture
def mock_umapi_user_data():
    return deepcopy([
        {
            'email': 'both1@example.com',
            'status': 'active',
            'groups': ['_org_admin', 'group1'],
            'username': 'both1@example.com',
            'adminRoles': ['org'],
            'domain': 'example.com',
            'country': 'US',
            'type': 'federatedID'},
        {
            'email': 'both2@example.com',
            'status': 'active',
            'groups': ['_org_admin', 'user_group'],
            'username': 'both2@example.com',
            'adminRoles': ['org'],
            'domain': 'example.com',
            'country': 'US',
            'type': 'federatedID'},
        {
            'email': 'both3@example.com',
            'status': 'active',
            'groups': ['_org_admin', 'group1', 'user_group'],
            'username': 'both3@example.com',
            'adminRoles': ['org'],
            'domain': 'example.com',
            'country': 'US',
            'type': 'federatedID'},
        {
            'email': 'adobe.only1@example.com',
            'status': 'active',
            'groups': ['_org_admin'],
            'username': 'adobe.only1@example.com',
            'adminRoles': ['org'],
            'domain': 'example.com',
            'country': 'US',
            'type': 'federatedID'},
        {
            'email': 'exclude1@example.com',
            'status': 'active',
            'groups': ['_org_admin'],
            'username': 'exclude1@example.com',
            'adminRoles': ['org'],
            'domain': 'example.com',
            'country': 'US',
            'type': 'federatedID'}])
