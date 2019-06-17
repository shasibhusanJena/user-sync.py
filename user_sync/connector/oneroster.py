# from __future__ import print_function

import json
import logging
import time
import clever
import classlink_oneroster

from clever.rest import ApiException


# Github: https://github.com/vossen-adobe/classlink
# PyPI: https://pypi.org/project/classlink-oneroster/

def get_connector(options):
    platform = options['platform']
    if platform == 'classlink':
        return ClasslinkConnector(options)
    elif platform == 'clever':
        return CleverConnector(options)

    raise ModuleNotFoundError("No module for " + platform +
                              " was found. Supported are: [classlink, clever]")


def decode_string(string):
    try:
        decoded = string.decode()
    except:
        decoded = str(string)
    return decoded.lower().strip()


#
#
#
#
#
#

class ClasslinkConnector():
    """ Starts connection and makes queries with One-Roster API"""

    def __init__(self, options):
        self.logger = logging.getLogger("classlink")
        self.host_name = options['host']
        self.client_id = options['client_id']
        self.client_secret = options['client_secret']
        self.key_identifier = options['key_identifier']
        self.max_users = options['max_user_limit']
        self.page_size = str(options['page_size'])
        self.classlink_api = classlink_oneroster.ClasslinkAPI(self.client_id, self.client_secret)

    def get_users(self,
                  group_filter=None,  # Type of group (class, course, school)
                  group_name=None,  # Plain group name (Math 6)
                  user_filter=None,  # Which users: users, students, staff
                  request_type=None,  # Determines which logic is used (see below)
                  ):

        results = []
        if group_filter == 'courses':
            key_id = self.execute_actions('courses', group_name, self.key_identifier, 'key_identifier')
            if key_id.__len__() == 0:
                return results
            list_classes = self.execute_actions(group_filter, user_filter, key_id, 'course_classlist')
            for each_class in list_classes:
                results.extend(self.execute_actions('classes', user_filter, each_class, 'mapped_users'))
        elif request_type == 'all_users':
            results.extend(self.execute_actions(None, user_filter, None, 'all_users'))
        else:
            key_id = self.execute_actions(group_filter, None, group_name, 'key_identifier')
            if key_id.__len__() == 0:
                return results
            results.extend(self.execute_actions(group_filter, user_filter, key_id, 'mapped_users'))
        return results

    def execute_actions(self, group_filter, user_filter, identifier, request_type):
        result = []
        if request_type == 'all_users':
            url_request = self.construct_url(user_filter, None, '', None)
            result = self.make_call(url_request, 'all_users', None)
        elif request_type == 'key_identifier':
            if group_filter == 'courses':
                url_request = self.construct_url(user_filter, identifier, 'course_classlist', None)
                result = self.make_call(url_request, 'key_identifier', group_filter, user_filter)
            else:
                url_request = self.construct_url(group_filter, identifier, 'key_identifier', None)
                result = self.make_call(url_request, 'key_identifier', group_filter, identifier)
        elif request_type == 'mapped_users':
            base_filter = group_filter if group_filter == 'schools' else 'classes'
            url_request = self.construct_url(base_filter, identifier, request_type, user_filter)
            result = self.make_call(url_request, 'mapped_users', group_filter, group_filter)
        elif request_type == 'course_classlist':
            url_request = self.construct_url("", identifier, 'users_from_course', None)
            result = self.make_call(url_request, request_type, group_filter)
        return result

    def construct_url(self, base_string_seeking, id_specified, request_type, users_filter):
        if request_type == 'course_classlist':
            url_ender = 'courses/?limit=' + self.page_size + '&offset=0'
        elif request_type == 'users_from_course':
            url_ender = 'courses/' + id_specified + '/classes?limit=' + self.page_size + '&offset=0'
        elif users_filter is not None:
            url_ender = base_string_seeking + '/' + id_specified + '/' + users_filter + '?limit=' + self.page_size + '&offset=0'
        else:
            url_ender = base_string_seeking + '?limit=' + self.page_size + '&offset=0'
        return self.host_name + url_ender

    def make_call(self, url, request_type, group_filter, group_name=None):
        user_list = []
        key = 'first'
        while key is not None:
            if key == 'first':
                response = self.classlink_api.make_roster_request(url)
            else:
                response = self.classlink_api.make_roster_request(response.links[key]['url'])
            if not response.ok:
                raise ValueError('Non Successful Response'
                                 + '  ' + 'status:' + str(response.status_code) + '  ' + 'message:' + str(response.reason))
            if request_type == 'key_identifier':
                other = 'course' if group_filter == 'courses' else 'classes'
                name_identifier, revised_key = ('name', 'orgs') if group_filter == 'schools' else ('title', other)
                for entry in json.loads(response.content).get(revised_key):
                    if decode_string(entry[name_identifier]) == decode_string(group_name):
                        try:
                            key_id = entry[self.key_identifier]
                        except ValueError:
                            raise ValueError('Key identifier: ' + self.key_identifier + ' not a valid identifier')
                        user_list.append(key_id)
                        return user_list[0]
            elif request_type == 'course_classlist':
                for ignore, entry in json.loads(response.content).items():
                    user_list.append(entry[0][self.key_identifier])
            else:
                for ignore, users in json.loads(response.content).items():
                    user_list.extend(users)
            if key == 'last' or int(response.headers._store['x-count'][1]) < int(self.page_size):
                break
            key = 'next' if 'next' in response.links else 'last'

        if not user_list:
            self.logger.warning("No " + request_type + " for " + group_filter + "  " + group_name)

        return user_list


