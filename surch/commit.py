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


def search_on_single_commit(search_list, commit_sha, cloned_repo_dir,
                            results_file_path=None, verbose=False,
                            consolidate_log=False):
    logger = utils.set_logger(verbose)
    if not os.path.isdir(cloned_repo_dir):
        logger.error('Failed execute {0} directory not exist.)'.format(cloned_repo_dir))
        raise SurchError

    utils.check_string_list(search_list)
    repo_url = subprocess.check_output('git -C {0} ls-remote --get-url'.format(cloned_repo_dir), shell=True)
    repo_name, organization = utils._get_repo_and_organization_name(repo_url)
    _fetch_all_branches(cloned_repo_dir, repo_name, logger)
    results_file_path = results_file_path or constants.RESULTS_PATH
    search_string = repo._create_search_string(list(search_list), logger)
    utils.handle_results_file(results_file_path, consolidate_log)
    results = [repo.search_strings_in_commit(cloned_repo_dir, commit_sha,
                                             search_string)]
    repo._write_results(results, cloned_repo_dir, results_file_path,
                        repo_name, organization, logger)
