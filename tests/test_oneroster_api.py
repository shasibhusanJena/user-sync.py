import pytest
import mock
import random
import urllib3
import user_sync.connector.oneroster as oneroster


@pytest.fixture()
def clever_api():
    options = {
        'client_id': '5d8a7b5eff6cbe25bc6e',
        'client_secret': 'ec6d2c060987e32cbe785f7f1a58a307a04cf0a4',
        'key_identifier': 'sourcedId',
        'page_size': 1000,
        'max_user_limit': 0
    }

    return oneroster.CleverConnector(options)


def test_simple_filters(clever_api):
    x = clever_api.translate(group_filter='sections', user_filter='students', name='classname')


def test_make_call(clever_api):
    section = "'58da8c6a894273be68000184'"
    # 31 Users

    call = clever_api.clever_api.get_section(id='58da8c6a894273be68000184')
 #   results = clever_api.make_call(call, limit=100, id=section)

    print()


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
    assert logs == 'No objects found for sections: Fake class\n'


def test_get_sections_for_course(clever_api):
    course = '5970d4dd35e9e69741000160'
    course_name = 'Class 001, Homeroom'
    # res = clever_api.clever_api.get_courses_with_http_info()
    res = clever_api.get_sections_for_course(course_name)
    print()


# def test_samle_data(clever_api):
#
#
#     c = clever_api.clever_api.get_sections_with_http_info()
#  #   clever_api.get_primary_key('sections', name='Introduction to Web Design - Corwin - 1')
#     print()



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
