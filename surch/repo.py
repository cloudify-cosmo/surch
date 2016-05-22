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
import subprocess
from time import time

import retrying
from tinydb import TinyDB

from . import logger, utils, constants

BLOB_URL = 'https://github.com/{0}/{1}/blob/{2}/{3}'

lgr = logger.init()


class Repo(object):
    def __init__(
            self,
            repo_url,
            search_list,
            cloned_repo_dir=constants.CLONED_REPOS_PATH,
            results_dir=constants.RESULTS_PATH,
            consolidate_log=False,
            verbose=False,
            print_result=False,
            remove_cloned_dir=False,
            **kwargs):
        """Surch instance define var from CLI or config file
        """

        self.print_result = print_result
        self.search_list = search_list
        self.remove_cloned_dir = remove_cloned_dir
        self.error_summary = []
        self.results = 0
        self.repo_url = repo_url
        self.repo_name = repo_url.rsplit('/', 1)[-1].rsplit('.', 1)[0]
        self.org_name = repo_url.rsplit('.com/', 1)[-1].rsplit('/', 1)[0]
        self.cloned_repo_dir = os.path.join(cloned_repo_dir, self.org_name)
        self.repo_path = os.path.join(self.cloned_repo_dir, self.repo_name)
        self.quiet_git = '--quiet' if not verbose else ''
        self.verbose = verbose
        self.results_file_path = os.path.join(
            results_dir, self.org_name, 'results.json')
        utils.handle_results_file(self.results_file_path, consolidate_log)
        self.db = TinyDB(
            self.results_file_path,
            sort_keys=True,
            indent=4,
            separators=(',', ': '))

        lgr.setLevel(logging.DEBUG if verbose else logging.INFO)

    @classmethod
    def init_with_config_file(cls, config_file, print_result=False,
                              verbose=False):
        conf_vars = utils.read_config_file(print_result=print_result,
                                           config_file=config_file,
                                           verbose=verbose)
        return cls(**conf_vars)

    @retrying.retry(stop_max_attempt_number=3)
    def _clone_or_pull(self):
        """This method check if the repo exist in the
        path and run clone or pull
        """

        def run(command):
            try:
                proc = subprocess.Popen(
                    command, stdout=subprocess.PIPE, shell=True)
                proc.stdout, proc.stderr = proc.communicate()
                if self.verbose:
                    lgr.debug(proc.stdout)
            except subprocess.CalledProcessError as git_error:
                err = 'Failed execute {0} on repo {1} ({1})'.format(
                    command, self.repo_name, git_error)
                lgr.error(err)
                self.error_summary.append(err)

        if not os.path.isdir(self.cloned_repo_dir):
            os.makedirs(self.cloned_repo_dir)
        if os.path.isdir(self.repo_path):
            lgr.debug('Local repo already exists at: {0}'.format(
                self.repo_path))
            lgr.info('Pulling repo: {0}...'.format(self.repo_name))
            run('git -C {0} pull {1}'.format(self.repo_path, self.quiet_git))
        else:
            lgr.info('Cloning repo {0} from org {1} to {2}...'.format(
                self.repo_name, self.org_name, self.repo_path))
            run('git clone {0} {1} {2}'.format(
                self.quiet_git, self.repo_url, self.repo_path))

    @staticmethod
    def _create_search_string(search_list):
        """Create part of the grep command from search list.
        """

        lgr.debug('Generating git grep-able search string...')
        unglobbed_search_list = ["'{0}'".format(item) for item in search_list]
        search_string = ' --or -e '.join(unglobbed_search_list)
        return search_string

    def _search(self, search_list, commits):
        """Create list of all commits which contain searched strings
        """
        search_string = self._create_search_string(list(search_list))
        matching_commits = []
        lgr.info('Scanning repo `{0}` for {1} string(s)...'.format(
            self.repo_name, len(search_list)))
        for commit in commits:
            matching_commits.append(self._search_commit(commit, search_string))
        return matching_commits

    def _get_all_commits(self):
        """Get the sha (number) of the commit
        """
        lgr.debug('Retrieving list of commits...')
        try:
            commits = subprocess.check_output(
                'git -C {0} rev-list --all'.format(self.repo_path), shell=True)
            commit_list = commits.splitlines()
            self.commits = len(commit_list)
            return commit_list
        except subprocess.CalledProcessError:
            return []

    def _search_commit(self, commit, search_string):
        try:
            matched_files = subprocess.check_output(
                'git -C {0} grep -l -e {1} {2}'.format(
                    self.repo_path, search_string, commit), shell=True)
            return matched_files.splitlines()
        except subprocess.CalledProcessError:
            return []

    def _write_results(self, results):
        lgr.info('Writing results to: {0}...'.format(self.results_file_path))
        for matched_files in results:
            for match in matched_files:
                try:
                    commit_sha, filepath = match.rsplit(':', 1)
                    username, email, commit_time = \
                        self._get_user_details(commit_sha)
                    result = dict(
                        organization_name=self.org_name,
                        repository_name=self.repo_name,
                        commit_sha=commit_sha,
                        filepath=filepath,
                        username=username,
                        email=email,
                        commit_time=commit_time,
                        blob_url=BLOB_URL.format(
                            self.org_name,
                            self.repo_name,
                            commit_sha, filepath)
                    )
                    self.results += 1
                    self.db.insert(result)
                except IndexError:
                    # The structre of the output is
                    # sha:filename
                    # sha:filename
                    # filename
                    # None
                    # and we need both sha and filename and when we don't \
                    #  get them we do pass
                    pass

    def _get_user_details(self, sha):
        details = subprocess.check_output(
            "git -C {0} show -s  {1}".format(self.repo_path, sha), shell=True)
        name = utils.find_string_between_strings(details, 'Author: ', ' <')
        email = utils.find_string_between_strings(details, '<', '>')
        commit_time = utils.find_string_between_strings(
            details, 'Date:   ', '+').strip()
        return name, email, commit_time

    def search(self, search_list):
        search_list = search_list or self.search_list
        if len(search_list) == 0:
            lgr.error('You must supply at least one string to search for.')
            sys.exit(1)

        start = time()
        self._clone_or_pull()
        commits = self._get_all_commits()
        results = self._search(search_list, commits)
        self._write_results(results)
        if self.remove_cloned_dir:
            utils.remove_repos_folder(path=self.repo_path)
        total_time = utils.convert_to_seconds(start, time())
        if self.error_summary:
            utils.print_results_summary(self.error_summary, lgr)
        lgr.info('Found {0} results in {1} commits.'.format(
            self.results, self.commits))
        lgr.debug('Total time: {0} seconds'.format(total_time))
        if self.print_result:
            utils.print_result(self.results_file_path)


def search(
        search_list,
        repo_url,
        config_file=None,
        cloned_repo_dir=constants.CLONED_REPOS_PATH,
        results_dir=constants.RESULTS_PATH,
        consolidate_log=False,
        print_result=False,
        verbose=False,
        remove_cloned_dir=False,
        **kwargs):

    if config_file:
        repo = Repo.init_with_config_file(config_file=config_file,
                                          print_result=print_result,
                                          verbose=verbose)
    else:
        repo = Repo(
            print_result=print_result,
            repo_url=repo_url,
            search_list=search_list,
            cloned_repo_dir=cloned_repo_dir,
            results_dir=results_dir,
            consolidate_log=consolidate_log,
            remove_cloned_dir=remove_cloned_dir,
            verbose=verbose)
    repo.search(search_list=search_list)
