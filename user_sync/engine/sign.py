import logging
from collections import defaultdict

import six

from user_sync import error, identity_type
from user_sync.config.common import DictConfig
from user_sync.connector.connector_sign import SignConnector
from user_sync.engine.umapi import AdobeGroup
from user_sync.error import AssertionException
from user_sync.helper import normalize_string


class SignSyncEngine:
    default_options = {
        'admin_roles': None,
        'create_users': False,
        'directory_group_filter': None,
        'entitlement_groups': [],
        'identity_types': [],
        'sign_only_limit': 200,
        'sign_orgs': [],
        'test_mode': False,
        'user_groups': []
    }
    name = 'sign_sync'
    DEFAULT_GROUP_NAME = 'default group'

    def __init__(self, caller_options):
        super().__init__()
        options = dict(self.default_options)
        options.update(caller_options)
        self.options = options
        self.logger = logging.getLogger(self.name)
        self.test_mode = options.get('test_mode')
        sync_config = DictConfig('<%s configuration>' % self.name, caller_options)
        self.user_groups = options['user_groups'] = sync_config.get_list('user_groups', True)
        if self.user_groups is None:
            self.user_groups = []
        self.user_groups = self._groupify(self.user_groups)
        self.entitlement_groups = self._groupify(sync_config.get_list('entitlement_groups'))
        self.identity_types = sync_config.get_list('identity_types', True)
        if self.identity_types is None:
            self.identity_types = ['adobeID', 'enterpriseID', 'federatedID']
        self.directory_user_by_user_key = {}
        # dict w/ structure - umapi_name -> adobe_group -> [set of roles]
        self.admin_roles = self._admin_role_mapping(sync_config)
        sign_orgs = sync_config.get_list('sign_orgs')
        self.connectors = {cfg.get('console_org'): SignConnector(cfg) for cfg in sign_orgs}
        # self.create_new_users = sync_config.get_bool("create_new_users")
        self.total_sign_user_count = set()
        self.sign_users_created_count = set()
        self.sign_users_removed_count = set()
        self.sign_users_updated_count = set()
        self.sign_users_with_matched_groups = set()
        self.sign_users_assigned_to_groups = set()
        self.sign_users_assigned_to_admin_role = set()
        self.action_summary = {}

    def run(self, directory_groups, directory_connector):
        """
        Run the Sign sync
        :param directory_groups:
        :param directory_connector:
        :return:
        """
        if self.test_mode:
            self.logger.info("Sign Sync disabled in test mode")
            return
        # directory_users = self.read_desired_user_groups(directory_groups, directory_connector)
        self.read_desired_user_groups(directory_groups, directory_connector)
        # if directory_users is None:
        #     raise AssertionException("Error retrieving users from directory")
        # self.log_action_summary()

        for org_name, sign_connector in self.connectors.items():
            # create any new Sign groups
            for new_group in set(self.user_groups[org_name]) - set(sign_connector.sign_groups()):
                self.logger.info("Creating new Sign group: {}".format(new_group))
                sign_connector.create_group(new_group)
            self.update_sign_users(self.directory_user_by_user_key, sign_connector, org_name)
        self.log_action_summary()

    def log_action_summary(self):
        """
        """
        logger = self.logger
        # find the total number of directory users and selected/filtered users
        # Number of directory users read
        self.action_summary['directory_users_read'] = len(self.directory_user_by_user_key)
        # Number of Sign Admins mapped
        self.action_summary['sign_admins_matched'] = len(self.admin_roles)
        # Total Number of Sign users
        self.action_summary['sign_users_read'] = len(self.total_sign_user_count)
        # Number of Sign users created/removed/updated
        self.action_summary['sign_users_created'] = len(self.sign_users_created_count)
        self.action_summary['sign_users_removed'] = len(self.sign_users_removed_count)
        self.action_summary['sign_users_updated'] = len(self.sign_users_updated_count)
        self.action_summary['sign_users_with_matched_groups'] = len(self.sign_users_with_matched_groups)
        self.action_summary['sign_users_assigned_to_groups'] = len(self.sign_users_assigned_to_groups)
        self.action_summary['sign_users_assigned_admin_role'] = len(self.sign_users_assigned_to_admin_role)

        action_summary_description = [
            ['directory_users_read', 'Number of directory users read'],
            ['sign_users_read', ' Number of Sign users read'],
            ['sign_users_created', 'Number of Sign users created'],
            ['sign_users_removed', 'Number of Sign users removed'],
            ['sign_users_updated', 'Number of Sign users updated'],
            ['sign_admins_matched', 'Number of Sign admins matched'],
            ['sign_users_with_matched_groups', 'Number of Sign users with matched groups'],
            ['sign_users_assigned_to_groups', 'Number of Sign users with groups updated'],
            ['sign_users_assigned_admin_role', 'Number of Sign users admin roles updated']
        ]

        pad = 0
        for action_description in action_summary_description:
            if len(action_description[1]) > pad:
                pad = len(action_description[1])

        header = '------- Action Summary -------'
        logger.info('---------------------------' + header + '---------------------------')
        for action_description in action_summary_description:
            description = action_description[1].rjust(pad, ' ')
            action_count = self.action_summary[action_description[0]]
            logger.info('  %s: %s', description, action_count)

    def update_sign_users(self, directory_users, sign_connector, org_name):
        sign_users = sign_connector.get_users()
        self.total_sign_user_count = len(directory_users.items)
        for _, directory_user in directory_users.items():
            sign_user = sign_users.get(directory_user['email'])
            if not self.should_sync(directory_user, org_name):
                continue

            assignment_group = None

            for group in self.user_groups[org_name]:
                if group in directory_user['groups']:
                    assignment_group = group
                    self.sign_users_with_matched_groups.add(directory_user)
                    break

            if assignment_group is None:
                assignment_group = self.DEFAULT_GROUP_NAME

            group_id = sign_connector.get_group(assignment_group)
            admin_roles = self.admin_roles.get(org_name, {})
            user_roles = self.resolve_new_roles(directory_user, admin_roles)
            if self.create_new_users is True and sign_user is None:
                self.insert_new_users(sign_connector, directory_user, user_roles, group_id, assignment_group)
            if sign_user is None:  # sign_user may still be None here is flag 'create_new_users' is False and user does not exist
                continue
            else:
                self.update_existing_users(sign_connector, sign_user, directory_user, group_id, user_roles,
                                           assignment_group)


    @staticmethod
    def roles_match(resolved_roles, sign_roles):
        if isinstance(sign_roles, str):
            sign_roles = [sign_roles]
        return sorted(resolved_roles) == sorted(sign_roles)

    @staticmethod
    def resolve_new_roles(umapi_user, role_mapping):
        roles = set()
        for group in umapi_user['groups']:
            sign_roles = role_mapping.get(group.lower())
            if sign_roles is None:
                continue
            roles.update(sign_roles)
        return list(roles) if roles else ['NORMAL_USER']

    def should_sync(self, umapi_user, org_name):
        """
        Initial gatekeeping to determine if user is candidate for Sign sync
        Any checks that don't depend on the Sign record go here
        Sign record must be defined for user, and user must belong to at least one entitlement group
        and user must be accepted identity type
        :param umapi_user:
        :param org_name:
        :return:
        """
        return set(umapi_user['groups']) & set(self.entitlement_groups[org_name]) and \
               umapi_user['type'] in self.identity_types

    @staticmethod
    def _groupify(groups):
        processed_groups = defaultdict(list)
        for g in groups:
            processed_group = AdobeGroup.create(g)
            processed_groups[processed_group.umapi_name].append(processed_group.group_name.lower())
        return processed_groups

    @staticmethod
    def _admin_role_mapping(sync_config):
        admin_roles = sync_config.get_list('admin_roles', True)
        if admin_roles is None:
            return {}
        mapped_admin_roles = {}
        for mapping in admin_roles:
            sign_role = mapping.get('sign_role')
            if sign_role is None:
                raise AssertionException("must define a Sign role in admin role mapping")
            adobe_groups = mapping.get('adobe_groups')
            if adobe_groups is None or not len(adobe_groups):
                continue
            for g in adobe_groups:
                group = AdobeGroup.create(g)
                group_name = group.group_name.lower()
                if group.umapi_name not in mapped_admin_roles:
                    mapped_admin_roles[group.umapi_name] = {}
                if group_name not in mapped_admin_roles[group.umapi_name]:
                    mapped_admin_roles[group.umapi_name][group_name] = set()
                mapped_admin_roles[group.umapi_name][group_name].add(sign_role)
        return mapped_admin_roles

    def read_desired_user_groups(self, mappings, directory_connector):
        self.logger.debug('Building work list...')

        options = self.options
        directory_group_filter = options['directory_group_filter']
        if directory_group_filter is not None:
            directory_group_filter = set(directory_group_filter)
        extended_attributes = options.get('extended_attributes')

        directory_user_by_user_key = self.directory_user_by_user_key

        directory_groups = set(six.iterkeys(mappings))
        if directory_group_filter is not None:
            directory_groups.update(directory_group_filter)
        directory_users = directory_connector.load_users_and_groups(groups=directory_groups,
                                                                    extended_attributes=extended_attributes,
                                                                    all_users=directory_group_filter is None)

        for directory_user in directory_users:
            user_key = self.get_directory_user_key(directory_user)
            if not user_key:
                self.logger.warning("Ignoring directory user with empty user key: %s", directory_user)
                continue
            directory_user_by_user_key[user_key] = directory_user

    def get_directory_user_key(self, directory_user):
        """
        :type directory_user: dict
        """
        email = directory_user.get('email')
        if email:
            return six.text_type(email)
        return None

    def get_user_key(self, id_type, username, domain, email=None):
        """
        Construct the user key for a directory or adobe user.
        The user key is the stringification of the tuple (id_type, username, domain)
        but the domain part is left empty if the username is an email address.
        If the parameters are invalid, None is returned.
        :param username: (required) username of the user, can be his email
        :param domain: (optional) domain of the user
        :param email: (optional) email of the user
        :param id_type: (required) id_type of the user
        :return: string "id_type,username,domain" (or None)
        :rtype: str
        """
        id_type = identity_type.parse_identity_type(id_type)
        email = normalize_string(email) if email else None
        username = normalize_string(username) or email
        domain = normalize_string(domain)

        if not id_type:
            return None
        if not username:
            return None
        if username.find('@') >= 0:
            domain = ""
        elif not domain:
            return None
        return six.text_type(id_type) + u',' + six.text_type(username) + u',' + six.text_type(domain)

    def get_identity_type_from_directory_user(self, directory_user):
        identity_type = directory_user.get('identity_type')
        if identity_type is None:
            identity_type = self.options['new_account_type']
            self.logger.warning('Found user with no identity type, using %s: %s', identity_type, directory_user)
        return identity_type

    def update_existing_users(self, sign_connector, sign_user, directory_user, group_id, user_roles, assignment_group):
            update_data = {
                "email": sign_user['email'],
                "firstName": sign_user['firstName'],
                "groupId": group_id,
                "lastName": sign_user['lastName'],
                "roles": user_roles,
            }
            groups_match = sign_user['group'].lower() == assignment_group
            roles_match = self.roles_match(user_roles, sign_user['roles'])
            if groups_match and roles_match:
                self.logger.debug("skipping Sign update for '{}' -- no updates needed".format(directory_user['email']))
                return
            if not groups_match:
                self.sign_users_assigned_to_groups.add(sign_user)
            if not roles_match:
                self.sign_users_assigned_to_admin_role.add(sign_user)
            try:
                sign_connector.update_user(sign_user['userId'], update_data)
                self.logger.info("Updated Sign user '{}', Group: '{}', Roles: {}".format(
                    directory_user['email'], assignment_group, update_data['roles']))
            except AssertionError as e:
                self.logger.error("Error updating user {}".format(e))

    def insert_new_users(self, sign_connector, directory_user, user_roles, group_id, assignment_group):
        """
        Inserts new user in the Sign Console
        :param sign_connector:
        :param directory_user:
        :param user_roles:
        :param group_id:
        :param assignment_group:
        :return:
        """
        insert_data = {
            "email": directory_user['email'],
            "firstName": directory_user['firstname'],
            "groupId": group_id,
            "lastName": directory_user['lastname'],
            "roles": user_roles,
        }
        try:
            sign_connector.insert_user(insert_data)
            self.logger.info("Inserted Sign user '{}', Group: '{}', Roles: {}".format(
                directory_user['email'], assignment_group, insert_data['roles']))
            self.sign_users_created_count += 1
        except AssertionException as e:
            self.logger.error(format(e))
        return
