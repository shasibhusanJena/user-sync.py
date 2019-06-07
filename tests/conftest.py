import logging
import os
import pytest
from six import StringIO
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
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger('test_logger')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    yield stream, logger
    handler.close()

@pytest.fixture
def api_result_set():
    result_set = [{
            'sourcedId': '18125',
            'status': 'active', 'dateLastModified': '2019-03-01T18:14:45.000Z', 'username': 'billy.flores',
            'userIds': [{'type': 'FED', 'identifier': '18125'}], 'enabledUser': 'true',
            'givenName': 'BILLY', 'familyName': 'FLORES', 'middleName': 'DASEAN',
            'role': 'student', 'identifier': '17580', 'email': 'billy.flores@classlink.k12.nj.us', 'sms': '',
            'phone': '', 'agents': [], 'orgs': [{'href': 'https://adobe-ca-v2.oneroster.com/ims/oneroster/v1p1/orgs/2',
                                                 'sourcedId': '2', 'type': 'org'}], 'grades': ['11'], 'password': ''},
        {
            'sourcedId': '18317',
            'status': 'active', 'dateLastModified': '2019-03-01T18:14:45.000Z', 'username': 'giselle.houston',
            'userIds': [{'type': 'FED', 'identifier': '18317'}], 'enabledUser': 'true', 'givenName': 'GISELLE',
            'familyName': 'HOUSTON', 'middleName': 'CAMILO', 'role': 'student', 'identifier': '15125',
            'email': 'giselle.houston@classlink.k12.nj.us', 'sms': '', 'phone': '', 'agents': [],
            'orgs': [{'href': 'https://adobe-ca-v2.oneroster.com/ims/oneroster/v1p1/orgs/2', 'sourcedId': '2',
                      'type': 'org'}], 'grades': ['11'], 'password': ''},
        {
            'sourcedId': '19529', 'status': 'active', 'dateLastModified': '2019-03-01T18:14:45.000Z',
            'username': 'lari.reyesgarcia', 'userIds': [{'type': 'FED', 'identifier': '19529'}], 'enabledUser': 'true',
            'givenName': 'LARI', 'familyName': 'REYES GARCIA', 'middleName': 'SIMONE', 'role': 'student',
            'identifier': '19934', 'email': 'lari.reyesgarcia@classlink.k12.nj.us', 'sms': '', 'phone': '',
            'agents': [], 'orgs': [{'href': 'https://adobe-ca-v2.oneroster.com/ims/oneroster/v1p1/orgs/2',
                                    'sourcedId': '2', 'type': 'org'}], 'grades': ['11'], 'password': ''
        }]

    return result_set