import collections
import re

import mock
import pytest
import urllib3

import user_sync.connector.oneroster as oneroster


@pytest.fixture()
def clever_api():
    options = {
        'client_id': '5d8a7b5eff6cbe25bc6e',
        'client_secret': 'ec6d2c060987e32cbe785f7f1a58a307a04cf0a4',
        'key_identifier': 'sourcedId',
        'page_size': 1000,
        'max_user_limit': 0,
        'match': 'name',
        'access_token': 'TEST_TOKEN'
    }

    return oneroster.CleverConnector(options)


@mock.patch('clever.DataApi.get_students_with_http_info')
@mock.patch('clever.DataApi.get_teachers_with_http_info')
def test_get_users(get_teachers, get_students, clever_api, mock_many_students, mock_teacher):

    # Empty response needed to end the make cap
    empty_repsonse = get_mock_api_response([])
    mock_student_response = [get_mock_api_response(mock_many_students), empty_repsonse]
    mock_teacher_response = [get_mock_api_response(mock_teacher), empty_repsonse]

    # Reset data
    get_students.side_effect = mock_student_response

    # Get students
    response = clever_api.get_users_raw(user_filter='students')
    expected = [x['id'] for x in mock_many_students]
    actual = [x.id for x in response]
    assert collections.Counter(expected) == collections.Counter(actual)

    # Reset data
    get_teachers.side_effect = mock_teacher_response

    response = clever_api.get_users_raw(user_filter='teachers')
    expected = [x['id'] for x in mock_teacher]
    actual = [x.id for x in response]
    assert collections.Counter(expected) == collections.Counter(actual)

    # Reset data
    get_students.side_effect = mock_student_response
    get_teachers.side_effect = mock_teacher_response

    # Get all users
    response = clever_api.get_users_raw(user_filter='users')
    expected = [x['id'] for x in mock_many_students]
    expected.append(mock_teacher[0]['id'])
    actual = [x.id for x in response]
    assert collections.Counter(expected) == collections.Counter(actual)


@mock.patch('clever.DataApi.get_students_for_section_with_http_info')
@mock.patch('clever.DataApi.get_teachers_for_section_with_http_info')
@mock.patch('user_sync.connector.oneroster.CleverConnector.get_primary_key')
def test_get_users_for_section(get_key, get_teachers, get_students, clever_api, mock_many_students, mock_teacher):

    # Empty response needed to end the make cap
    empty_repsonse = get_mock_api_response([])
    mock_student_response = [get_mock_api_response(mock_many_students), empty_repsonse]
    mock_teacher_response = [get_mock_api_response(mock_teacher), empty_repsonse]

    # Section key - not actually relevent here
    get_key.return_value = ['58da8c6b894273be680001fc']

    # Get students
    get_students.side_effect = mock_student_response
    response = clever_api.get_users_raw(user_filter='students',
                                        group_filter='sections',
                                        group_name='Class 003, Homeroom - Stark - 0')

    expected = [x['id'] for x in mock_many_students]
    actual = [x.id for x in response]
    assert collections.Counter(expected) == collections.Counter(actual)

    # Get students
    get_teachers.side_effect = mock_teacher_response
    response = clever_api.get_users_raw(user_filter='teachers',
                                        group_filter='sections',
                                        group_name='Class 003, Homeroom - Stark - 0')

    expected = [x['id'] for x in mock_teacher]
    actual = [x.id for x in response]
    assert collections.Counter(expected) == collections.Counter(actual)

    # Get all users
    get_students.side_effect = mock_student_response
    get_teachers.side_effect = mock_teacher_response
    response = clever_api.get_users_raw(user_filter='users',
                                        group_filter='sections',
                                        group_name='Class 003, Homeroom - Stark - 0')

    expected = [x['id'] for x in mock_many_students]
    expected.append(mock_teacher[0]['id'])
    actual = [x.id for x in response]
    assert collections.Counter(expected) == collections.Counter(actual)


