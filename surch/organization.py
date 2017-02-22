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

from .plugins import handler
from .exceptions import SurchError
from . import repo, utils, constants


def get_repos_list_per_page(self, repos_per_page, page_num):
    """Getting repository data from git api per api page
    """
    try:
        response = requests.get(
            constants.GITHUB_REPO_DETAILS_API_URL.format(item_type,
                                                         organization,
                                                         'public',
                                                         repos_per_page,
                                                         page_num),
            auth=git_credentials)

        return response.json()
    except (requests.ConnectionError, requests.Timeout) as error:
        logger.error(error)
        sys.exit(1)


def _parse_repo_data(repo_data):
    """Return only name and clone_url from all repo list of dicts
    """
    return [dict((key, data[key]) for key in ['name', 'clone_url'])
            for data in repo_data]


def _set_git_credentials(git_user=None, git_password=None):
    if not git_user or not git_password:
        logger.warn('Choosing not to provide GitHub credentials limits '
                    'requests to GitHub to 60/h. This might affect cloning.')
        git_credentials = False
    else:
        git_credentials = (git_user, git_password)
    return git_credentials


def _get_all_repos_list(git_user, git_password, is_organization=True,
                        git_item_type='org', repos_per_page=100):
    """use in 'get_repos_list_per_page' method to get all repositories
    organization/user data
    """
    logger.info('Retrieving repository information for this {0}{1}...'.format(
        'organization:' if is_organization else 'user:', organization))
    git_credentials = _set_git_credentials(git_user, git_password)
    org_data = _get_org_data(git_item_type, git_credentials)
    repo_count = org_data['public_repos']
    last_page_number = repo_count / repos_per_page
    if (repo_count % repos_per_page) > 0:
        # Adding 2 because 1 for the extra repos that mean more page,
        #  and 1 for the next for loop.
        last_page_number += 2
        repos_data = []
        for page_num in xrange(1, last_page_number):
            repo_data = get_repos_list_per_page(repos_per_page,
                                                     page_num)
            repos_data.extend(_parse_repo_data(repo_data))
        return repos_data


def _get_org_data(git_item_type, git_credentials):
    response = requests.get(constants.GITHUB_API_URL.format(
        git_item_type, organization), auth=git_credentials)
    if response.status_code == requests.codes.NOT_FOUND:
        logger.error('The organization or user {0} could not be found. '
                     'Please make sure you use the correct type '
                     '(org/user).'.format(organization))
        sys.exit(1)
    return response.json()


def search(is_organization, verbose):
    logger = utils.set_logger(verbose)
    item_type = 'orgs' if is_organization else 'users'
    global logger
    repo_name, organization = utils._get_repo_and_organization_name(repo_url)





