# Copyright (c) 2016-2017 Adobe Systems Incorporated.  All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in allls

# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
import six
import re
import string

import user_sync.config
import user_sync.connector.helper
import user_sync.helper
import user_sync.identity_type
from user_sync.error import AssertionException

from user_sync.connector.oneroster import OneRoster


def connector_metadata():
    metadata = {
        'name': OneRosterConnector.name
    }
    return metadata


def connector_initialize(options):
    """
    :type options: dict
    """
    return OneRosterConnector(options)


def connector_load_users_and_groups(state, groups=None, extended_attributes=None, all_users=True):
    """
    :type state: LDAPDirectoryConnector
    :type groups: Optional(list(str))
    :type extended_attributes: Optional(list(str))
    :type all_users: bool
    :rtype (bool, iterable(dict))
    """
    return state.load_users_and_groups(groups or [], extended_attributes or [], all_users)


class OneRosterConnector(object):
    name = 'oneroster'

    def __init__(self, caller_options):
        caller_config = user_sync.config.DictConfig('%s configuration' % self.name, caller_options)
        self.options = self.get_options(caller_config)
        self.logger = user_sync.connector.helper.create_logger(self.options)
        caller_config.report_unused_values(self.logger)
        self.logger.debug('%s initialized with options: %s', self.name, self.options)

    @staticmethod
    def get_options(caller_config):
        builder = user_sync.config.OptionsBuilder(caller_config)
        builder.require_string_value('client_id')
        builder.require_string_value('client_secret')
        builder.require_string_value('host')
        builder.set_string_value('all_users_filter', 'users')
        builder.set_string_value('limit', 1000)
        builder.set_string_value('key_identifier', 'sourcedId')
        builder.set_string_value('logger_name', 'oneroster')
        builder.set_string_value('country_code', None)
        builder.set_string_value('user_email_format', six.text_type('{email}'))
        builder.set_string_value('user_given_name_format', six.text_type('{givenName}'))
        builder.set_string_value('user_surname_format', six.text_type('{familyName}'))
        builder.set_string_value('user_country_code_format', six.text_type('{countryCode}'))
        builder.set_string_value('user_username_format', None)
        builder.set_string_value('user_domain_format', None)
        builder.set_string_value('user_identity_type', None)
        builder.set_string_value('user_identity_type_format', None)

        return builder.get_options()

    def load_users_and_groups(self, groups, extended_attributes, all_users):
        """
        description: Leverages class components to return a user list, that will be sent to UMAPI
        :type groups: list(str)
        :type extended_attributes: list(str)
        :type all_users: bool
        :rtype (bool, iterable(dict))
        """
        rh = RecordHandler(self.options, logger=self.logger)
        conn = Connection(self.logger, self.options)
        groups_from_yml = self.parse_yml_groups(groups)
        users_by_key = {}
        for group_filter in groups_from_yml:
            inner_dict = groups_from_yml[group_filter]
            for group_name in inner_dict:
                for user_group in inner_dict[group_name]:
                    user_filter = inner_dict[group_name][user_group]
                    response = conn.list_api_response_handler(
                        group_filter, group_name, user_filter, 'mapped_users')
                    new_users_by_key = rh.parse_results(response, self.options['key_identifier'], extended_attributes)
                    for key, value in six.iteritems(new_users_by_key):
                        if key not in users_by_key:
                            users_by_key[key] = value
                        users_by_key[key]['groups'].add(user_group)
        if all_users:
            response = conn.list_api_response_handler("", "", self.options['all_users_filter'], 'all_users')
            new_all_users = rh.parse_results(response, self.options['key_identifier'], extended_attributes)
            for key, value in six.iteritems(new_all_users):
                if key not in users_by_key:
                    users_by_key[key] = value

        return six.itervalues(users_by_key)

    def parse_yml_groups(self, groups_list):
        """
        description: parses group options from user-sync.config file into a nested dict
         with Key: group_filter for the outter dict, Value: being the nested
        dict {Key: group_name, Value: user_filter}
        :type groups_list: set(str) from user-sync-config-ldap.yml
        :rtype: iterable(dict)
        """
        full_dict = {}
        for text in groups_list:
            try:
                group_filter, group_name, user_filter = text.lower().split("::")
            except ValueError:
                raise ValueError("Incorrect MockRoster Group Syntax: " + text +
                                 " \nRequires values for group_filter, group_name, user_filter."
                                 " With '::' separating each value")
            if group_filter not in {'classes', 'courses', 'schools'}:
                raise ValueError("Incorrect group_filter: " + group_filter +
                                 " .... must be either: classes, courses, or schools")
            if user_filter not in {'students', 'teachers', 'users'}:
                raise ValueError("Incorrect user_filter: " + user_filter +
                                 " .... must be either: students, teachers, or users")
            if group_filter not in full_dict:
                full_dict[group_filter] = {group_name: {}}
            elif group_name not in full_dict[group_filter]:
                full_dict[group_filter][group_name] = {}
            full_dict[group_filter][group_name].update({text: user_filter})
        return full_dict