@mock.patch('clever.DataApi.get_students_with_http_info')
def test_make_call(get_students, clever_api, mock_user_data):
    page_1 = get_mock_api_response(mock_user_data[0:2])
    page_2 = get_mock_api_response(mock_user_data[2:4])
    page_3 = get_mock_api_response([])

    get_students.side_effect = [page_1, page_2, page_3]

    results = clever_api.make_call(clever_api.clever_api.get_students_with_http_info)
    expected = [x['id'] for x in mock_user_data]
    actual = [x.data.id for x in results]
    assert collections.Counter(expected) == collections.Counter(actual)


@mock.patch('user_sync.connector.oneroster.CleverConnector.make_call')
def test_get_primary_key(mock_make_call, clever_api, log_stream, mock_section_data):
    stream, logger = log_stream
    clever_api.logger = logger
    mock_make_call.return_value = get_mock_api_response_dataonly(mock_section_data)

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

    # Get ID based on SIS ID
    clever_api.match = "sis_id"
    keys = clever_api.get_primary_key("sections", "161-875-2356")
    assert keys == ['58da8c6b894273be68000236']

    # Get ID based on course
    clever_api.match = 'course'
    keys = clever_api.get_primary_key("sections", "Math 101")
    assert keys == ['58da8c6b894273be680001fc']

    pytest.raises(ValueError, clever_api.get_primary_key, type='bad', name='bad')


@mock.patch('user_sync.connector.oneroster.CleverConnector.make_call')
@mock.patch('user_sync.connector.oneroster.CleverConnector.get_primary_key')
def test_get_sections_for_course(get_key, make_call, clever_api, mock_section_data):
    # Sections for ID 1
    data_1 = mock_section_data[0:2]

    # Sections for ID 2
    data_2 = mock_section_data[3:5]

    # These are the id's found for course name (totally arbitrary here)
    get_key.return_value = ['12345', '67892']

    # Each time we call, we get a response
    make_call.side_effect = [get_mock_api_response_dataonly(data_1),
                             get_mock_api_response_dataonly(data_2)]

    # Combine ID fields from data 1 and 2
    expected = [map(lambda x: x['id'], data) for data in [data_1, data_2]]
    expected = [y for x in expected for y in x]

    result = clever_api.get_sections_for_course('Math 101')
    assert collections.Counter(expected) == collections.Counter(result)


@mock.patch('user_sync.connector.oneroster.CleverConnector.make_call')
@mock.patch('user_sync.connector.oneroster.CleverConnector.get_sections_for_course')
def test_get_users_for_course(get_sections, make_call, clever_api, mock_user_data):
    mock_students = mock_user_data[0:2]
    mock_teachers = mock_user_data[2:4]

    get_sections.return_value = ['12345']
    make_call.side_effect = [
        get_mock_api_response_dataonly(mock_students),
        get_mock_api_response_dataonly(mock_teachers)
    ]

    response = clever_api.get_users_for_course("Math 9", "users")
    expected = [x['id'] for x in mock_user_data]
    actual = [x.data.id for x in response]
    assert collections.Counter(expected) == collections.Counter(actual)


def test_translate(clever_api):
    calls = clever_api.translate('sections', 'users')
    assert calls[0] == clever_api.clever_api.get_students_for_section_with_http_info
    assert calls[1] == clever_api.clever_api.get_teachers_for_section_with_http_info
    pytest.raises(ValueError, clever_api.translate, user_filter="x", group_filter="y")



#def test_objectmapper(clever_api):


def get_mock_api_response(data, status_code=200, headers=None):
    headers = urllib3.response.HTTPHeaderDict(headers)
    response_list = [MockResponse(MockEntry(**d)) for d in data]
    return (MockResponse(response_list), status_code, headers)


def get_mock_api_response_dataonly(data):
    return get_mock_api_response(data)[0].data


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


