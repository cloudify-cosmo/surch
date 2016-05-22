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
import sys
import logging

import requests

from . import logger, repo, utils, constants

REPO_DETAILS_API_URL = \
    'https://api.github.com/{0}/{1}/repos?type={2}&per_page={3}&page={4}'
ORG_DETAILS_API_URL = 'https://api.github.com/{0}/{1}'


lgr = logger.init()


class Organization(object):
    def __init__(
            self,
            search_list,
            organization,
            git_user,
            git_password,
            organization_flag=True,
            repos_to_skip=None,
            consolidate_log=False,
            cloned_repos_path=constants.CLONED_REPOS_PATH,
            results_dir=constants.RESULTS_PATH,
            verbose=False,
            remove_cloned_repository=False,
            **kwargs):
        """Surch instance define var from CLI or config file
        """
        utils.handle_results_file(results_dir, consolidate_log)
        self.search_list = search_list
        self.organization = organization
        self.results_dir = results_dir
        self.repos_to_skip = repos_to_skip or []
        if not git_user or not git_user:
            lgr.warn(
                'Choosing not to provide GitHub credentials limits '
                'requests to GitHub to 60/h. This might affect cloning.')
            self.auth = False
        else:
            self.auth = True
            self.git_user = git_user
            self.git_password = git_password
        self.remove_cloned_repository = remove_cloned_repository
        self.repository_data = []
        if not os.path.isdir(cloned_repos_path):
            os.makedirs(cloned_repos_path)
        self.item_type = 'orgs' if organization_flag else 'users'
        self.object_type = 'organization' if organization_flag else 'user'
        self.cloned_repos_path = cloned_repos_path
        self.verbose = verbose

        lgr.setLevel(logging.DEBUG if verbose else logging.INFO)

    @classmethod
    def init_with_config_file(cls, config_file, verbose=False,
                              remove_cloned_repository=False,
                              organization_flag=True):
        conf_vars = utils.read_config_file(config_file, verbose,
                                           remove_cloned_repository,
                                           organization_flag)
        return cls(**conf_vars)

    def get_github_repo_list(
            self,
            url_type='clone_url',
            repository_type='public',
            repository_per_page=100):
        """This method get from GitHub the git url list for cloning
        """
        lgr.info(
            'Retrieving list of repositories for the {0}...'.format(
                self.object_type))
        auth = (self.git_user, self.git_password) if self.auth else False
        repository_data = \
            requests.get(
                ORG_DETAILS_API_URL.format(
                    self.item_type, self.organization), auth=auth)
        if '<Response [404]>' in str(repository_data):
            lgr.error(
                'The organization or user {0} could not be found. '
                'Please make sure you use the correct type (org/user).'.format(
                    self.organization))
            sys.exit(1)
        repository_number = \
            repository_data.json()['{0}_repos'.format(repository_type)]
        last_page_number = repository_number / repository_per_page
        if (repository_number % repository_per_page) > 0:
            # Adding 2 because 1 for the extra repos that mean more page,
            #  and 1 for the next for loop.
            last_page_number += 2

            for page_num in range(1, last_page_number):
                repository_data = requests.get(
                    REPO_DETAILS_API_URL.format(self.item_type,
                                                self.organization,
                                                repository_type,
                                                repository_per_page,
                                                page_num), auth=auth)

                for repository in repository_data.json():
                    self.repository_data.append(repository)
                self.repository_specific_data = \
                    self._parse_json_list_of_dict(['name', url_type])

    def _parse_json_list_of_dict(self, list_of_arguments):
        return [dict((key, data[key]) for key in list_of_arguments)
                for data in self.repository_data]

    def search(self, search_list, url_type='clone_url'):
        search_list = search_list or self.search_list
        if len(search_list) == 0:
            lgr.error('You must supply at least one string to search for.')
            sys.exit(1)
        self.get_github_repo_list()
        self.cloned_repos_path = os.path.join(self.organization,
                                              self.cloned_repos_path)
        for repository_data in self.repository_specific_data:
            if repository_data['name'] not in self.repos_to_skip:
                repo.search(
                    search_list=search_list,
                    repo_url=repository_data[url_type],
                    cloned_repo_dir=self.cloned_repos_path,
                    results_dir=self.results_dir,
                    remove_cloned_repository=False,
                    consolidate_log=True,
                    verbose=self.verbose)
        if self.remove_cloned_repository:
            utils.remove_repos_folder(path=self.cloned_repos_path)


def search(
        search_list,
        organization,
        git_user=None,
        git_password=None,
        repos_to_skip=None,
        organization_flag=True,
        config_file=None,
        cloned_repos_path=constants.CLONED_REPOS_PATH,
        results_dir=constants.RESULTS_PATH,
        remove_cloned_repository=False,
        verbose=False,
        **kwargs):

    if config_file:
        org = Organization.init_with_config_file(
            config_file=config_file,
            verbose=verbose,
            remove_cloned_repository=remove_cloned_repository,
            organization_flag=organization_flag)
    else:
        org = Organization(
            search_list=search_list,
            organization=organization,
            git_user=git_user,
            organization_flag=organization_flag,
            git_password=git_password,
            repos_to_skip=repos_to_skip,
            cloned_repos_path=cloned_repos_path,
            results_dir=results_dir,
            remove_cloned_repository=remove_cloned_repository,
            verbose=verbose)

    org.search(search_list=search_list)
