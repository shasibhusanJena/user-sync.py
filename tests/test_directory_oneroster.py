import pytest

from user_sync.connector.directory_oneroster import *


@pytest.fixture()
def caller_options():
    return {
        'client_id': '0fc7e35773c1fffd32579507',
        'client_secret': '10332e330b2e364020179021',
        'host': 'https://adobe-ca-v2.oneroster.com/ims/oneroster/v1p1/',
        'all_users_filter': 'users',
        'limit': '100',
        'key_identifier': 'sourcedId',
        'logger_name': 'oneroster',
        'user_email_format': '{email}',
        'user_given_name_format': '{givenName}',
        'user_surname_format': '{familyName}',
        'user_country_code_format': '{countryCode}',
        'user_identity_type': 'federatedID',
        'default_group_filter': 'classes',
        'default_user_filter': 'students'
        #  'user_username_format': None,
        #  'user_domain_format': None,
        #  'user_identity_type_format': None,
    }


@pytest.fixture()
def stub_api_response():
    return [{
        'sourcedId': '18125',
        'status': 'active',
        'dateLastModified': '2019-03-01T18:14:45.000Z',
        'username': 'billy.flores',
        'userIds': [{
            'type': 'FED',
            'identifier': '18125'}],
        'enabledUser': 'true',
        'givenName': 'BILLY',
        'familyName': 'FLORES',
        'middleName': 'DASEAN',
        'role': 'student',
        'identifier': '17580',
        'email': 'billy.flores@classlink.k12.nj.us',
        'sms': '(666) 666-6666',
        'phone': '',
        'agents': [],
        'orgs': [
            {
                'href': 'https://adobe-ca-v2.oneroster.com/ims/oneroster/v1p1/orgs/2',
                'sourcedId': '2',
                'type': 'org'}],
        'grades': ['11'],
        'password': ''},
        {
            'sourcedId': '18317',
            'status': 'active',
            'dateLastModified': '2019-03-01T18:14:45.000Z',
            'username': 'giselle.houston',
            'userIds': [{
                'type': 'FED',
                'identifier': '18317'}],
            'enabledUser': 'true',
            'givenName': 'GISELLE',
            'familyName': 'HOUSTON',
            'middleName': 'CAMILO',
            'role': 'student',
            'identifier': '15125',
            'email': 'giselle.houston@classlink.k12.nj.us',
            'sms': '',
            'phone': '',
            'agents': [],
            'orgs': [
                {
                    'href': 'https://adobe-ca-v2.oneroster.com/ims/oneroster/v1p1/orgs/2',
                    'sourcedId': '2',
                    'type': 'org'}],
            'grades': ['11'],
            'password': ''},

    ]


@pytest.fixture
def oneroster_connector(caller_options):
    return OneRosterConnector(caller_options)


def test_parse_results_valid(oneroster_connector, stub_api_response):

    expected_result = {
        '18125': {
            'identity_type': 'federatedID',
            'username': 'billy.flores@classlink.k12.nj.us',
            'domain': 'classlink.k12.nj.us',
            'firstname': 'BILLY',
            'lastname': 'FLORES',
            'email': 'billy.flores@classlink.k12.nj.us',
            'groups': set(),
            'country': None,
            'source_attributes': {
                'email': 'billy.flores@classlink.k12.nj.us',
                'identity_type': None,
                'username': None,
                'domain': None,
                'givenName': 'BILLY',
                'familyName': 'FLORES',
                'country': None}},
        '18317': {
            'identity_type': 'federatedID',
            'username': 'giselle.houston@classlink.k12.nj.us',
            'domain': 'classlink.k12.nj.us',
            'firstname': 'GISELLE',
            'lastname': 'HOUSTON',
            'email': 'giselle.houston@classlink.k12.nj.us',
            'groups': set(),
            'country': None,
            'source_attributes': {
                'email': 'giselle.houston@classlink.k12.nj.us',
                'identity_type': None,
                'username': None,
                'domain': None,
                'givenName': 'GISELLE',
                'familyName': 'HOUSTON',
                'country': None}},
    }

    record_handler = RecordHandler(options=oneroster_connector.options, logger=oneroster_connector.logger)
    actual_result = record_handler.parse_results(stub_api_response, 'sourcedId', [])
    assert expected_result == actual_result

    # asserts extended attributes are added to source_attributes dict(),
    # sms and identifier attributes have been extended

    expected_result['18125']['source_attributes']['sms'] = '(666) 666-6666'
    expected_result['18125']['source_attributes']['identifier'] = '17580'
    expected_result['18317']['source_attributes']['sms'] = None
    expected_result['18317']['source_attributes']['identifier'] = '15125'
    actual_result = record_handler.parse_results(stub_api_response, 'sourcedId', ['sms', 'identifier'])
    assert expected_result == actual_result

    # Fetch nonexistent properties

    expected_result['18125']['source_attributes']['fake'] = None
    expected_result['18317']['source_attributes']['fake'] = None
    actual_result = record_handler.parse_results(stub_api_response, 'sourcedId', ['sms', 'identifier', 'fake'])
    assert expected_result == actual_result