#Not a real test - just for producing data
# def test_data_generator(clever_api):
#     res = clever_api.get_users(group_filter='sections',
#                                       user_filter='users',
#                                       group_name='Class 003, Homeroom - Stark - 0')
#     mock_many = [
#         {
#             'id': x.id,
#             'name': x.name,
#             'email': x.email,
#             'sis_id': x.sis_id,
#             'school': x.school
#         } for x in res
#     ]


@pytest.fixture()
def mock_section_data():
    return [
        {
            'id': '58da8c6b894273be680001fc',
            'name': 'Class 003, Homeroom - Stark - 0',
            'sis_id': '278-002-1020',
            'course': 'Math 101'
        },
        {
            'id': '58da8c6b894273be6800020a',
            'name': 'Class 202, Homeroom - Jones - 0',
            'sis_id': '341-356-1315',
            'course': 'Art 101'
        },
        {
            'id': '58da8c6b894273be5100020a',
            'name': 'Class 202, Homeroom - Jones - 0',
            'sis_id': '754-1523-6311',
            'course': 'Sci 101'
        },
        {
            'id': '58da8c6b894273be68000236',
            'name': 'Grade 2 Math, Class 201 - Hammes - 3',
            'sis_id': '161-875-2356',
            'course': 'Geo 101'
        },
        {
            'id': '58da8c6b894273be68000222',
            'name': 'Kindergarten Math, Class 002 - Schoen - 1',
            'sis_id': '958-163-2145',
            'course': 'Alg 101'},
        {
            'id': '58da8c6b894273be68000242',
            'name': 'Mathematics, Class 601 - Goldner - 3',
            'sis_id': '762-561-6723',
            'course': 'Shop 101'}
    ]


@pytest.fixture()
def mock_user_data():
    return [
        {
            'id': '58da8c6b894224000242',
            'email': 'z.steve@example.net',
            'name': {'first': 'Steve', 'last': 'Ziemann', 'middle': 'G'},
            'school': '58da8c58155b940248000007',
            'sis_id': '100095233'
        },
        {
            'id': '58da8c6b89486y677765',
            'email': 'julia.r@example.org',
            'name': {'first': 'Julia', 'last': 'Runolfsdottir', 'middle': 'B'},
            'school': '58da8c58155b940248000007',
            'sis_id': '108028995'
        },
        {
            'id': '58da8c6b89427512faef3f',
            'email': 'sisko.b@example.net',
            'name': {'first': 'Benjamin', 'last': 'Sisko', 'middle': 'J'},
            'school': '58da8c58155b940248000007',
            'sis_id': '1001234233'
        },
        {
            'id': '58da8c75ghgdsdf0242',
            'email': 'picard.j@example.org',
            'name': {'first': 'Jean Luc', 'last': 'Picard', 'middle': ''},
            'school': '58da8c58155b940248000007',
            'sis_id': '108062341'
        }
    ]


