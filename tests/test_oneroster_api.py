import pytest
import mock
import random
import urllib3
import re
import collections
import user_sync.connector.oneroster as oneroster

cleverpath = 'user_sync.connector.oneroster.CleverConnector'


@pytest.fixture()
def clever_api():
    options = {
        'client_id': '5d8a7b5eff6cbe25bc6e',
        'client_secret': 'ec6d2c060987e32cbe785f7f1a58a307a04cf0a4',
        'key_identifier': 'sourcedId',
        'page_size': 1000,
        'max_user_limit': 0,
        'match': 'name'
    }

    return oneroster.CleverConnector(options)


# def test_simple_filters(clever_api):
#     x = clever_api.translate(group_filter='sections', user_filter='students', name='classname')
#
#
# def test_make_call(clever_api):
#     section = "'58da8c6a894273be68000184'"
#     # 31 Users
#
#     call = clever_api.clever_api.get_section(id='58da8c6a894273be68000184')
#     #   results = clever_api.make_call(call, limit=100, id=section)
#
#     print()


@mock.patch('user_sync.connector.oneroster.CleverConnector.make_call')
def test_get_primary_key(mock_make_call, clever_api, log_stream):
    data = [
        {'id': '58da8c6b894273be680001fc', 'name': 'Class 003, Homeroom - Stark - 0'},
        {'id': '58da8c6b894273be6800020a', 'name': 'Class 202, Homeroom - Jones - 0'},
        {'id': '58da8c6b894273be5100020a', 'name': 'Class 202, Homeroom - Jones - 0'},
        {'id': '58da8c6b894273be68000236', 'name': 'Grade 2 Math, Class 201 - Hammes - 3'},
        {'id': '58da8c6b894273be68000222', 'name': 'Kindergarten Math, Class 002 - Schoen - 1'},
        {'id': '58da8c6b894273be68000242', 'name': 'Mathematics, Class 601 - Goldner - 3'}
    ]

    mock_make_call.return_value = get_mock_api_response(data)[0].data

    stream, logger = log_stream
    clever_api.logger = logger

    keys = clever_api.get_primary_key("sections", "Class 202, Homeroom - Jones - 0")
    assert keys == ['58da8c6b894273be6800020a', '58da8c6b894273be5100020a']

    keys = clever_api.get_primary_key("sections", "Fake class")
    assert not keys

    stream.flush()
    logs = stream.getvalue()
    assert re.search('(No objects found for sections:).*(Fake class)', logs)

    stream.buf = ''
    clever_api.match = 'bad'
    clever_api.get_primary_key("sections", "fake")
    stream.flush()
    logs = stream.getvalue()
    assert re.search("(No property: 'bad' was found on section for entity 'fake')", logs)

    data = [{'id': '58da8c6b894273be680001fc', 'name': 'Class 003, Homeroom - Stark - 0', 'course': 'Math 101'}]
    mock_make_call.return_value = get_mock_api_response(data)[0].data
    clever_api.match = 'course'

    keys = clever_api.get_primary_key("sections", "Math 101")
    assert keys == ['58da8c6b894273be680001fc']

    pytest.raises(ValueError, clever_api.get_primary_key, type='bad', name='bad')


@mock.patch('user_sync.connector.oneroster.CleverConnector.make_call')
@mock.patch('user_sync.connector.oneroster.CleverConnector.get_primary_key')
def test_get_sections_for_course(get_key, make_call, clever_api):
    # Sections for ID 1
    data_1 = [
        {'id': '58da8c6b894273be680001fc', 'name': 'Class 003, Homeroom - Stark - 0'},
        {'id': '58da8c6b894273be6800020a', 'name': 'Class 202, Homeroom - Jones - 0'},
        {'id': '58da8c6b894273be5100020a', 'name': 'Class 202, Homeroom - Jones - 0'},
    ]

    # Sections for ID 2
    data_2 = [
        {'id': '58da8c6b894273be68000236', 'name': 'Grade 2 Math, Class 201 - Hammes - 3'},
        {'id': '58da8c6b894273be68000222', 'name': 'Kindergarten Math, Class 002 - Schoen - 1'},
        {'id': '58da8c6b894273be68000242', 'name': 'Mathematics, Class 601 - Goldner - 3'}
    ]

    # These are the id's found for course name (totally arbitrary here)
    get_key.return_value = ['12345', '67892']

    # Each time we call, we get a response
    make_call.side_effect = [get_mock_api_response(data_1), get_mock_api_response(data_2)]

    # Combine ID fields from data 1 and 2
    expected = [map(lambda x: x['id'], data) for data in [data_1, data_2]]
    expected = [y for x in expected for y in x]

    result = clever_api.get_sections_for_course('Math 101')
    assert collections.Counter(expected) == collections.Counter(result)


@mock.patch('user_sync.connector.oneroster.CleverConnector.make_call')
@mock.patch('user_sync.connector.oneroster.CleverConnector.get_sections_for_course')
def test_get_users_for_course(get_sections, make_call, clever_api):
    mock_students = [
        {
            'email': 'z.steve@example.net',
            'name': {'first': 'Steve', 'last': 'Ziemann', 'middle': 'G'},
            'school': '58da8c58155b940248000007',
            'sis_id': '100095233', },
        {
            'email': 'julia.r@example.org',
            'name': {'first': 'Julia', 'last': 'Runolfsdottir', 'middle': 'B'},
            'school': '58da8c58155b940248000007',
            'sis_id': '108028995'}]

    mock_teachers = [
        {
            'email': 'sisko.b@example.net',
            'name': {'first': 'Benjamin', 'last': 'Sisko', 'middle': 'J'},
            'school': '58da8c58155b940248000007',
            'sis_id': '1001234233', },
        {
            'email': 'picard.j@example.org',
            'name': {'first': 'Jean Luc', 'last': 'Picard', 'middle': ''},
            'school': '58da8c58155b940248000007',
            'sis_id': '108062341'}]

    get_sections.return_value = ['12345']
    make_call.side_effect = [
        get_mock_api_response(mock_students),
        get_mock_api_response(mock_teachers)
    ]

    response =  clever_api.get_users_for_course("Math 9", "users")
    response_data = [{'email': d.data.email, 'name': d.data.name,
                      'school': d.data.school, 'sis_id': d.data.sis_id} for d in response]

    mock_students.extend(mock_teachers)
    assert response_data == mock_students

# def test_x(clever_api):
#     d = clever_api.clever_api.get_students_with_http_info()[0].data
#
#     print()


def test_translate(clever_api):
    calls = clever_api.translate('sections', 'users')
    assert calls[0] == clever_api.clever_api.get_students_for_section_with_http_info
    assert calls[1] == clever_api.clever_api.get_teachers_for_section_with_http_info
    pytest.raises(ValueError, clever_api.translate, user_filter="x", group_filter="y")


def get_mock_api_response(data, status_code=200, headers=None):
    headers = urllib3.response.HTTPHeaderDict(headers)
    response_list = [MockResponse(MockEntry(**d)) for d in data]
    return (MockResponse(response_list), status_code, headers)


class MockResponse():
    def __init__(self, data):
        self.data = data


class MockEntry():
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.course = kwargs.get('course')
        self.email = kwargs.get('email')
        self.school = kwargs.get('school')
        self.sis_id = kwargs.get('sis_id')