class Connection:
    """ Starts connection and makes queries with One-Roster API"""

    def __init__(self, logger, options):
        self.logger = logger
        self.host_name = options['host']
        self.limit = options['limit']
        self.client_id = options['client_id']
        self.client_secret = options['client_secret']
        self.oneroster = OneRoster(self.client_id, self.client_secret)
        self.key_identifier = options['key_identifier']

    def list_api_response_handler(self, group_filter, group_name, user_filter, finder_option):
        list_api_results = []
        if group_filter == 'courses':
            key_id = self.list_item_retriever('courses', group_name, self.key_identifier, 'key_identifier')
            if key_id.__len__() == 0:
                return list_api_results
            list_classes = self.list_item_retriever(group_filter, user_filter, key_id,'course_classlist')
            for each_class in list_classes:
                list_api_results.extend(self.list_item_retriever('classes', user_filter, each_class, 'mapped_users'))

        elif finder_option == 'all_users':
            list_api_results.extend(self.list_item_retriever(None, user_filter, None, 'all_users'))

        else:
            key_id = self.list_item_retriever(group_filter, None, group_name, 'key_identifier')
            if key_id.__len__() == 0:
                return list_api_results
            list_api_results.extend(self.list_item_retriever(group_filter, user_filter, key_id, 'mapped_users'))
        return list_api_results

    def string_first_url_builder(self, base_string_seeking, id_specified, finder_option, users_filter):
        if finder_option == 'course_classlist':
            url_ender = 'courses/?limit=' + self.limit + '&offset=0'

        elif finder_option == 'users_from_course':
            url_ender = 'courses/' + id_specified + '/classes?limit=' + self.limit + '&offset=0'

        else:
            url_ender = base_string_seeking + '?limit=' + self.limit + '&offset=0'

        if users_filter is not None:
            url_ender = base_string_seeking + '/' + id_specified + '/' + users_filter + '?limit=' + self.limit + '&offset=0'

        return self.host_name + url_ender


    def list_item_retriever(self, group_filter, user_filter, identifier, finder_option):
        list_api_results = []

        if finder_option == 'all_users':
            url_request = self.string_first_url_builder(user_filter, None, '', None)
            list_api_results = self.start_call(url_request, 'all_users', None)

        elif finder_option == 'key_identifier':
            if group_filter == 'courses':
                url_request = self.string_first_url_builder(user_filter, identifier, 'course_classlist', None)
                list_api_results = self.start_call(url_request, 'key_identifier', group_filter, user_filter)
            else:
                url_request = self.string_first_url_builder(group_filter, identifier, 'key_identifier', None)
                list_api_results = self.start_call(url_request, 'key_identifier', group_filter, identifier)

        elif finder_option == 'mapped_users':
            base_filter = group_filter if group_filter == 'schools' else 'classes'
            url_request = self.string_first_url_builder(base_filter, identifier, finder_option, user_filter)
            list_api_results = self.start_call(url_request, 'mapped_users', group_filter, group_filter)

        elif finder_option == 'course_classlist':
            url_request = self.string_first_url_builder("", identifier, 'users_from_course', None)
            list_api_results = self.start_call(url_request, finder_option, group_filter)

        return list_api_results
    def start_call(self, url_request, finder_option, group_filter, group_name=None):
        list_api_results = []
        key = 'first'
        while key is not None:
            response = self.oneroster.make_roster_request(url_request) \
                if key == 'first' \
                else self.oneroster.make_roster_request(response.links[key]['url'])
            if response.ok is not True:
                status = response.status_code
                message = response.reason
                raise ValueError('Non Successful Response'
                                 + '  ' + 'status:' + str(status) + '  ' + 'message:' + str(message))
            if finder_option == 'key_identifier':
                other = 'course' if group_filter == 'courses' else 'classes'
                name_identifier, revised_key = ('name', 'orgs') if group_filter == 'schools' else ('title', other)
                for each_class in json.loads(response.content).get(revised_key):
                    if self.encode_str(each_class[name_identifier]) == self.encode_str(group_name):
                        try:
                            key_id = each_class[self.key_identifier]
                        except ValueError:
                            raise ValueError('Key identifier: ' + self.key_identifier + ' not a valid identifier')
                        list_api_results.append(key_id)
                        return list_api_results[0]

            elif finder_option == 'course_classlist':
                for ignore, each_class in json.loads(response.content).items():
                        list_api_results.append(each_class[0][self.key_identifier])

            else:
                for ignore, users in json.loads(response.content).items():
                    list_api_results.extend(users)
            if key == 'last' or int(response.headers._store['x-count'][1]) < int(self.limit):
                break
            key = 'next' if 'next' in response.links else 'last'

        if list_api_results.__len__() == 0:
            self.logger.warning("No " + finder_option + " for " + group_filter + "  " + group_name)

        return list_api_results

    def encode_str(self, text):
        return re.sub(r'(\s)', '', text).lower()


