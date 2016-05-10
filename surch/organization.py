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
import logging
from time import time

import requests

from . import logger, repo, utils

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
LOG_PATH = os.path.join(HOME_PATH, 'results.json')

lgr = logger.init()


class Organization(object):

    def __init__(
            self,
            search_list,
            skipped_repo,
            organization,
            git_user,
            git_password,
            local_path=DEFAULT_PATH,
            log_path=LOG_PATH,
            verbose=False,
            quiet_git=True):
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
        self.organization = organization
        self.db = log_path
        self.search_list = search_list
        self.ignore_repository = skipped_repo or []
        if not git_user or not git_user:

            lgr.info('************************************'
                     'ATTENSION************************************\n'
                     ' You run without authunticate git allows'
                     ' you to make up to 60 requests per hour')
            self.auth = False
        else:
            self.auth = True
            self.git_user = git_user
            self.git_password = git_password
        self.all_data = []
        if not os.path.isdir(local_path):
            os.makedirs(local_path)
        self.local_path = os.path.join(local_path, organization)
        self.quiet_git = '--quiet' if quiet_git else ''
        self.verbose = verbose

        lgr.setLevel(logging.DEBUG if verbose else logging.INFO)

    @classmethod
    def get_and_init_vars_from_config_file(
            cls,
            config_file,
            verbose=False,
            quiet_git=True):
        """ Define vars from "config.yaml" file"""
        conf_vars = utils.get_and_init_vars_from_config_file(config_file,
                                                             verbose,
                                                             quiet_git)
        return cls(**conf_vars)

    def get_github_repo_list(
            self,
            url_type='clone_url',
            repository_type='public',
            repository_per_page=100):
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
        if not self.auth:
            all_data = requests.get(API_URL_ORGANIZATION_DETAILS.
                                    format(self.organization))
        else:
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
                if not self.auth:
                    all_data = requests.get(
                        API_URL_REPO_DETAILS.format(self.organization,
                                                    repository_type,
                                                    repository_per_page,
                                                    page_num))
                else:
                    all_data = requests.get(
                        API_URL_REPO_DETAILS.format(self.organization,
                                                    repository_type,
                                                    repository_per_page,
                                                    page_num),
                        auth=(self.git_user, self.git_password))

                for repo in all_data.json():
                    self.all_data.append(repo)
                self.repository_specific_data = \
                    self._parase_json_list_of_dict(['name', url_type])

    def _search_in_commits(self):
        """ This method search the secrets in the commits

        :return: problematic_commits blob_url
        """
        start = time()
        directories_list = self._get_directory_list()
        for directory in directories_list:
            self.repository_name = directory.split('/', -1)[-1]
            repo.find_strings_in_commits_from_local_repo(
                search_list=self.search_list, repo_url=None,
                directory=directory, repository_name=self.repository_name,
                organization_name=self.organization, local_path=self.local_path,
                log_path=self.db, verbose=self.verbose,
                quiet_git=self.quiet_git)

        total_time = utils.convert_to_seconds(start, time())
        lgr.debug('Search time: {0} seconds'.format(total_time))

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
        start = time()
        lgr.info('Clone or pull from {0} organization or user'
                 .format(self.organization))
        for repository_data in self.repository_specific_data:
            if repository_data['name'] not in self.ignore_repository:
                repo.clone_or_pull_repository(
                    search_list=self.search_list,
                    repo_url=repository_data[url_type],
                    repository_name=repository_data['name'],
                    organization_name=self.organization,
                    local_path=self.local_path, log_path=self.db,
                    verbose=self.verbose, quiet_git=self.quiet_git)
        total_time = utils.convert_to_seconds(start, time())
        lgr.debug('git clone\pull time: {0} seconds'.format(total_time))

    def _get_directory_list(self):
        """ Get list of the clone directory in the path"""
        full_path_list = []
        for item in os.listdir(self.local_path):
            path = os.path.join(self.local_path, item)
            if os.path.isdir(path):
                full_path_list.append(path)
        return full_path_list

    def search(self):
        start = time()
        self.get_github_repo_list()
        self._clone_repositorys()
        self._search_in_commits()
        total_time = utils.convert_to_seconds(start, time())
        lgr.debug('Total time: {0} seconds'.format(total_time))
        utils.print_error_summary(self.error_summary, lgr)


def search(search_list, organization, git_user=None, git_password=None,
           skipped_repo=None, local_path=DEFAULT_PATH, log_path=LOG_PATH,
           verbose=False, quiet_git=True):

    skipped_repo = skipped_repo or []
    org = Organization(search_list=search_list, skipped_repo=skipped_repo,
                       organization=organization, git_user=git_user,
                       git_password=git_password, local_path=local_path,
                       log_path=log_path, verbose=verbose, quiet_git=quiet_git)
    org.search()

