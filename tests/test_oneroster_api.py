import pytest
import mock
import random
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
    results = clever_api.make_call(call, limit=100, id=section)

    print()


@mock.patch('user_sync.connector.oneroster.CleverConnector.make_call')
def test_get_primary_key(mock_make_call, clever_api):
    data = [
        {'id': '58da8c6b894273be680001fc', 'name': 'Class 003, Homeroom - Stark - 0'},
        {'id': '58da8c6b894273be6800020a', 'name': 'Class 202, Homeroom - Jones - 0'},
        {'id': '58da8c6b894273be6800020a', 'name': 'Class 202, Homeroom - Jones - 0'},
        {'id': '58da8c6b894273be68000236', 'name': 'Grade 2 Math, Class 201 - Hammes - 3'},
        {'id': '58da8c6b894273be68000222', 'name': 'Kindergarten Math, Class 002 - Schoen - 1'},
        {'id': '58da8c6b894273be68000242', 'name': 'Mathematics, Class 601 - Goldner - 3'}
    ]

    mock_make_call.return_value = build_mock_response_object(data)

    z = clever_api.get_primary_key("sections", "Class 202, Homeroom - Jones - 0")
    z2 = clever_api.get_primary_key("sections", "Class 2022, Homeroom - Jones - 0")

    print()


def test_get_sections_for_course(clever_api):
    course = '5970d4dd35e9e69741000160'
    course_name = 'Class 001, Homeroom'

    # res = clever_api.clever_api.get_courses_with_http_info()

    res = clever_api.get_sections_for_course(course_name)

    print()


def test_samle_data(clever_api):
    c = clever_api.clever_api.get_sections().data
    clever_api.get_primary_key('sections', name='Introduction to Web Design - Corwin - 1')
    print()


def build_mock_response_object(objects):
    mock_results = []
    for o in objects:
        obj = mock.MagicMock()
        obj.data.id = o.get('id')
        obj.data.name = o.get('name')
        obj.data.course = o.get('course')
        mock_results.append(obj)
    return mock_results

