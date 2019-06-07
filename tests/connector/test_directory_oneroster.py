import os
import pytest
import user_sync
import user_sync.connector.directory

from user_sync.connector.directory_oneroster import OneRosterConnector
from user_sync.connector.directory_oneroster import RecordHandler
from user_sync import config


@pytest.fixture()
def default_options():
    config_loader = user_sync.config.ConfigLoader({
                                                      'config_filename': os.path.join('tests','fixture','user-sync-config.yml'),
                                                      'encoding_name': None})

    config_loader.main_config.value['directory_users']['connectors']['oneroster'] = os.path.join('tests','fixture','connector-oneroster.yml')
    config_loader.invocation_options['connector'][0] = 'oneroster'

    directory_connector_module = __import__('user_sync.connector.directory_oneroster', fromlist=[''])
    directory_connector = user_sync.connector.directory.DirectoryConnector(directory_connector_module)
    directory_connector_options = config_loader.get_directory_connector_options(directory_connector.name)
    directory_connector_options['user_identity_type'] = 'federatedID'
    directory_connector_options['user_domain_format'] = '{org}'
    directory_connector_options['user_identity_type_format'] = ''
    directory_connector_options['user_username_format'] = '{username}'
    directory_connector_options['user_country_code_format'] = '{countryCode}'
    directory_connector_options['user_surname_format'] = '{familyName}'
    directory_connector_options['logger_name'] = 'oneroster'
    directory_connector_options['user_given_name_format'] = '{givenName}'

    return directory_connector_options

@pytest.fixture
def oneroster_connector(default_options):
    return OneRosterConnector(default_options)



# @pytest.fixture
# def oneroster_logger(default_options):
#     return OneRosterConnector(default_options).logger


@pytest.fixture
def record_handler(default_options, log_stream):
    return RecordHandler(default_options, log_stream)



def test_parse_results_valid(record_handler, api_result_set):
    extended_attributes = ['firstname']

    x = record_handler.parse_results(api_result_set, 'sourcedId', extended_attributes)

    y = api_result_set

    k = 5

    assert record_handler.parse_results(api_result_set, 'sourcedId', extended_attributes) \
           == {'18125':
                   {'identity_type': 'federatedID', 'username': 'billy.flores@classlink.k12.nj.us',
                    'domain': 'classlink.k12.nj.us', 'firstname': 'BILLY', 'lastname': 'FLORES',
                    'email': 'billy.flores@classlink.k12.nj.us', 'groups': set(), 'country': 'US',
                    'source_attributes': {'email': 'billy.flores@classlink.k12.nj.us', 'identity_type': None, 'username': None, 'domain': None, 'givenName': 'BILLY', 'familyName': 'FLORES', 'country': None}}, '18317': {'identity_type': 'federatedID', 'username': 'giselle.houston@classlink.k12.nj.us', 'domain': 'classlink.k12.nj.us', 'firstname': 'GISELLE', 'lastname': 'HOUSTON', 'email': 'giselle.houston@classlink.k12.nj.us', 'groups': set(), 'country': 'US', 'source_attributes': {'email': 'giselle.houston@classlink.k12.nj.us', 'identity_type': None, 'username': None, 'domain': None, 'givenName': 'GISELLE', 'familyName': 'HOUSTON', 'country': None}}, '19529': {'identity_type': 'federatedID', 'username': 'lari.reyesgarcia@classlink.k12.nj.us', 'domain': 'classlink.k12.nj.us', 'firstname': 'LARI', 'lastname': 'REYES GARCIA', 'email': 'lari.reyesgarcia@classlink.k12.nj.us', 'groups': set(), 'country': 'US', 'source_attributes': {'email': 'lari.reyesgarcia@classlink.k12.nj.us', 'identity_type': None, 'username': None, 'domain': None, 'givenName': 'LARI', 'familyName': 'REYES GARCIA', 'country': None}}}

































def test_parse_yml_groups_valid(oneroster_connector):
    assert oneroster_connector.parse_yml_groups({'classes::yyy::students'}) \
           == {
               'classes': {
                   'yyy': {
                       'classes::yyy::students': 'students'}}}

    assert oneroster_connector.parse_yml_groups({'courses::y    y    y::teachers'}) \
           == {
               'courses': {
                   'y    y    y': {
                       'courses::y    y    y::teachers': 'teachers'}}}

def test_parse_yml_groups_simple_group_mapping_valid(oneroster_connector):
    assert oneroster_connector.parse_yml_groups({'xxx'}) \
           == {
                'classes': {
                    'xxx': {
                        'xxx': 'students'}}}



def test_parse_yml_groups_failure(oneroster_connector, log_stream):
    stream, logger = log_stream
    oneroster_connector.logger = logger

    # false value for group_filter, viable options [courses, classes, schools]
    oneroster_connector.parse_yml_groups({'course::Alg-102::students'})

    # false value for user_filter, viable options [students, teachers, users]
    oneroster_connector.parse_yml_groups({'courses::Alg-102::stud'})

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

    assert oneroster_connector.parse_yml_groups(group_list) \
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




    # assert returned_dict == expected_dict

