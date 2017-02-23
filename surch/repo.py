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
import subprocess

import retrying
from tinydb import TinyDB

from . import utils, constants


def _run_command_without_output(command, repo_name, logger=utils.logger):
    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        proc.stdout, proc.stderr = proc.communicate()
    except subprocess.CalledProcessError as git_error:
        err = 'Failed execute {0} on repo {1} ({2})'.format(command, repo_name,
                                                            git_error)
        logger.error(err)


def _order_branches_list(branches_names):
    branches = []
    for name in branches_names:
        name = name.replace('  ', '').replace('* ', '')
        branches.append(name)
    return branches


@retrying.retry(stop_max_attempt_number=3)
def _get_repo(repo_url, cloned_repo_dir, repo_name, organization,
              logger=utils.logger):
    """Clone the repo if it doesn't exist in the cloned_repo_dir.
    Otherwise, pull it.
    """
    if os.path.isdir(cloned_repo_dir):
        logger.debug('Local repo already exists at: {0}'.format(
            cloned_repo_dir))
        logger.info('Pulling repo: {0}...'.format(repo_name))
        git_pull_command = 'git -C {0} pull -q'.format(cloned_repo_dir)
        _run_command_without_output(git_pull_command, repo_name, logger)
    else:
        logger.info('Cloning repo {0} from org/user {1} to {2}...'.format(
            repo_name, organization, cloned_repo_dir))
        git_clone_command = 'git clone -q {0} {1}'.format(repo_url,
                                                          cloned_repo_dir)
        _run_command_without_output(git_clone_command, repo_name, logger)


def _get_all_commits_from_all_branches(cloned_repo_dir, repo_name,
                                       logger=utils.logger):
    commit_list = []
    git_get_branches_command = 'git -C {0} branch -a'.format(cloned_repo_dir)
    branches = subprocess.check_output(git_get_branches_command,
                                       shell=True).splitlines()
    for branch in branches:
        if '/' in str(branch):
            name = str(branch).rsplit('/', 1)[-1]
            git_checkout_command = 'git -C {0} checkout {1} -q'.format(
                cloned_repo_dir, name)

            _run_command_without_output(git_checkout_command,
                                        repo_name, logger)

            git_get_commits_from_branch = \
                'git -C {0} rev-list origin/{1}'.format(cloned_repo_dir, name)

            commits_per_branch = subprocess.check_output(
                git_get_commits_from_branch, shell=True).splitlines()

            for commit_per_branch in commits_per_branch:
                commit_list.append(commit_per_branch)
    commit_num = len(list(set(commit_list)))
    logger.info('Found {0} commits in {1}...'.format(commit_num, repo_name))
    return list(set(commit_list))


def _create_search_string(search_list,
                          logger=utils.logger):
    """Create part of the grep command from search list.
    """
    logger.debug('Generating git grep-able search string...')
    unglobbed_search_list = ["'{0}'".format(item) for item in search_list]
    search_string = ' --or -e '.join(unglobbed_search_list)
    return search_string


def _search_commit(cloned_repo_dir, commit, search_string):
    """Run git grep on the commit
    """
    try:
        matched_files = subprocess.check_output(
            'git -C {0} grep -c -e {1} {2}'.format(
                cloned_repo_dir, search_string, commit),
            shell=True).splitlines()
        branches_names = subprocess.check_output(
            'git  -C {0} branch --contains {1}'.format(cloned_repo_dir, commit),
            shell=True).splitlines()

        return {'matched_files': matched_files,
                'branches_names': branches_names}
    except subprocess.CalledProcessError:
        return '', ''


def _search(search_list, commits, cloned_repo_dir, repo_name,
            logger=utils.logger):
    """Create list of all commits which contains one of the strings
    we're searching for.
    """
    search_string = _create_search_string(list(search_list), logger)
    matching_commits = []
    logger.info('Scanning repo {0} for {1} string(s)...'.format(
        repo_name, len(search_list)))
    for commit in commits:
        matched_files_and_branches = _search_commit(cloned_repo_dir, commit,
                                                    search_string)
        matching_commits.append(matched_files_and_branches)

    return matching_commits


def _write_results(results, cloned_repo_dir, results_file_path,
                   repo_name, organization, logger=utils.logger):
    """Write the result to DB
    """
    result_count = 0
    db = TinyDB(results_file_path, indent=4,
                sort_keys=True, separators=(',', ': '))

    logger.info('Writing results to: {0}...'.format(results_file_path))
    for result in results:
        try:
            for match in list(result['matched_files']):
                branches_names = _order_branches_list(result['branches_names'])
                commit_sha, filepath, line_num = match.rsplit(':')
                username, email, commit_time = \
                    _get_user_details(cloned_repo_dir, commit_sha)
                result = dict(email=email,
                              filepath=filepath,
                              username=username,
                              commit_sha=commit_sha,
                              commit_time=commit_time,
                              branches_names=branches_names,
                              repository_name=repo_name,
                              organization_name=organization,
                              blob_url=constants.GITHUB_BLOB_URL.format(
                                  organization,
                                  repo_name,
                                  commit_sha, filepath))
                result_count += 1
                db.insert(result)
        except (IndexError, TypeError):
            # The structre of the output is
            # sha:filename
            # sha:filename
            # filename
            # None
            # We need both sha and filename and when we don't get them
            # we skip to the next var
            pass
    logger.info('Found {0} files with your strings...'.format(result_count))


def _get_user_details(cloned_repo_dir, sha):
    """ Return user_name, user_email, commit_time
    per commit before write to DB
    """
    details = subprocess.check_output(
        'git -C {0} show -s  {1}'.format(cloned_repo_dir, sha), shell=True)
    name = utils.find_string_between_strings(details, 'Author: ', ' <')
    email = utils.find_string_between_strings(details, '<', '>')
    commit_time = utils.find_string_between_strings(details,
                                                    'Date:   ', '+').strip()
    return name, email, commit_time


def set_cloned_repo_dir(cloned_repo_dir, organization, repo_name,
                        from_org, from_members):
    cloned_repo_dir = cloned_repo_dir or os.path.join(
        constants.CLONED_REPOS_PATH, organization, repo_name)
    if from_members:
        cloned_repo_dir = os.path.join(cloned_repo_dir, organization, repo_name)
        from_org = False
    if from_org:
        cloned_repo_dir = os.path.join(cloned_repo_dir, repo_name)
    return cloned_repo_dir


def search(repo_url, search_list, results_file_path=None, cloned_repo_dir=None,
           verbose=False, remove_clone_dir=False, consolidate_log=False,
           from_org=False, from_members=False, **kwargs):
    """API method init repo instance and search strings
    """
    utils.check_string_list(search_list)
    logger = utils.set_logger(verbose)
    utils.handle_results_file(results_file_path, consolidate_log)
    repo_name, organization = utils._get_repo_and_organization_name(repo_url)

    cloned_repo_dir = set_cloned_repo_dir(cloned_repo_dir, organization,
                                          repo_name, from_org, from_members)

    results_file_path = results_file_path or constants.RESULTS_PATH
    _get_repo(repo_url, cloned_repo_dir, repo_name, organization, logger)
    commits_list = _get_all_commits_from_all_branches(cloned_repo_dir,
                                                      repo_name, logger)

    results = _search(search_list, commits_list, cloned_repo_dir, repo_name,
                      logger)
    _write_results(results, cloned_repo_dir, results_file_path,
                   repo_name, organization, logger)

    utils._remove_repos_folder(cloned_repo_dir, remove_clone_dir)
