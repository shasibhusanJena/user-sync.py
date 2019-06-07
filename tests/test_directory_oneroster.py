import pytest

import user_sync
import user_sync.connector.directory
from user_sync.connector.directory_oneroster import *


@pytest.fixture()
def default_options():
    return {'host': 'https://adobe-ca-v2.oneroster.com/ims/oneroster/v1p1/',
            'key_identifier': 'sourcedId',
            'client_id': '0fc7e35773c1fffd32579507', 'client_secret': '10332e330b2e364020179021',
            'all_users_filter': 'users', 'default_group_filter': 'classes',
            'default_user_filter': 'students', 'limit': '100', 'user_email_format': '{email}',
            'user_country_code_format': '{countryCode}', 'user_identity_type': 'federatedID'}


@pytest.fixture
def oneroster_connector(default_options):
    return OneRosterConnector(default_options)


@pytest.fixture
def record_handler(log_stream):
    options = {'client_id': '0fc7e35773c1fffd32579507', 'client_secret': '10332e330b2e364020179021',
               'host': 'https://adobe-ca-v2.oneroster.com/ims/oneroster/v1p1/', 'all_users_filter': 'users',
               'limit': '100', 'key_identifier': 'sourcedId', 'logger_name': 'oneroster',
               'user_email_format': '{email}', 'user_given_name_format': '{givenName}',
               'user_surname_format': '{familyName}', 'user_country_code_format': '{countryCode}',
               'user_username_format': None, 'user_domain_format': None, 'user_identity_type': 'federatedID',
               'user_identity_type_format': None, 'default_group_filter': 'classes', 'default_user_filter': 'students'}

    return RecordHandler(options, log_stream)


@pytest.fixture
def connection(log_stream):
    options = {'client_id': '0fc7e35773c1fffd32579507', 'client_secret': '10332e330b2e364020179021',
               'host': 'https://adobe-ca-v2.oneroster.com/ims/oneroster/v1p1/', 'all_users_filter': 'users',
               'limit': '100', 'key_identifier': 'sourcedId', 'logger_name': 'oneroster',
               'user_email_format': '{email}', 'user_given_name_format': '{givenName}',
               'user_surname_format': '{familyName}', 'user_country_code_format': '{countryCode}',
               'user_username_format': None, 'user_domain_format': None, 'user_identity_type': 'federatedID',
               'user_identity_type_format': None, 'default_group_filter': 'classes', 'default_user_filter': 'students'}

    return Connection(log_stream, options)



