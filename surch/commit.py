########
# Copyright (c) 2017 GigaSpaces Technologies Ltd. All rights reserved
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
import subprocess

from tinydb import TinyDB

from .exceptions import SurchError
from . import repo, utils, constants


def _fetch_all_branches(cloned_repo_dir, repo_name, logger=utils.logger):
    git_get_branches_command = 'git -C {0} branch -a'.format(cloned_repo_dir)
    branches = subprocess.check_output(git_get_branches_command,
                                       shell=True).splitlines()
    for branch in branches:
        if '/' in str(branch):
            name = str(branch).rsplit('/', 1)[-1]
            git_checkout_command = 'git -C {0} checkout {1} -q'.format(
                cloned_repo_dir, name)
            repo._run_command_without_output(git_checkout_command,
                                             repo_name, logger)


def _write_results(files_list, results_file_path, logger=utils.logger):
    """Write the result to DB
    """
    result_count = 0
    db = TinyDB(results_file_path, indent=4,
                sort_keys=True, separators=(',', ': '))

    logger.info('Writing results to: {0}...'.format(results_file_path))
    for file in files_list:
        result_count += 1
        db.insert(file)
    logger.info('Found {0} files with your strings...'.format(result_count))


def search_and_decode_data(filename, url, search_list, owner_name,
                           repo_name, commit_sha, git_user, git_password,
                           files_list, logger=utils.logger):
    data_files = requests.get(url, auth=(git_user, git_password))
    data_files = data_files.json()
    try:
        decode_data_file = data_files['content'].decode('base64')
        for string in search_list:
            if string in decode_data_file:
                filepath = filename
                url = 'https://api.github.com/repos/{0}/{1}/commits/' \
                      '{2}'.format(owner_name, repo_name, commit_sha)
                commit_data = requests.get(url, auth=(git_user, git_password))
                commit_details = commit_data.json()['commit']['author']
                commit_time = commit_details['date']
                email = commit_details['email']
                username = \
                    (commit_data.json()['author']['login']).decode('ascii')

                result = dict(email=email, string=string, filepath=filepath,
                              username=username, commit_sha=commit_sha,
                              commit_time=commit_time,
                              repository_name=repo_name,
                              owner_name=owner_name,
                              blob_url=constants.GITHUB_BLOB_URL.format(
                                  owner_name, repo_name, commit_sha, filepath))
                files_list.append(result)
    except KeyError:
        for tree in data_files['tree']:
            logger.info('Checking this {0} file now...'.format(tree['path']))
            search_and_decode_data(tree['path'], tree['url'], search_list,
                                   owner_name, repo_name, commit_sha, git_user,
                                   git_password, files_list)


def search(search_list, commit_sha, cloned_repo_dir, results_file_path=None,
           verbose=False, consolidate_log=False):
    logger = utils.set_logger(verbose)
    if not os.path.isdir(cloned_repo_dir):
        logger.error('Failed execute {0} '
                     'directory not exist.)'.format(cloned_repo_dir))
        raise SurchError

    utils.check_string_list(search_list)
    repo_url = subprocess.check_output(
        'git -C {0} ls-remote --get-url'.format(cloned_repo_dir), shell=True)
    repo_name, organization = utils._get_repo_and_organization_name(repo_url)
    _fetch_all_branches(cloned_repo_dir, repo_name, logger)
    results_file_path = results_file_path or constants.RESULTS_PATH
    search_string = repo._create_search_string(list(search_list), logger)
    utils.handle_results_file(results_file_path, consolidate_log)
    results = [repo.search_strings_in_commit(cloned_repo_dir, commit_sha,
                                             search_string)]
    repo._write_results(results, cloned_repo_dir, results_file_path,
                        repo_name, organization, logger)


def web_search(owner_name, repo_name, search_list, commit_sha,
               git_user=None, git_password=None, results_file_path=None,
               verbose=False, consolidate_log=False):

    logger = utils.set_logger(verbose)
    files_list = []
    if not git_user or not git_password:
        logger.error('Choosing not to provide GitHub credentials limits '
                     'requests to GitHub to 60/h. This might affect cloning.')
        raise SurchError

    results_file_path = results_file_path or constants.RESULTS_PATH
    utils.handle_results_file(results_file_path, consolidate_log)

    url = "https://api.github.com/repos/{0}/{1}/git/trees/{2}".format(
        owner_name, repo_name, commit_sha)
    get_data = requests.get(url, auth=(git_user, git_password))
    all_data = get_data.json()
    for tree in all_data['tree']:
        logger.info('Checking this {0} file now...'.format(tree['path']))
        search_and_decode_data(tree['path'], tree['url'], search_list,
                               owner_name, repo_name, commit_sha,
                               git_user, git_password, files_list, logger)
    _write_results(files_list, results_file_path, logger)