# OneRosterValueFormatter Class:

# Connection Class:

# RecordHandler Class:

# @mock.patch('user_sync.connector.directory_oneroster.Connection.get_key_identifier')
# def test_retrieve_api_token(self, MockCall):
#     x = 5
#     call = MockCall()
#     call.posts.return_value = b'{"access_token":"2ad79b29-af22-42be-8c15-f777369eb726","token_type":"bearer","expires_in":25945966,"scope":"all"}'
#
#     expected_token = '2ad79b29-af22-42be-8c15-f777369eb726'
#
#     returned_token = json.loads(call.posts())['access_token']
#     y = 5
#     assert returned_token == 5
#
#     assert returned_token == expected_token

# @pytest.fixture()
# def option_builder():
#     caller_options = {
#         'host': 'https://mockroster.io/',
#         'api_token_endpoint': 'https://mockroster.io/oauth/token',
#         'key_identifier': 'sourcedId',
#         'country_code': 'US',
#         'authentication_type': {
#             'auth_type': 'oauth2_non_lib',
#             'client_id': 'oruser',
#             'client_secret': 'secret'},
#         'user_identity_type': 'federatedID'}
#
#     connector = OneRosterConnector(caller_options)
#

#
#
# def test_parse_results():
#     extended_attributes = []
#
#     result_set = [{
#         'userId': 'bc16d091-7017-4f2f-9109-250fd590ca6a',
#         'sourcedId': 'bc16d091-7017-4f2f-9109-250fd590ca6a',
#         'status': 'active',
#         'dateLastModified': '2018-04-01 21:05:50',
#         'metadata': '',
#         'enabledUser': '1',
#         'userIds': '',
#         'identifier': 'GbYh-2CV5-Dz19',
#         'schoolId': 'f5897384-9488-466f-b049-1992f7a53f15',
#         'givenName': 'Antonietta',
#         'familyName': 'Consterdine',
#         'middleName': 'Feliza',
#         'email': 'aconsterdine@woodland.perficientads.com',
#         'username': 'aconsterdine',
#         'phone': '354-733-0622',
#         'role': 'student',
#         'grades': '07',
#         'type': 'LDAP',
#         'password': 'secret'},
#         {
#         'userId': '18e27d22-49d9-407e-a38e-d5ad35577e53',
#         'sourcedId': '18e27d22-49d9-407e-a38e-d5ad35577e53',
#         'status': 'active',
#         'dateLastModified': '2018-02-13 12:37:53',
#         'metadata': '',
#         'enabledUser': '1',
#         'userIds': '',
#         'identifier': 'Ur9l-oYH3-VpQ5',
#         'schoolId': 'f5897384-9488-466f-b049-1992f7a53f15',
#         'givenName': 'Ariel',
#         'familyName': 'Rome',
#         'middleName': 'Edeline',
#         'email': 'arome@woodland.perficientads.com',
#         'username': 'arome',
#         'phone': '926-670-4557',
#         'role': 'student',
#         'grades': '07',
#         'type': 'LDAP',
#         'password': 'secret'}]
#
#     returned_dict = RecordHandler.parse_results(result_set, extended_attributes, connector.key_identifier)
#
#     expected_user_dict = {
#         'bc16d091-7017-4f2f-9109-250fd590ca6a':
#             {
#                 'email': 'aconsterdine@woodland.perficientads.com',
#                 'username': 'aconsterdine@woodland.perficientads.com',
#                 'firstname': 'Antonietta',
#                 'lastname': 'Consterdine',
#                 'domain': 'woodland.perficientads.com',
#                 'source_attributes':
#                     {
#                         'email': 'aconsterdine@woodland.perficientads.com',
#                         'username': 'aconsterdine',
#                         'givenName': 'Antonietta',
#                         'familyName': 'Consterdine',
#                         'domain': 'woodland.perficientads.com',
#                         'enabledUser': '1',
#                         'grades': '07',
#                         'identifier': 'GbYh-2CV5-Dz19',
#                         'metadata': '',
#                         'middleName': 'Feliza',
#                         'phone': '354-733-0622',
#                         'role': 'student',
#                         'schoolId': 'f5897384-9488-466f-b049-1992f7a53f15',
#                         'sourcedId': 'bc16d091-7017-4f2f-9109-250fd590ca6a',
#                         'status': 'active',
#                         'type': 'LDAP',
#                         'userId': 'bc16d091-7017-4f2f-9109-250fd590ca6a',
#                         'userIds': ''},
#                 'groups': set()},
#         '18e27d22-49d9-407e-a38e-d5ad35577e53':
#             {
#                 'email': 'arome@woodland.perficientads.com',
#                 'username': 'arome@woodland.perficientads.com',
#                 'firstname': 'Ariel',
#                 'lastname': 'Rome',
#                 'domain': 'woodland.perficientads.com',
#                 'source_attributes':
#                     {
#                         'email': 'arome@woodland.perficientads.com',
#                         'username': 'arome',
#                         'givenName': 'Ariel',
#                         'familyName': 'Rome',
#                         'domain': 'woodland.perficientads.com',
#                         'enabledUser': '1',
#                         'grades': '07',
#                         'identifier': 'Ur9l-oYH3-VpQ5',
#                         'metadata': '',
#                         'middleName': 'Edeline',
#                         'phone': '926-670-4557',
#                         'role': 'student',
#                         'schoolId': 'f5897384-9488-466f-b049-1992f7a53f15',
#                         'sourcedId': '18e27d22-49d9-407e-a38e-d5ad35577e53',
#                         'status': 'active',
#                         'type': 'LDAP',
#                         'userId': '18e27d22-49d9-407e-a38e-d5ad35577e53',
#                         'userIds': ''},
#                 'groups': set()}}
#
#     assert returned_dict == expected_user_dict
#
# def test_create_user_object():
#
#     user = {'userId': 'bc16d091-7017-4f2f-9109-250fd590ca6a',
#                   'sourcedId': 'bc16d091-7017-4f2f-9109-250fd590ca6a',
#                   'status': 'active', 'dateLastModified': '2018-04-01 21:05:50',
#                   'metadata': '', 'enabledUser': '1', 'userIds': '',
#                   'identifier': 'GbYh-2CV5-Dz19', 'schoolId': 'f5897384-9488-466f-b049-1992f7a53f15',
#                   'givenName': 'Antonietta', 'familyName': 'Consterdine', 'middleName': 'Feliza',
#                   'email': 'aconsterdine@woodland.perficientads.com', 'username': 'aconsterdine',
#                   'phone': '354-733-0622', 'role': 'student', 'grades': '07', 'type': 'LDAP', 'password': 'secret'}
#
#     original_group = 'courses::Alg-102::students'
#
#     created_user = result_parser.create_user_object(user, [], original_group)
#
#     expected_user = {'domain': 'woodland.perficientads.com', 'firstname': 'Antonietta',
#                      'lastname': 'Consterdine', 'email': 'aconsterdine@woodland.perficientads.com',
#                      'groups': ['courses::Alg-102::students'],
#                      'source_attributes': {'email': 'aconsterdine@woodland.perficientads.com',
#                                            'username': 'aconsterdine', 'givenName': 'Antonietta',
#                                            'familyName': 'Consterdine', 'domain': 'woodland.perficientads.com',
#                                            'enabledUser': '1', 'grades': '07', 'identifier': 'GbYh-2CV5-Dz19',
#                                            'metadata': '', 'middleName': 'Feliza', 'phone': '354-733-0622',
#                                            'role': 'student', 'schoolId': 'f5897384-9488-466f-b049-1992f7a53f15',
#                                            'sourcedId': 'bc16d091-7017-4f2f-9109-250fd590ca6a', 'status': 'active',
#                                            'type': 'LDAP', 'userId': 'bc16d091-7017-4f2f-9109-250fd590ca6a', 'userIds': ''},
#                      'username': 'aconsterdine@woodland.perficientads.com'}
#
#     assert created_user == expected_user

