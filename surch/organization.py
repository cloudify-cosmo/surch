########
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import os
import time
import logging
# import subprocess

import yaml
# import click
# import retrying
import requests
from tinydb import TinyDB

from . import logger, repo

# This strings is for getting the repo git url list , it get organization,
#  repository_per_page vars
API_URL_REPO_DETAILS = \
    'https://api.github.com/orgs/{0}/repos?type={1}&per_page={2}&page={3}'
# This string is a template for blob_url to redirect you
# for the problematic commit.
# It get organization, repository_name, sha, file_name
BLOB_URL_TEMPLATE = 'https://github.com/{0}/{1}/blob/{2}/{3}'
# Get organization details
API_URL_ORGANIZATION_DETAILS = 'https://api.github.com/orgs/{0}'
HOME_PATH = os.path.expanduser("~")
DEFAULT_PATH = os.path.join(HOME_PATH, 'surch')
LOG_PATH = os.path.join(HOME_PATH, 'problematic_commit.json')

lgr = logger.init()




def _calculate_performance_to_second(start, end):
    """ Calculate the runnig time"""
    return str(round(end - start, 3))


class Organization(object):

    def __init__(self, search_list, skipped_repo, organization, git_user,
                 git_password, local_path=DEFAULT_PATH, log_path=LOG_PATH,
                 verbose=False, quiet_git=True):
        """ Surch instance define var from CLI or config file

        :param search_list: list of secrets you want to search
        :type search_list: (tupe, list)
        :param skipped_repo: list of repo you didn't want to check
        :type skipped_repo: (tupe, list)
        :param organization: organization name
        :type organization: basestring
        :param git_user: git user name for authenticate
        :type git_user: basestring
        :param git_password:git user password for authenticate
        :type git_password: basestring
        :param local_path: this path contain the repos clone
        :type local_path: basestring
        :param verbose: user verbose mode
        :type verbose: bool
        """
        self.error_summary = []
        self.git_user = git_user
        self.db = log_path
        self.search_list = self._create_search_strings(list(search_list))
        self.ignore_repository = skipped_repo or []
        self.organization = organization
        self.git_password = git_password
        self.all_data = []
        if not os.path.isdir(local_path):
            os.makedirs(local_path)
        self.local_path = os.path.join(local_path, organization)
        self.quiet_git = '--quiet' if quiet_git else ''
        self.verbose = verbose

        lgr.setLevel(logging.DEBUG if verbose else logging.INFO)

    @classmethod
    def from_config_file(cls, config_file, verbose=False, quiet_git=True):
        """ Define vars from "config.yaml" file"""
        with open(config_file, 'r') as config:
            conf_vars = yaml.load(config.read())
        conf_vars.setdefault('verbose', verbose)
        conf_vars.setdefault('quiet_git', quiet_git)
        return cls(**conf_vars)

    def get_github_repo_list(self, url_type='clone_url',
                             repository_type='public', repository_per_page=100):
        """ This method get from git hub the git url list for clonnig

        :param url_type: url type (git_url, ssh_url, clone_url, svn_url)
        default:'clone_url'
        :type url_type: basestring
        :param repository_type: repository type (all, private, public, fork)
        default: 'public'
        :type repository_type: basestring
        :param repository_per_page: this for getting the
                                        MAX information in 1 page
        default: 100
        :type repository_per_page: int
        :return:
        """
        all_data = requests.get(API_URL_ORGANIZATION_DETAILS.
                                format(self.organization),
                                auth=(self.git_user, self.git_password))

        repository_number = all_data.json()['{0}_repos'.format(repository_type)]
        last_page_number = repository_number / repository_per_page
        if (repository_number % repository_per_page) > 0:
            # Adding 2 because 1 for the extra repos that mean more page,
            #  and 1 for the next for loop.
            last_page_number += 2

            for page_num in range(1, last_page_number):
                all_data = requests.get(
                    API_URL_REPO_DETAILS.format(self.organization,
                                                repository_type,
                                                repository_per_page, page_num),
                    auth=(self.git_user, self.git_password))
                for repo in all_data.json():
                    self.all_data.append(repo)
                self.repository_specific_data = \
                    self._parase_json_list_of_dict(['name', url_type])

    def _parase_json_list_of_dict(self, list_of_arguments):
        return [dict((key, data[key]) for key in list_of_arguments)
                for data in self.all_data]

    def _clone_repositorys(self, url_type='clone_url'):
        """ This method run clone or pull for the repo list

        :param url_type: url type (git_url, ssh_url, clone_url, svn_url)
        default:'clone_url'
        :type url_type: basestring
        :return: cloned repo
        """
        start = time.time()
        lgr.info('Clone or pull from {0} organization or user'
                 .format(self.organization))
        for repository_data in self.repository_specific_data:
            if repository_data['name'] not in self.ignore_repository:
                repository = repo.Repo(search_list=self.search_list,
                                       url=repository_data[url_type],
                                       local_path=self.local_path,
                                       log_path=self.db, verbose=self.verbose,
                                       quiet_git=self.quiet_git, org_used=True)
                repository._clone_repo(repository_data['name'],
                                       self.organization,
                                       repository_data[url_type])
        total = _calculate_performance_to_second(start, time.time())
        lgr.debug('git clone\pull time: {0} seconds'.format(total))


    def search_in_commits(self):
        """ This method search the secrets in the commits

        :return: problematic_commits blob_url
        """
        start = time.time()
        directories_list = self._get_directory_list()
        for directory in directories_list:
            self.repository_name = directory.split('/', -1)[-1]
            repository = repo.Repo(search_list=self.search_list,
                                   url=None,
                                   local_path=self.local_path,
                                   log_path=self.db, verbose=self.verbose,
                                   quiet_git=self.quiet_git, org_used=True)

            repository._find_problematic_commits_in_directory(
                self.search_list, directory, self.repository_name,
                self.organization)
        total = _calculate_performance_to_second(start, time.time())
        lgr.debug('Search time: {0} seconds'.format(total))


    def _get_directory_list(self):
        """ Get list of the clone directory in the path"""
        full_path_list = []
        for item in os.listdir(self.local_path):
            path = os.path.join(self.local_path, item)
            if os.path.isdir(path):
                full_path_list.append(path)
        return full_path_list


    def _create_search_strings(self, search_list):
        """ Create part of the grep command from search list"""
        search_strings = search_list[0]
        search_list = list(search_list)
        search_list.remove(search_strings)
        for string in search_list:
            search_strings = "{0} --or -e '{1}'".format(search_strings, string)
        return search_strings

    def _print_error_summary(self):
        if self.error_summary:
            lgr.info(
                'Summary of all errors: \n{0}'.format(
                    '\n'.join(self.error_summary)))

    def check_on_organization(self):
        start = time.time()
        self.get_github_repo_list()
        self._clone_repositorys()
        self.search_in_commits()
        total = _calculate_performance_to_second(start, time.time())
        lgr.debug('Total time: {0} seconds'.format(total))
        self._print_error_summary()

