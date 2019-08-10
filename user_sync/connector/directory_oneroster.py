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

import itertools
import re
import string

import oneroster
import six

import user_sync.config
import user_sync.connector.helper
import user_sync.helper
import user_sync.identity_type
from user_sync.error import AssertionException
from user_sync.helper import CSVAdapter
from collections import OrderedDict


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
    :type state: OnerosterDirectoryConnector
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
        self.token_map = self.options.get('file_path')
        if self.token_map:
            if self.options['connection']['platform'] != 'clever':
                raise AssertionException('Token map can only be used with Clever')
            if self.options['connection']['access_token']:
                self.logger.warning("Warning: access_token will not be used because token CSV was supplied")
            self.token_map = self.load_token_map()

    @staticmethod
    def get_options(caller_config):

        connection_config = caller_config.get_dict_config('connection', True)
        connection_builder = user_sync.config.OptionsBuilder(connection_config)
        connection_builder.require_string_value('platform')
        connection_builder.require_string_value('host')
        connection_builder.set_int_value('page_size', 1000)
        connection_builder.set_int_value('max_users', 0)
        connection_options = connection_builder.get_options()

        mapping_config = caller_config.get_dict_config('mapping', True)
        mapping_builder = user_sync.config.OptionsBuilder(mapping_config)
        mapping_builder.set_string_value('mode','standard')
        mapping_options = mapping_builder.get_options()

        o = mapping_config.get_dict_config('product_mapping')
        o_builder = user_sync.config.OptionsBuilder(o)
        o_builder.require_string_value('type')
        o_builder.require_value('source',(str,list))
        o_builder.set_bool_value('secure_credential', False)
        mapping_options.update(o_builder.get_options())

        o = mapping_config.get_dict_config('standard_mapping')
        o_builder = user_sync.config.OptionsBuilder(o)
        o_builder.set_string_value('access_token', None)
        o_builder.set_string_value('client_id', None)
        o_builder.set_string_value('client_secret', None)
        o_builder.set_value('match_groups_by', (str, list), 'name')
        o_builder.set_string_value('key_identifier', None)
        o_builder.set_string_value('all_users_filter', 'users')
        o_builder.set_string_value('default_group_filter', 'classes')
        o_builder.set_string_value('default_user_filter', 'students')
        o_builder.set_string_value('group_delimiter', '::')
        mapping_options.update(o_builder.get_options())

        attr_builder = user_sync.config.OptionsBuilder(caller_config)
        attr_builder.set_string_value('user_email_format', six.text_type('{email}'))
        attr_builder.set_string_value('user_given_name_format', six.text_type('{givenName}'))
        attr_builder.set_string_value('user_surname_format', six.text_type('{familyName}'))
        attr_builder.set_string_value('user_country_code_format', None)
        attr_builder.set_string_value('user_username_format', None)
        attr_builder.set_string_value('user_domain_format', None)
        attr_builder.set_string_value('user_identity_type', None)
        attr_builder.set_string_value('user_identity_type_format', None)
        attr_options = attr_builder.get_options()

        builder = user_sync.config.OptionsBuilder(caller_config)
        builder.set_dict_value('include_only', {})
        options = builder.get_options()

        options['attributes'] = attr_options
        options['connection'] = connection_options
        options['mapping'] = mapping_options
        return options

    def load_token_map(self):
        """
        Load token mapping from CSV -- Clever sync only.  This overrides the access_token completely.
        :return:
        """
        return list(CSVAdapter.read_csv_rows(self.options['file_path']))


    def load_users_and_groups(self, groups, extended_attributes, all_users):
        """
        description: Leverages class components to return a user list, that will be sent to UMAPI
        :type groups: list(str)
        :type extended_attributes: list(str)
        :type all_users: bool
        :rtype (bool, iterable(dict))
        """

        self.options['extended_attributes'] = extended_attributes
        api_options = self.options['connection']
        api_options['key_identifier'] = self.options['schema']['key_identifier']
        api_options['match_on'] = self.options['schema']['match_groups_by']
        max_user_count = api_options['max_users']
        limit_users = max_user_count > 0

        connector_class = self.get_connector(api_options['platform'])
        parsed_groups = self.parse_yaml_groups(groups)

        self.record_handler = RecordHandler(self.logger, self.options)
        self.api = connector_class(**api_options)

        if self.token_map:
            users_by_key = self.get_users_for_tokens()
        else:
            users_by_key = self.get_mapped_users(parsed_groups)
            if all_users:
                self.update_user_dict(users_by_key, self.get_all_users())

        limited_msg = "(limit applied)" if limit_users else ""
        self.logger.info("Api returns " + str(len(users_by_key)) + " total users " + limited_msg)
        if limit_users and not self.token_map:
            self.logger.info("Enforcing user limit of: " + str(max_user_count) + " users")
            return six.itervalues(dict(itertools.islice(users_by_key.items(), max_user_count)))
        else:
            return six.itervalues(users_by_key)

    def update_user_dict(self, user_dict, new_users, additional_groups=None):
        for k, v in six.iteritems(new_users):
            if additional_groups:
                v['groups'].update(additional_groups)
            if k not in user_dict:
                user_dict[k] = v
            else:
                user_dict[k]['groups'].update(v['groups'])

    def get_users_for_tokens(self):
        self.logger.info("Using token map for Clever - all/mapped user groups will be ignored... ")
        user_dict = OrderedDict()
        for entry in self.token_map:
            self.api.user_count = 0
            self.api.access_token = entry['token']
            new_users = self.get_all_users(groups=[entry['product']])
            self.update_user_dict(user_dict, new_users)
        return user_dict

    def get_all_users(self, groups=None):
        user_dict = OrderedDict()
        response = self.api.get_users(user_filter=self.options['schema']['all_users_filter'])
        new_users = self.record_handler.parse_results(response)
        self.update_user_dict(user_dict, new_users, groups)
        return user_dict

    def get_mapped_users(self, groups):

        user_dict = OrderedDict
        for group_filter in groups:
            groups_names = groups[group_filter]
            for group_name in groups_names:
                for user_group in groups_names[group_name]:
                    user_filter = groups_names[group_name][user_group]
                    response = self.api.get_users(
                        group_filter=group_filter,
                        group_name=group_name,
                        user_filter=user_filter,
                    )
                    new_users = self.record_handler.parse_results(response)
                    self.update_user_dict(user_dict, new_users, [user_group])
        return user_dict

    def get_connector(self, name):
        if name.lower() == 'clever':
            return oneroster.CleverConnector
        elif name.lower() == 'classlink':
            return oneroster.ClasslinkConnector
        else:
            raise NotImplementedError("Unrecognized platform: '" + name +
                                      "'.  Supported are: [classlink, clever].")

    def validate_group_string(self, string, delim):

        if delim not in string:
            return False

        if len(string.split(delim)) != 3 or re.search('.*(:::).*', string):
            msg = "Invalid group syntax: {0}\n" \
                  "Syntax should be of form 'group_filter{1}group_name{1}user_filter'"
            raise ValueError(msg.format(string, delim))
        return True

    def parse_yaml_groups(self, groups_list):
        """
        description: parses group options from user-sync.config file into a nested dict
        {{Key (group_filter):
            (Value) {Key (group_name):
                            (Value) user_filter}}
        :type groups_list: set(str) from user-sync-config-ldap.yml
        :rtype: iterable(dict)
        """
        allowed_groups = ['classes', 'courses', 'schools', 'sections']
        allowed_users = ['students', 'teachers', 'users']
        delim = self.options['schema']['group_delimiter']
        groups = {}
        for text in groups_list:
            if self.validate_group_string(text, delim):
                group_filter, group_name, user_filter = text.lower().split(delim)

                if self.options['connection']['platform'] == 'clever':
                    group_filter = group_filter.replace('classes', 'sections')
                elif self.options['connection']['platform'] == 'classlink':
                    group_filter = group_filter.replace('sections', 'classes')
                group_filter = group_filter.replace('orgs', 'schools')

                if group_filter not in allowed_groups:
                    raise ValueError(
                        "Bad group type: " + group_filter + " for " + text
                        + ", valid are: " + ', '.join(allowed_groups))
                if user_filter not in allowed_users:
                    raise ValueError(
                        "Bad user type: " + group_filter + " for " + text
                        + ", valid are: " + ', '.join(allowed_users))

                if group_filter not in groups:
                    groups[group_filter] = {group_name: {}}
                elif group_name not in groups[group_filter]:
                    groups[group_filter][group_name] = {}
                groups[group_filter][group_name].update({text: user_filter})
            else:
                group_filter = self.options['schema']['default_group_filter']
                user_filter = self.options['schema']['default_user_filter']
                if group_filter not in groups:
                    groups[group_filter] = {text: {}}
                elif text not in groups[group_filter]:
                    groups[group_filter][text] = {}
                groups[group_filter][text].update({text: user_filter})
        return groups