# @patch('user_sync.connector.directory_oneroster.Authenticator.retrieve_api_token')
# def test_retrieve_api_token(, MockCall):
#     call = MockCall()
#     call.posts.return_value = b'{"access_token":"2ad79b29-af22-42be-8c15-f777369eb726","token_type":"bearer","expires_in":25945966,"scope":"all"}'
#
#     expected_token = '2ad79b29-af22-42be-8c15-f777369eb726'
#
#     returned_token = json.loads(call.posts())['access_token']
#     assert returned_token == expected_token

# @mock.patch('user_sync.connector.directory_oneroster.ResultParser')
# @mock.patch('user_sync.connector.directory_oneroster.Connection')
# @mock.patch('user_sync.connector.directory_oneroster.Connection.get_all_users')
# def test_load_users_and_groups(MockAuth, MockConn, MockParse):
#
#     #x = MockAuth
#
#
#     mock_adobe_user_group = {'courses::Alg-102::students', 'classes::Algebra I - Fall::teachers'}
#     y = 5
#     #groups_from_yml = connector.parse_yml_groups(mock_adobe_user_group)
#
#     #deliverable_user_list = connector.load_users_and_groups(mock_adobe_user_group, [], True)
#
#
#     #assert six.itervalues(users_result) != None
#
#         # def test_load_users_and_groups():
#         #     mock_adobe_user_group = {'courses::Alg-102::students', 'classes::Algebra I - Fall::teachers'}
#         #
#         #     deliverable_user_list = connector.load_users_and_groups(mock_adobe_user_group, [], True)
#         #
#         #     print(deliverable_user_list)