#
# class Organization(object):
#     def __init__(self,
#                  organization,
#                  config_file=None,
#                  git_user=None,
#                  git_password=None,
#                  repos_to_skip=None,
#                  repos_to_check=None,
#                  is_organization=True,
#                  pager=None,
#                  source=None,
#                  verbose=False,
#                  search_list=None,
#                  results_dir=None,
#                  print_result=False,
#                  consolidate_log=False,
#                  cloned_repos_dir=None,
#                  remove_cloned_dir=False,
#                  **kwargs):
#         """Surch org instance init
#
#         :param organization: organization name (string)
#         :param git_user: user name for authentication (string)
#         :param git_password:
#                         user password  or api key for authentication (string)
#         :param repos_to_skip: exclude repos (list)
#         :param repos_to_check: include repos (list)
#         :param is_organization: this flag for api (boolean)
#         :param verbose: log level (boolean)
#         :param results_dir: path to result file (string)
#         :param print_result: this flag print result file in the end (boolean)
#         :param consolidate_log:
#                         this flag decide if save the old result file (boolean)
#         :param cloned_repos_dir: path for cloned repo (string)
#         :param remove_cloned_dir:
#                         this flag for removing the clone directory (boolean)
#         """
#         utils.assert_executable_exists('git')
#         self.logger = utils.logger
#         self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)
#         if repos_to_skip and repos_to_check:
#             raise SurchError(
#                 "You can't both include and exclude repositories")
#         if not git_user or not git_password:
#             self.logger.warn(
#                 'Choosing not to provide GitHub credentials limits '
#                 'requests to GitHub to 60/h. This might affect cloning')
#             self.git_credentials = False
#         else:
#             self.git_credentials = (git_user, git_password)
#
#         self.config_file = config_file if config_file else None
#         self.pager = handler.plugins_handle(config_file=self.config_file,
#                                             plugins_list=pager)
#         self.source = handler.plugins_handle(config_file=self.config_file,
#                                              plugins_list=source)
#         self.search_list = search_list
#         self.print_result = print_result
#         self.organization = organization
#         self.results_dir = results_dir
#         self.repos_to_skip = repos_to_skip
#         self.repos_to_check = repos_to_check
#         self.remove_cloned_dir = remove_cloned_dir
#         results_dir = \
#             os.path.join(results_dir, 'results.json') if results_dir else None
#         self.results_file_path = results_dir or os.path.join(
#             constants.RESULTS_PATH, self.organization, 'results.json')
#         self.consolidate_log = consolidate_log
#         self.is_organization = is_organization
#         self.item_type = 'orgs' if is_organization else 'users'
#         self.cloned_repos_dir = cloned_repos_dir or os.path.join(
#             self.organization, constants.CLONED_REPOS_PATH)
#         self.verbose = verbose
#
#     @classmethod
#     def init_with_config_file(cls,
#                               config_file,
#                               pager=None,
#                               source=None,
#                               verbose=False,
#                               search_list=None,
#                               print_result=False,
#                               is_organization=True,
#                               remove_cloned_dir=False):
#         """Init org instance from config file
#         """
#         source = handler.plugins_handle(
#             config_file=config_file, plugins_list=source)
#         conf_vars = utils.read_config_file(
#             pager=pager,
#             source=source,
#             verbose=verbose,
#             search_list=search_list,
#             config_file=config_file,
#             print_result=print_result,
#             is_organization=is_organization,
#             remove_cloned_dir=remove_cloned_dir)
#         return cls(**conf_vars)
#
#     def _get_org_data(self):
#         response = requests.get(constants.GITHUB_API_URL.format(
#             self.item_type, self.organization), auth=self.git_credentials)
#         if response.status_code == requests.codes.NOT_FOUND:
#             raise SurchError(
#                 'The organization or user {0} could not be found. '
#                 'Please make sure you use the correct type (org/user)'.format(
#                     self.organization))
#         return response.json()
#
#     def get_repos_list_per_page(self, repos_per_page, page_num):
#         """Getting repository data from git api per api page
#         """
#         try:
#             response = requests.get(
#                 constants.GITHUB_REPO_DETAILS_API_URL.format(
#                     self.item_type,
#                     self.organization,
#                     'public',
#                     repos_per_page,
#                     page_num), auth=self.git_credentials)
#             return response.json()
#         except (requests.ConnectionError, requests.Timeout) as error:
#             raise SurchError(error)
#
#     def _parse_repo_data(self, repo_data):
#         """Return only name and clone_url from all repo list of dicts
#         """
#         return [dict((key, data[key]) for key in ['name', 'clone_url'])
#                 for data in repo_data]
#
#     def _get_all_repos_list(self, repos_per_page=100):
#         """Use in 'get_repos_list_per_page' method to get all repositories
#         organization/user data
#         """
#         self.logger.info(
#             'Retrieving repository information for this {0}{1}...'.format(
#                 'organization:' if self.is_organization else 'user:',
#                 self.organization))
#         org_data = self._get_org_data()
#         repo_count = org_data['public_repos']
#         last_page_number = repo_count / repos_per_page
#         if (repo_count % repos_per_page) > 0:
#             # Adding 2 because 1 for the extra repos that mean more page,
#             #  and 1 for the next for loop.
#             last_page_number += 2
#             repos_data = []
#             for page_num in xrange(1, last_page_number):
#                 repo_data = self.get_repos_list_per_page(repos_per_page,
#                                                          page_num)
#                 repos_data.extend(self._parse_repo_data(repo_data))
#             return repos_data
#
#     def get_repo_include_list(self,
#                               all_repos,
#                               repos_to_include=None,
#                               repos_to_exclude=None):
#         """Get include or exclude repositories list,
#         return repositories list to search on
#         """
#         if repos_to_exclude and repos_to_include:
#             raise SurchError(
#                 'You can not both include and exclude repositories')
#         repo_url_list = []
#         if repos_to_include:
#             for repo_name in repos_to_include:
#                 for repo_data in all_repos:
#                     if repo_data['name'] == repo_name:
#                         repo_url_list.append(repo_data['clone_url'])
#         elif repos_to_exclude:
#             for repo_data in all_repos:
#                 if repo_data['name'] not in repos_to_exclude:
#                     repo_url_list.append(repo_data['clone_url'])
#         else:
#             for repo_data in all_repos:
#                 repo_url_list.append(repo_data['clone_url'])
#         return repo_url_list
#
#     def search(self, search_list=None):
#         """This method search the string on the organization/user
#         """
#         search_list = search_list or []
#         handler.merge_all_search_list(
#             source=self.source,
#             config_file=self.config_file,
#             search_list=search_list)
#         if len(search_list) == 0:
#             raise SurchError(
#                 'You must supply at least one string to search for')
#         repos_data = self._get_all_repos_list()
#         if not os.path.isdir(self.cloned_repos_dir):
#             os.makedirs(self.cloned_repos_dir)
#         utils.handle_results_file(self.results_file_path, self.consolidate_log)
#
#         repos_url_list = self.get_repo_include_list(
#             all_repos=repos_data,
#             repos_to_include=self.repos_to_check,
#             repos_to_exclude=self.repos_to_skip)
#
#         for repo_data in repos_url_list:
#             repo.search(
#                 print_result=False,
#                 repo_url=repo_data,
#                 verbose=self.verbose,
#                 consolidate_log=True,
#                 search_list=search_list,
#                 remove_cloned_dir=False,
#                 from_organization=True,
#                 results_dir=self.results_dir,
#                 cloned_repo_dir=self.cloned_repos_dir)
#         if 'pagerduty' in self.pager:
#             handler.pagerduty_trigger(config_file=self.config_file,
#                                       log=self.results_file_path)
#
#
# def search(organization,
#            pager=None,
#            source=None,
#            verbose=False,
#            git_user=None,
#            config_file=None,
#            results_dir=None,
#            search_list=None,
#            git_password=None,
#            print_result=False,
#            repos_to_skip=None,
#            repos_to_check=None,
#            is_organization=True,
#            cloned_repos_dir=None,
#            remove_cloned_dir=False,
#            **kwargs):
#     """API method init organization instance and search strings
#     """
#     utils.assert_executable_exists('git')
#     pager = handler.plugins_handle(
#         config_file=config_file, plugins_list=pager)
#     source = handler.plugins_handle(
#         config_file=config_file, plugins_list=source)
#
#     search_list = handler.merge_all_search_list(
#         source=source, config_file=config_file, search_list=search_list)
#
#     org = Organization(
#         pager=pager,
#         verbose=verbose,
#         git_user=git_user,
#         results_dir=results_dir,
#         git_password=git_password,
#         search_list=search_list,
#         organization=organization,
#         print_result=print_result,
#         repos_to_skip=repos_to_skip,
#         repos_to_check=repos_to_check,
#         is_organization=is_organization,
#         cloned_repos_dir=cloned_repos_dir,
#         remove_cloned_dir=remove_cloned_dir)
#
#     org.search(search_list=search_list)