#
#
#
#   Clever
#
#
#
#


class CleverConnector():

    def __init__(self, options):
        self.logger = logging.getLogger("clever")
        self.client_id = options['client_id']
        self.client_secret = options['client_secret']
        self.key_identifier = options['key_identifier']
        self.max_users = options['max_user_limit']
        self.page_size = str(options['page_size'])
        self.match = options['match']
        configuration = clever.Configuration()

        # client_id: 5d8a7b5eff6cbe25bc6e
        # client_secret: ec6d2c060987e32cbe785f7f1a58a307a04cf0a4
        # Our token: 3d65011e5b5d02c9de5cd129442a3b539de57cf6
        # configuration.username = self.client_id
        # configuration.password = self.client_secret
        # configuration.get_basic_auth_token()

        configuration.access_token = 'TEST_TOKEN'
        self.clever_api = clever.DataApi(clever.ApiClient(configuration))

    def get_users(self, **kwargs):
        return set([])

    def make_call(self, call, **params):

        # :param async bool
        # :param int limit:
        # :param str starting_after:
        # :param str ending_before:

        collected_objects = []
        while True:
            try:
                response = call(**params)
                new_objects = response[0].data
                if new_objects:
                    collected_objects.extend(new_objects)
                    params['starting_after'] = new_objects[-1].data.id
                else:
                    break
            except ApiException as e:
                raise e
            except Exception as e:
                raise e
        return collected_objects

    def get_primary_key(self, type, name):
        if self.match == 'id':
            return name

        call = {
            'sections': self.clever_api.get_sections_with_http_info,
            'courses': self.clever_api.get_sections_with_http_info,
            'schools': self.clever_api.get_sections_with_http_info,
        }.get(type)

        if not call:
            raise ValueError("Invalid group filter: " + type +
                             " is not a valid type. [sections, courses, schools]")

        objects = self.make_call(call)
        id_list = []
        for o in objects:
            try:
                if decode_string(getattr(o.data, self.match)) == decode_string(name):
                    id_list.append(o.data.id)
            except AttributeError:
                self.logger.warning("No property: '" + self.match +
                                    "' was found on " + type.rstrip('s') + " for entity '" + name + "'")
                break
        if not id_list:
            self.logger.warning("No objects found for " + type + ": " + name)
        return id_list

    def get_sections_for_course(self, name):
        id_list = self.get_primary_key('courses', name)
        sections = []

        for i in id_list:
            sections.extend(
                self.make_call(self.clever_api.get_sections_for_course_with_http_info, id=i))
        if not sections:
            self.logger.warning("No sections found for course '" + name + "'")
            return []
        else:
            return map(lambda x: x.data.id, sections)

    def get_users_for_course(self, name, user_filter):
        calls = self.translate('sections',user_filter)
        sections = self.get_sections_for_course(name)
        user_list = []
        for s in sections:
            for c in calls:
                user_list.extend(self.make_call(c, id=s))
        if not user_list:
            self.logger.warning("No users found for course '" + name + "'")
        return user_list

    def translate(self, group_filter, user_filter):

        call = {
            'sections_students': [self.clever_api.get_students_for_section_with_http_info],
            'sections_teachers': [self.clever_api.get_teachers_for_section_with_http_info],
            'sections_users': [self.clever_api.get_students_for_section_with_http_info,
                               self.clever_api.get_teachers_for_section_with_http_info],

            'courses_students': [self.get_users_for_course],
            'courses_teachers': [self.get_users_for_course],
            'courses_users': [self.get_users_for_course, self.get_users_for_course],

            'schools_students': [self.clever_api.get_students_for_school_with_http_info],
            'schools_teachers': [self.clever_api.get_teachers_for_school_with_http_info],
            'schools_users': [self.clever_api.get_students_for_school_with_http_info,
                              self.clever_api.get_teachers_for_school_with_http_info],

            'all_students' : [self.clever_api.get_students_with_http_info],
            'all_teachers' : [self.clever_api.get_teachers_with_http_info],
            'all_users' : [self.clever_api.get_students_with_http_info,
                           self.clever_api.get_teachers_with_http_info],
        }.get(group_filter + "_" + user_filter)

        if not call:
            raise ValueError("Unrecognized method request: 'get_" + user_filter + "_for_" + group_filter + "'")
        return call