class RecordHandler:
    def __init__(self, logger, options):
        self.logger = logger
        self.options = options
        self.inclusions = options['schema']['include_only']
        self.key_identifier = options['schema']['key_identifier']
        self.extended_attributes = options.get('extended_attributes')
        self.user_identity_type = user_sync.identity_type.parse_identity_type(options['user_identity_type'])
        self.user_identity_type_formatter = OneRosterValueFormatter(options['user_identity_type_format'])
        self.user_email_formatter = OneRosterValueFormatter(options['user_email_format'])
        self.user_username_formatter = OneRosterValueFormatter(options['user_username_format'])
        self.user_domain_formatter = OneRosterValueFormatter(options['user_domain_format'])
        self.user_given_name_formatter = OneRosterValueFormatter(options['user_given_name_format'])
        self.user_surname_formatter = OneRosterValueFormatter(options['user_surname_format'])
        self.user_country_code_formatter = OneRosterValueFormatter(options['user_country_code_format'])

        if self.inclusions != {}:
            self.logger.info("Note: inclusion filters are applied: " + str(self.inclusions))

    def parse_results(self, result_set):
        """
        description: parses through user_list from API calls, to create final user objects
        :type result_set: list(dict())
        :rtype users_dict: dict(constructed user objects)
        """

        users_dict = {}
        for user in result_set:
            returned_user = self.create_user_object(user)
            if returned_user is not None:
                users_dict[user[self.key_identifier]] = returned_user
        return users_dict

    def create_user_object(self, record):
        """
        description: Using user's API information to construct final user objects
        :type record: dict()
        :rtype: user: dict(user object)
        """

        if self.exclude_user(record):
            return

        attribute_warning = "No %s attribute (%s) for user with key: %s, defaulting to %s"
        source_attributes = {}

        key = record.get(self.key_identifier)

        if not key:
            self.logger.warning('Skipping user with id %s: no user key found (%s)', key, self.key_identifier)
            return

        email, last_attribute_name = self.user_email_formatter.generate_value(record)
        email = email.strip() if email else None
        if not email:
            if last_attribute_name is not None:
                self.logger.warning('Skipping user with id %s: empty email attribute (%s)', key, last_attribute_name)
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
                self.logger.warning('Skipping user with key %s: %s', key, e)
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

        user['groups'] = set()
        if self.extended_attributes:
            for attr in self.extended_attributes:
                source_attributes[attr] = OneRosterValueFormatter.get_attribute_value(record, attr)
        user['source_attributes'] = source_attributes.copy()
        return user

    def exclude_user(self, record):
        """
        desciption: filters out users according to the include_only values provided on connector-oneroster.yml
        :type record: dict()
        :rtype: bool
        """

        for key, value in self.inclusions.items():
            try:
                if self.decode_string(record.get(key)) not in self.decode_string(value):
                    return True
            except:
                self.logger.warning("No key for filtering attribute " + key + " for user " + record['email'])
                return True

        return False

    def decode_string(self, string):
        if not string:
            return
        try:
            decoded = string.decode()
        except:
            decoded = str(string)
        return decoded.lower().strip()


class OneRosterValueFormatter(object):

    def __init__(self, string_format):
        """
        The format string must be a unicode or ascii string
        """
        if string_format is None:
            attribute_names = []
        else:
            string_format = six.text_type(string_format)  # force unicode so attribute values are unicode
            formatter = string.Formatter()
            attribute_names = [six.text_type(item[1]) for item in formatter.parse(string_format) if item[1]]
        self.string_format = string_format
        self.attribute_names = attribute_names

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
        if isinstance(attribute_values, list):
            attribute_values = [cls.decode_attribute(val, attribute_name) for val in attribute_values]
            return attribute_values[0] if first_only or len(attribute_values) == 1 else attribute_values
        elif attribute_values:
            return cls.decode_attribute(attribute_values, attribute_name)
        return None

    @classmethod
    def decode_attribute(cls, attr, attr_name):
        try:
            return attr.decode()
        except UnicodeError as e:
            raise AssertionException("Encoding error in value of attribute '%s': %s" % (attr_name, e))
        except:
            return attr