def test_parse_results_valid(record_handler):
    api_result_set = [{'sourcedId': '18125', 'status': 'active', 'dateLastModified': '2019-03-01T18:14:45.000Z',
                       'username': 'billy.flores', 'userIds': [{'type': 'FED', 'identifier': '18125'}],
                       'enabledUser': 'true', 'givenName': 'BILLY', 'familyName': 'FLORES', 'middleName': 'DASEAN',
                       'role': 'student', 'identifier': '17580', 'email': 'billy.flores@classlink.k12.nj.us', 'sms': '',
                       'phone': '', 'agents': [], 'orgs': [
                            {'href': 'https://adobe-ca-v2.oneroster.com/ims/oneroster/v1p1/orgs/2', 'sourcedId': '2',
                             'type': 'org'}],
                       'grades': ['11'], 'password': ''},
                      {'sourcedId': '18317', 'status': 'active', 'dateLastModified': '2019-03-01T18:14:45.000Z',
                       'username': 'giselle.houston', 'userIds': [{'type': 'FED', 'identifier': '18317'}],
                       'enabledUser': 'true', 'givenName': 'GISELLE', 'familyName': 'HOUSTON', 'middleName': 'CAMILO',
                       'role': 'student', 'identifier': '15125', 'email': 'giselle.houston@classlink.k12.nj.us',
                       'sms': '',
                       'phone': '', 'agents': [], 'orgs': [
                          {'href': 'https://adobe-ca-v2.oneroster.com/ims/oneroster/v1p1/orgs/2', 'sourcedId': '2',
                           'type': 'org'}], 'grades': ['11'], 'password': ''},
                      {'sourcedId': '19529', 'status': 'active', 'dateLastModified': '2019-03-01T18:14:45.000Z',
                       'username': 'lari.reyesgarcia', 'userIds': [{'type': 'FED', 'identifier': '19529'}],
                       'enabledUser': 'true', 'givenName': 'LARI', 'familyName': 'REYES GARCIA', 'middleName': 'SIMONE',
                       'role': 'student', 'identifier': '19934', 'email': 'lari.reyesgarcia@classlink.k12.nj.us',
                       'sms': '',
                       'phone': '', 'agents': [], 'orgs': [
                          {'href': 'https://adobe-ca-v2.oneroster.com/ims/oneroster/v1p1/orgs/2', 'sourcedId': '2',
                           'type': 'org'}], 'grades': ['11'], 'password': ''}]

    expected_result = {'18125': {'identity_type': 'federatedID', 'username': 'billy.flores@classlink.k12.nj.us',
                                 'domain': 'classlink.k12.nj.us', 'firstname': 'BILLY', 'lastname': 'FLORES',
                                 'email': 'billy.flores@classlink.k12.nj.us', 'groups': set(), 'country': None,
                                 'source_attributes': {'email': 'billy.flores@classlink.k12.nj.us',
                                                       'identity_type': None,
                                                       'username': None, 'domain': None, 'givenName': 'BILLY',
                                                       'familyName': 'FLORES', 'country': None}},
                       '18317': {'identity_type': 'federatedID', 'username': 'giselle.houston@classlink.k12.nj.us',
                                 'domain': 'classlink.k12.nj.us', 'firstname': 'GISELLE', 'lastname': 'HOUSTON',
                                 'email': 'giselle.houston@classlink.k12.nj.us', 'groups': set(), 'country': None,
                                 'source_attributes': {'email': 'giselle.houston@classlink.k12.nj.us',
                                                       'identity_type': None,
                                                       'username': None, 'domain': None, 'givenName': 'GISELLE',
                                                       'familyName': 'HOUSTON', 'country': None}},
                       '19529': {'identity_type': 'federatedID', 'username': 'lari.reyesgarcia@classlink.k12.nj.us',
                                 'domain': 'classlink.k12.nj.us', 'firstname': 'LARI', 'lastname': 'REYES GARCIA',
                                 'email': 'lari.reyesgarcia@classlink.k12.nj.us', 'groups': set(), 'country': None,
                                 'source_attributes': {'email': 'lari.reyesgarcia@classlink.k12.nj.us',
                                                       'identity_type': None,
                                                       'username': None, 'domain': None, 'givenName': 'LARI',
                                                       'familyName': 'REYES GARCIA', 'country': None}}}

    actual_result = record_handler.parse_results(api_result_set, 'sourcedId', [])
    assert expected_result == actual_result

    # asserts extended attributes are added to source_attributes dict(),
    # sms and identifier attributes have been extended

    assert record_handler.parse_results(api_result_set, 'sourcedId', ['sms', 'identifier']) == \
           {'18125': {'identity_type': 'federatedID', 'username': 'billy.flores@classlink.k12.nj.us',
                      'domain': 'classlink.k12.nj.us', 'firstname': 'BILLY', 'lastname': 'FLORES',
                      'email': 'billy.flores@classlink.k12.nj.us', 'groups': set(), 'country': None,
                      'source_attributes': {'email': 'billy.flores@classlink.k12.nj.us',
                                            'identity_type': None,
                                            'username': None, 'domain': None, 'givenName': 'BILLY',
                                            'familyName': 'FLORES', 'country': None, 'sms': None,
                                            'identifier': '17580'}},
            '18317': {'identity_type': 'federatedID', 'username': 'giselle.houston@classlink.k12.nj.us',
                      'domain': 'classlink.k12.nj.us', 'firstname': 'GISELLE', 'lastname': 'HOUSTON',
                      'email': 'giselle.houston@classlink.k12.nj.us', 'groups': set(), 'country': None,
                      'source_attributes': {'email': 'giselle.houston@classlink.k12.nj.us',
                                            'identity_type': None,
                                            'username': None, 'domain': None, 'givenName': 'GISELLE',
                                            'familyName': 'HOUSTON', 'country': None, 'sms': None,
                                            'identifier': '15125'}},
            '19529': {'identity_type': 'federatedID', 'username': 'lari.reyesgarcia@classlink.k12.nj.us',
                      'domain': 'classlink.k12.nj.us', 'firstname': 'LARI', 'lastname': 'REYES GARCIA',
                      'email': 'lari.reyesgarcia@classlink.k12.nj.us', 'groups': set(), 'country': None,
                      'source_attributes': {'email': 'lari.reyesgarcia@classlink.k12.nj.us',
                                            'identity_type': None,
                                            'username': None, 'domain': None, 'givenName': 'LARI',
                                            'familyName': 'REYES GARCIA', 'country': None, 'sms': None,
                                            'identifier': '19934'}}}



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


def test_OneRosterValueFormatter():
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
        'phone': {'home': '111-111-1111', 'work': '222-222-2222'},
        'agents': ['1', '2'],
        'orgs': [{
            'href': 'https://adobe-ca-v2.oneroster.com/ims/oneroster/v1p1/orgs/2',
            'sourcedId': '2',
            'type': 'org'}],
        'grades': ['15', ['11', '12', '13'], '14'],
        'byte': b'byteencoded',
        'password': ''}

    formatter = user_sync.connector.directory_oneroster.OneRosterValueFormatter(None)

    # Get a simple string
    assert formatter.get_attribute_value(attributes, "username") == "billy.flores"
    assert formatter.get_attribute_value(attributes, "dateLastModified") == "2019-03-01T18:14:45.000Z"

    # Get a list
    assert formatter.get_attribute_value(attributes, "agents") == ['1', '2']

    # Get a dictionary
    assert formatter.get_attribute_value(attributes, "phone") == {'home': '111-111-1111', 'work': '222-222-2222'}
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