@pytest.fixture()
def mock_many_students():
    return [{'id': '58da8c63d7dc0ca06800043e', 'name': {'first': 'Karen', 'last': 'Harvey', 'middle': 'D'}, 'email': 'karen.h@example.net', 'sis_id': '173157322'},
            {'id': '58da8c63d7dc0ca068000443', 'name': {'first': 'Adrianna', 'last': 'Sawayn', 'middle': 'A'}, 'email': 'adrianna.s@example.org', 'sis_id': '176057934'},
            {'id': '58da8c63d7dc0ca06800045f', 'name': {'first': 'Jonathan', 'last': 'Dietrich', 'middle': 'G'}, 'email': 'd.jonathan@example.com', 'sis_id': '206776810'},
            {'id': '58da8c63d7dc0ca06800047a', 'name': {'first': 'George', 'last': "O'Connell", 'middle': 'S'}, 'email': 'o_george@example.org', 'sis_id': '235286679'},
            {'id': '58da8c63d7dc0ca068000497', 'name': {'first': 'Kevin', 'last': 'Herman', 'middle': 'B'}, 'email': 'h_kevin@example.net', 'sis_id': '265863904'},
            {'id': '58da8c63d7dc0ca0680004ca', 'name': {'first': 'Alice', 'last': 'Fadel', 'middle': 'J'}, 'email': 'f_alice@example.org', 'sis_id': '297056232'},
            {'id': '58da8c64d7dc0ca068000562', 'name': {'first': 'Mark', 'last': 'McGlynn', 'middle': 'A'}, 'email': 'm.mark@example.net', 'sis_id': '427573397'},
            {'id': '58da8c64d7dc0ca0680005aa', 'name': {'first': 'Mark', 'last': 'Hackett', 'middle': 'E'}, 'email': 'h.mark@example.org', 'sis_id': '495684672'},
            {'id': '58da8c64d7dc0ca0680005c0', 'name': {'first': 'Linda', 'last': 'Abernathy', 'middle': 'C'}, 'email': 'linda.a@example.com', 'sis_id': '508410312'},
            {'id': '58da8c64d7dc0ca0680005c3', 'name': {'first': 'Julianne', 'last': 'Dicki', 'middle': 'C'}, 'email': 'd.julianne@example.net', 'sis_id': '510492620'},
            {'id': '58da8c64d7dc0ca0680005e7', 'name': {'first': 'Tammy', 'last': 'Robel', 'middle': 'R'}, 'email': 'tammy_r@example.net', 'sis_id': '547417208'},
            {'id': '58da8c64d7dc0ca068000640', 'name': {'first': 'Marcia', 'last': 'Rippin', 'middle': 'R'}, 'email': 'r_marcia@example.org', 'sis_id': '635560230'},
            {'id': '58da8c64d7dc0ca06800064b', 'name': {'first': 'Margaret', 'last': 'Grant', 'middle': 'D'}, 'email': 'margaret_g@example.net', 'sis_id': '641257513'},
            {'id': '58da8c64d7dc0ca068000674', 'name': {'first': 'Florence', 'last': 'Rowe', 'middle': 'P'}, 'email': 'florence_r@example.org', 'sis_id': '674331356'},
            {'id': '58da8c65d7dc0ca068000698', 'name': {'first': 'Mary', 'last': 'Rosenbaum', 'middle': 'P'}, 'email': 'r.mary@example.com', 'sis_id': '710689080'},
            {'id': '58da8c65d7dc0ca0680006f4', 'name': {'first': 'Kimberly', 'last': 'Mraz', 'middle': 'R'}, 'email': 'm.kimberly@example.org', 'sis_id': '800017226'},
            {'id': '58da8c65d7dc0ca068000715', 'name': {'first': 'Diana', 'last': 'Monahan', 'middle': 'E'}, 'email': 'm.diana@example.net', 'sis_id': '830604811'},
            {'id': '58da8c65d7dc0ca06800077d', 'name': {'first': 'Vivian', 'last': 'Kris', 'middle': 'K'}, 'email': 'vivian_k@example.net', 'sis_id': '926639679'},
            {'id': '58da8c65d7dc0ca0680007ab', 'name': {'first': 'Vanessa', 'last': 'Farrell', 'middle': 'C'}, 'email': 'vanessa_f@example.org', 'sis_id': '963452890'},
            {'id': '58da8c65d7dc0ca0680007b0', 'name': {'first': 'Jeffrey', 'last': 'Hettinger', 'middle': 'A'}, 'email': 'h.jeffrey@example.org', 'sis_id': '967155729'}]


@pytest.fixture()
def mock_teacher():
    return [{'id': '58da8c5da7a7e5a64700009c', 'name': {'first': 'Jessica', 'last': 'Stark', 'middle': 'R'}, 'email': 'stark_jessica@example.net', 'sis_id': '70'}]
