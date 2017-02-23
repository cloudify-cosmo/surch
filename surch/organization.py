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

import requests

from .exceptions import SurchError
from . import repo, utils, constants


def get_repos_list_per_page(git_item_type, organization, git_credentials,
                            page_num, logger=utils.logger):
    """Getting repository data from git api per api page
    """
    try:
        response = requests.get(
            constants.GITHUB_REPO_DETAILS_API_URL.format(git_item_type,
                                                         organization, 'public',
                                                         page_num),
            auth=git_credentials)

        return response.json()
    except (requests.ConnectionError, requests.Timeout) as error:
        logger.error(error)
        raise SurchError


def _parse_repo_data(repo_data):
    """Return only name and clone_url from all repo list of dicts
    """
    return [dict((key, data[key]) for key in ['name', 'clone_url'])
            for data in repo_data]


def _set_git_credentials(git_user=None, git_password=None, logger=utils.logger):
    if not git_user or not git_password:
        logger.warn('Choosing not to provide GitHub credentials limits '
                    'requests to GitHub to 60/h. This might affect cloning.')
        git_credentials = False
    else:
        git_credentials = (git_user, git_password)
    return git_credentials


def _get_all_repos_list(git_user, git_password, git_item_name,
                        is_organization=True, logger=utils.logger):
    """use in 'get_repos_list_per_page' method to get all repositories
    organization/user data
    """
    git_item_type = 'orgs' if is_organization else 'users'
    logger.info('Retrieving repository information for this {0}{1}...'.format(
        'organization: ' if is_organization else 'user: ', git_item_name))
    git_credentials = _set_git_credentials(git_user, git_password, logger)
    org_data = _get_org_data(git_item_type, git_item_name,
                             git_credentials, logger)
    repo_count = org_data['public_repos']
    last_page_number = repo_count / 100
    if (repo_count % 100) > 0:
        # Adding 2 because 1 for the extra repos that mean more page,
        #  and 1 for the next for loop.
        last_page_number += 2
        repos_data = []
        for page_num in xrange(1, last_page_number):
            repo_data = get_repos_list_per_page(git_item_type, git_item_name,
                                                git_credentials, page_num,
                                                logger)
            repos_data.extend(_parse_repo_data(repo_data))
        return repos_data


def _get_org_data(git_item_type, organization,
                  git_credentials, logger=utils.logger):
    response = requests.get(constants.GITHUB_API_URL.format(
        git_item_type, organization), auth=git_credentials)
    if response.status_code == requests.codes.NOT_FOUND:
        logger.error('The organization or user {0} could not be found. '
                     'Please make sure you use the correct type '
                     '(org/user).'.format(organization))
        raise SurchError
    return response.json()


def _get_repo_include_list(all_repos, repos_to_include=None,
                          repos_to_exclude=None, logger=utils.logger):
    """ Get include or exclude repositories list ,
    return repositories list to search on"""
    if repos_to_exclude and repos_to_include:
        logger.error('You can not both include and exclude repositories.')
        raise SurchError
    repo_url_list = []
    if repos_to_include:
        for repo_name in repos_to_include:
            for repo_data in all_repos:
                if repo_data['name'] == repo_name:
                    repo_url_list.append(repo_data['clone_url'])
    elif repos_to_exclude:
        for repo_data in all_repos:
            if repo_data['name'] not in repos_to_exclude:
                repo_url_list.append(repo_data['clone_url'])
    else:
        for repo_data in all_repos:
            repo_url_list.append(repo_data['clone_url'])
    return repo_url_list


def search(git_item_name, git_user, git_password, search_list,
           is_organization=True, results_file_path=None, cloned_repos_dir=None,
           repos_to_skip=None, repos_to_check=None, consolidate_log=False,
           remove_clones_dir=False, verbose=False, from_members=False):

    logger = utils.set_logger(verbose)
    utils.handle_results_file(results_file_path, consolidate_log)

    cloned_repos_dir = cloned_repos_dir or os.path.join(
        constants.CLONED_REPOS_PATH, git_item_name)

    repos_data = _get_all_repos_list(git_user, git_password, git_item_name,
                                     is_organization, logger)
    repos_url_list = _get_repo_include_list(all_repos=repos_data,
                                            repos_to_include=repos_to_check,
                                            repos_to_exclude=repos_to_skip)
    for repo_url in repos_url_list:
        repo.search(repo_url=repo_url, search_list=search_list,
                    results_file_path=results_file_path,
                    cloned_repo_dir=cloned_repos_dir, verbose=verbose,
                    remove_clone_dir=False, consolidate_log=True,
                    from_org=True, from_members=from_members)

    utils._remove_repos_folder(cloned_repos_dir, remove_clones_dir)