def test_parse_yml_groups_valid(oneroster_connector):
    assert oneroster_connector.parse_yaml_groups({'classes::yyy::students'}) \
           == {
               'classes': {
                   'yyy': {
                       'classes::yyy::students': 'students'}}}

    assert oneroster_connector.parse_yaml_groups({'courses::y    y    y::teachers'}) \
           == {
               'courses': {
                   'y    y    y': {
                       'courses::y    y    y::teachers': 'teachers'}}}

    assert oneroster_connector.parse_yaml_groups({'xxx'}) \
           == {
               'classes': {
                   'xxx': {
                       'xxx': 'students'}}}


def test_parse_yml_groups_failure(oneroster_connector, log_stream):
    stream, logger = log_stream
    oneroster_connector.logger = logger

    # false value for group_filter, viable options [courses, classes, schools]
    oneroster_connector.parse_yaml_groups({'course::Alg-102::students'})

    # false value for user_filter, viable options [students, teachers, users]
    oneroster_connector.parse_yaml_groups({'courses::Alg-102::stud'})

    stream.flush()
    error_logger_message = stream.getvalue()
    assert 'stud' in error_logger_message
    assert 'course' in error_logger_message


def test_parse_yml_groups_complex_valid(oneroster_connector):
    group_list = {'courses::Alg-102::students',
                  'classes::Geography I - Spring::students',
                  'classes::Art I - Fall::students',
                  'classes::Art I - Fall::teachers',
                  'classes::Art        I - Fall::teachers',
                  'classes::Algebra I - Fall::students',
                  'schools::Spring Valley::students',
                  'xxx'}

    assert oneroster_connector.parse_yaml_groups(group_list) \
           == {
               "classes": {
                   "algebra i - fall": {
                       "classes::Algebra I - Fall::students": "students"
                   },
                   "geography i - spring": {
                       "classes::Geography I - Spring::students": "students"
                   },
                   "art i - fall": {
                       "classes::Art I - Fall::students": "students",
                       "classes::Art I - Fall::teachers": "teachers"
                   },
                   "art        i - fall": {
                       "classes::Art        I - Fall::teachers": "teachers"
                   },
                   'xxx': {
                       'xxx': 'students'}
               },
               "courses": {
                   "alg-102": {
                       "courses::Alg-102::students": "students"
                   }
               },
               "schools": {
                   "spring valley": {
                       "schools::Spring Valley::students": "students"
                   }
               }
           }


def test_get_attr_values():
    attributes = {
        'sourcedId': '18125',
        'status': 'active',
        'dateLastModified': '2019-03-01T18:14:45.000Z',
        'username': 'billy.flores',
        'userIds': [{
            'type': 'FED',
            'identifier': '18125'}],
        'enabledUser': 'true',
        'givenName': 'BILLY',
        'familyName': 'FLORES',
        'middleName': 'DASEAN',
        'role': 'student',
        'identifier': '17580',
        'email': 'billy.flores@classlink.k12.nj.us',
        'sms': None,
        'phone': {
            'home': '111-111-1111',
            'work': '222-222-2222'},
        'agents': ['1', '2'],
        'orgs': [{
            'href': 'https://adobe-ca-v2.oneroster.com/ims/oneroster/v1p1/orgs/2',
            'sourcedId': '2',
            'type': 'org'}],
        'grades': ['15', ['11', '12', '13'], '14'],
        'byte': b'byteencoded',
        'password': ''}

    formatter = OneRosterValueFormatter(None)

    # Get a simple string
    assert formatter.get_attribute_value(attributes, "username") == "billy.flores"
    assert formatter.get_attribute_value(attributes, "dateLastModified") == "2019-03-01T18:14:45.000Z"

    # Get a list
    assert formatter.get_attribute_value(attributes, "agents") == ['1', '2']

    # Get a dictionary
    assert formatter.get_attribute_value(attributes, "phone") == {
        'home': '111-111-1111',
        'work': '222-222-2222'}
    assert formatter.get_attribute_value(attributes, "orgs") == {
        'href': 'https://adobe-ca-v2.oneroster.com/ims/oneroster/v1p1/orgs/2',
        'sourcedId': '2',
        'type': 'org'
    }

    # Get None
    assert formatter.get_attribute_value(attributes, "sms") == None

    # Get a nested object
    assert formatter.get_attribute_value(attributes, "grades") == ['15', ['11', '12', '13'], '14']

    # Decode a string
    assert formatter.get_attribute_value(attributes, "byte") == "byteencoded"

#
# def test_lug_ex(oneroster_connector):
#     import mock
#     with mock.patch("user_sync.connector.directory_oneroster.Connection.list_api_response_handler") as mock_endpoint:
#         mock_endpoint.return_value = "1234"
#         x = oneroster_connector.load_users_and_groups(['xxx'],[],False)
#
#         print()