class RecordHandler:
    def __init__(self, options, logger):
        self.logger = logger
        self.country_code = options['country_code']
        self.user_identity_type = user_sync.identity_type.parse_identity_type(options['user_identity_type'])
        self.user_identity_type_formatter = OneRosterValueFormatter(options['user_identity_type_format'])
        self.user_email_formatter = OneRosterValueFormatter(options['user_email_format'])
        self.user_username_formatter = OneRosterValueFormatter(options['user_username_format'])
        self.user_domain_formatter = OneRosterValueFormatter(options['user_domain_format'])
        self.user_given_name_formatter = OneRosterValueFormatter(options['user_given_name_format'])
        self.user_surname_formatter = OneRosterValueFormatter(options['user_surname_format'])
        self.user_country_code_formatter = OneRosterValueFormatter(options['user_country_code_format'])

    def parse_results(self, result_set, key_identifier, extended_attributes):
        """
        description: parses through user_list from API calls, to create final user objects
        :type result_set: list(dict())
        :type extended_attributes: list(str)
        :type key_identifier: str()
        :rtype users_dict: dict(constructed user objects)
        """
        users_dict = {}
        for user in result_set:
            returned_user = self.create_user_object(user, key_identifier, extended_attributes)
            if returned_user is not None:
                users_dict[user[key_identifier]] = returned_user
        return users_dict

    def create_user_object(self, record, key_identifier, extended_attributes):
        """
        description: Using user's API information to construct final user objects
        :type record: dict()
        :type extended_attributes: list(str)
        :type key_identifier: str()
        :rtype: formatted_user: dict(user object)
        """
        attribute_warning = "No %s attribute (%s) for user with key: %s, defaulting to %s"
        source_attributes = {}
        key = record.get(key_identifier)
        if key is None or record.get('status') != 'active':
            return
        email, last_attribute_name = self.user_email_formatter.generate_value(record)
        email = email.strip() if email else None
        if not email:
            if last_attribute_name is not None:
                self.logger.warning('Skipping user with id %s: empty email attribute (%s)',  key, last_attribute_name)
        user = user_sync.connector.helper.create_blank_user()
        source_attributes['email'] = email
        user['email'] = email
        identity_type, last_attribute_name = self.user_identity_type_formatter.generate_value(record)
        if last_attribute_name and not identity_type:
            self.logger.warning(attribute_warning, 'identity_type', last_attribute_name, key, self.user_identity_type)
        source_attributes['identity_type'] = identity_type
        if not identity_type:
            user['identity_type'] = self.user_identity_type
        else:
            try:
                user['identity_type'] = user_sync.identity_type.parse_identity_type(identity_type)
            except AssertionException as e:
                self.logger.warning('Skipping user with key %s: %s', e, key)
        username, last_attribute_name = self.user_username_formatter.generate_value(record)
        username = username.strip() if username else None
        source_attributes['username'] = username
        if username:
            user['username'] = username
        else:
            if last_attribute_name:
                self.logger.warning(attribute_warning, 'identity_type', last_attribute_name, email, key)
            user['username'] = email
        domain, last_attribute_name = self.user_domain_formatter.generate_value(record)
        domain = domain.strip() if domain else None
        source_attributes['domain'] = domain
        if domain:
            user['domain'] = domain
        elif username != email:
            user['domain'] = email[email.find('@') + 1:]
        elif last_attribute_name:
            self.logger.warning('No domain attribute (%s) for user with dn: %s', last_attribute_name, key)
        given_name_value, last_attribute_name = self.user_given_name_formatter.generate_value(record)
        source_attributes['givenName'] = given_name_value
        if given_name_value is not None:
            user['firstname'] = given_name_value
        elif last_attribute_name:
            self.logger.warning('No given name attribute (%s) for user with dn: %s', last_attribute_name, key)
        sn_value, last_attribute_name = self.user_surname_formatter.generate_value(record)
        source_attributes['familyName'] = sn_value
        if sn_value is not None:
            user['lastname'] = sn_value
        elif last_attribute_name:
            self.logger.warning('No surname attribute (%s) for user with dn: %s', last_attribute_name, key)
        c_value, last_attribute_name = self.user_country_code_formatter.generate_value(record)
        source_attributes['country'] = c_value
        if c_value is not None:
            user['country'] = c_value.upper()
        elif c_value is None:
            user['country'] = self.country_code
        elif last_attribute_name:
            self.logger.warning('No country code attribute (%s) for user with dn: %s', last_attribute_name)
        user['groups'] = set()
        if extended_attributes is not None:
            for extended_attribute in extended_attributes:
                extended_attribute_value = OneRosterValueFormatter.get_attribute_value(record, extended_attribute)
                source_attributes[extended_attribute] = extended_attribute_value
        user['source_attributes'] = source_attributes.copy()
        return user


