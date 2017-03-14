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
from multiprocessing.dummy import Pool
from multiprocessing import cpu_count

from .exceptions import SurchError
from . import repo, utils, constants


def search_on_single_commit(search_list, commit_sha, cloned_repo_dir,
                            results_file_path=None, repo_name='',
                            organization='', verbose=False,
                            consolidate_log=False):

    utils.check_string_list(search_list)
    logger = utils.set_logger(verbose)
    results_file_path = results_file_path or constants.RESULTS_PATH
    search_string = repo._create_search_string(list(search_list), logger)

    utils.handle_results_file(results_file_path, consolidate_log)
    results = repo.search_strings_in_commit(cloned_repo_dir, commit_sha,
                                            search_string)
    repo._write_results(results, cloned_repo_dir, results_file_path,
                        repo_name, organization, logger)