class OneRosterValueFormatter(object):
    encoding = 'utf8'

    def __init__(self, string_format):
        """
        The format string must be a unicode or ascii string: see notes above about being careful in Py2!
        """
        if string_format is None:
            attribute_names = []
        else:
            string_format = six.text_type(string_format)    # force unicode so attribute values are unicode
            formatter = string.Formatter()
            attribute_names = [six.text_type(item[1]) for item in formatter.parse(string_format) if item[1]]
        self.string_format = string_format
        self.attribute_names = attribute_names

    def get_attribute_names(self):
        """
        :rtype list(str)
        """
        return self.attribute_names

    def generate_value(self, record):
        """
        :type record: dict
        :rtype (unicode, unicode)
        """
        result = None
        attribute_name = None
        if self.string_format is not None:
            values = {}
            for attribute_name in self.attribute_names:
                value = self.get_attribute_value(record, attribute_name, first_only=True)
                if value is None:
                    values = None
                    break
                values[attribute_name] = value
            if values is not None:
                result = self.string_format.format(**values)
        return result, attribute_name

    @classmethod
    def get_attribute_value(cls, attributes, attribute_name, first_only=False):
        """
        The attribute value type must be decodable (str in py2, bytes in py3)
        :type attributes: dict
        :type attribute_name: unicode
        :type first_only: bool
        """
        attribute_values = attributes.get(attribute_name)
        if attribute_values:
            try:
                if first_only or len(attribute_values) == 1:
                    attr = attribute_values if isinstance(attribute_values, six.string_types) else attribute_values[0]
                    return attr if isinstance(attr, six.string_types) else attr.decode(cls.encoding)
                else:
                    return [(val if isinstance(val, six.string_types)
                             else val.decode(cls.encoding)) for val in attribute_values]
            except UnicodeError as e:
                raise AssertionException("Encoding error in value of attribute '%s': %s" % (attribute_name, e))
        return None
