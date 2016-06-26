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
import json
import mock


import testtools
import click.testing as clicktest

from surch import utils
from surch import repo
from surch import organization
from surch import constants
import surch.surch as surch


def _invoke_click(func, args=None, opts=None):
    args = args or []
    opts = opts or {}
    opts_and_args = []
    opts_and_args.extend(args)
    for opt, value in opts.items():
        if value:
            opts_and_args.append(opt + value)
        else:
            opts_and_args.append(opt)
    return clicktest.CliRunner().invoke(getattr(surch, func), opts_and_args)


def count_dicts_in_results_file(file_path):
    i = 0
    try:
        with open(file_path, 'r') as results_file:
            results = json.load(results_file)
        for key, value in results.items():
            for k, v in value.items():
                i += 1
    except:
        pass
    return i


class TestRepo(testtools.TestCase):
    def test_surch_repo_command_with_arguments_and_found_results(self):
        self.args = 'https://github.com/cloudify-cosmo/surch.git'
        opts = {
            '-s': 'import',
            '-p': './test',
            '-l': './test'}
        _invoke_click('surch_repo', [self.args], opts)
        dicts_num = count_dicts_in_results_file(
            './test/results.json')
        success = True if dicts_num > 0 else False
        self.assertTrue(success)

    def test_surch_repo_command_with_config_and_found_results(self):
        self.args = ' '
        opts = {
            '-c': './config/repo-config.yaml',
            '-v': None}
        _invoke_click('surch_repo', [self.args], opts)
        result_path = os.path.join(constants.RESULTS_PATH,
                                   'cloudify-cosmo/results.json')
        dicts_num = count_dicts_in_results_file(result_path)
        success = True if dicts_num > 0 else False
        self.assertTrue(success)

    def test_surch_repo_command_with_arguments_found_results_and_remove(self):
        self.args = 'https://github.com/cloudify-cosmo/surch.git'
        opts = {
            '-s': 'import',
            '-p': './test/clones',
            '-l': './test',
            '-R': None}
        _invoke_click('surch_repo', [self.args], opts)
        dicts_num = count_dicts_in_results_file(
            './test/results.json')
        success = True if dicts_num > 0 else False
        self.assertTrue(success)
        self.assertFalse(os.path.isdir('./test/clones/surch'))

    def test_surch_repo_command_with_arguments_without_string_opt(self):
        self.args = 'https://github.com/cloudify-cosmo/surch.git'
        opts = {
            '-p': './test',
            '-l': './test',
            '-v': None}
        result = _invoke_click('surch_repo', [self.args], opts)
        self.assertEqual('<Result SystemExit(1,)>', str(result))

    def test_create_search_strings(self):
        Repo = repo.Repo(repo_url='',
                         search_list='',
                         verbose=False,
                         results_dir=None,
                         print_result=False,
                         cloned_repo_dir=None,
                         consolidate_log=False,
                         remove_cloned_dir=False)
        search_list = Repo._create_search_string(['a', 'b', 'c'])
        success = \
            True if search_list == "'a' --or -e 'b' --or -e 'c'" else False
        self.assertTrue(success)

    def test_clone_or_pull(self):
        repo_class = repo.Repo(
            repo_url='https://github.com/cloudify-cosmo/surch.git',
            search_list=['a', 'b', 'c'])
        repo_path = os.path.join(constants.CLONED_REPOS_PATH,
                                 'surch')
        if os.path.isdir(repo_path):
            repo_class._clone_or_pull()
            self.assertTrue(os.path.isdir(repo_path))
            utils.remove_repos_folder(repo_path)
        repo_class._clone_or_pull()
        self.assertTrue(os.path.isdir(repo_path))

    def test_get_all_commits(self):
        repo_class = repo.Repo(
            repo_url='https://github.com/cloudify-cosmo/surch.git',
            search_list=['a', 'b', 'c'])
        repo_path = os.path.join(constants.CLONED_REPOS_PATH,
                                 'cloudify-cosmo/surch')
        if not os.path.isdir(repo_path):
            repo_class._clone_or_pull()
        commits = repo_class._get_all_commits()
        success = True if commits > 0 else False
        self.assertTrue(success)

    @mock.patch.object(repo.Repo, '_get_user_details',
                       mock.Mock(return_value=('surch', 'surch', 'surch')))
    def test_write_results(self):
        repo_class = repo.Repo(
            repo_url='https://github.com/cloudify-cosmo/surch.git',
            search_list=['a', 'b', 'c'])
        result_path = os.path.join(constants.RESULTS_PATH,
                                   'cloudify-cosmo/results.json')
        repo_class._write_results(
            [['189e57105a3eab4bf6b1ac6accd522d6f4b8bb93:README.md',
             '189e57105a3eab4bf6b1ac6accd522d6f4b8bb93:setup.py']])
        dicts_num = count_dicts_in_results_file(result_path)
        success = True if dicts_num > 0 else False
        self.assertTrue(success)


class TestUtils(testtools.TestCase):
    def test_read_config_file(self):
        config_file = utils.read_config_file('./config/repo-config.yaml')
        if 'organization_flag' and 'print_result' in config_file:
            success = True
        else:
            success = False
        self.assertTrue(success)

    def test_remove_folder(self):
        if not os.path.isdir('./test'):
            os.makedirs('./test')
        utils.remove_repos_folder('./test')
        self.assertFalse(os.path.isdir('./test'))

    def test_find_string_between_strings(self):
        string = utils.find_string_between_strings('bosurchom', 'bo', 'om')
        success = True if string == 'surch' else False
        self.assertTrue(success)

    @mock.patch.object(utils, 'str', mock.Mock(return_value='surch'))
    def test_handle_results_file(self):
        with open('./test.json', 'a') as file:
            file.write('surch')
        utils.handle_results_file('./test.json', False)
        success = True if os.path.isfile('./test.json.surch') else False
        if success:
            os.remove('./test.json.surch')
        self.assertTrue(success)


class TestOrg(testtools.TestCase):

    def test_surch_org_command_with_arguments_and_found_results(self):
        self.args = 'cloudify-cosmo'
        opts = {
            '-s': 'import',
            '-p': './test',
            '-l': './test/cloudify-cosmo',
            '--include-repo=': 'surch',
            '-v': None}
        result = _invoke_click('surch_org', [self.args], opts)
        self.assertEqual('<Result okay>', str(result))
        dicts_num = count_dicts_in_results_file(
            './test/cloudify-cosmo/results.json')
        success = True if dicts_num > 0 else False
        self.assertTrue(success)

    def test_surch_org_command_with_config_no_auth_and_found_results(self):
        self.args = 'None'
        opts = {
            '-c': './config/org-config_no_auth.yaml',
            '-v': None}
        result = _invoke_click('surch_org', [self.args], opts)
        self.assertEqual('<Result okay>', str(result))
        result_path = os.path.join(constants.RESULTS_PATH,
                                   'cloudify-cosmo/results.json')
        dicts_num = count_dicts_in_results_file(result_path)
        success = True if dicts_num > 0 else False
        self.assertTrue(success)

    def test_get_all_commits(self):
        repo_class = repo.Repo(
            repo_url='https://github.com/cloudify-cosmo/surch.git',
            search_list=['a', 'b', 'c'])
        repo_path = os.path.join(constants.CLONED_REPOS_PATH,
                                 'cloudify-cosmo/surch')
        if not os.path.isdir(repo_path):
            repo_class._clone_or_pull()
        commits = repo_class._get_all_commits()
        success = True if commits > 0 else False
        self.assertTrue(success)

    def test_surch_org_command_with_include_exclude_repo(self):
        self.args = 'cloudify-cosmo'
        opts = {
            '-s': 'surch',
            '--exclude-repo=': 'surch',
            '--include-repo=': 'surch',
            '-v': None}
        result = _invoke_click('surch_org', [self.args], opts)
        self.assertEqual('<Result SystemExit(1,)>', str(result))

    def test_get_repo_include_list_with_repos_to_include(self):
        org = organization.Organization(organization='cloudify-cosmo')
        all_repo = [{'name': 'a', 'clone_url': 'a'},
                    {'name': 'b', 'clone_url': 'b'},
                    {'name': 'c', 'clone_url': 'c'},
                    {'name': 'd', 'clone_url': 'd'},
                    {'name': 'e', 'clone_url': 'e'},
                    {'name': 'f', 'clone_url': 'f'},
                    {'name': 'g', 'clone_url': 'g'}]
        repos_to_include = ['b', 'e', 'g']
        repos = org.get_repo_include_list(all_repos=all_repo,
                                          repos_to_include=repos_to_include)
        self.assertEqual("['b', 'e', 'g']", str(repos))

    def test_get_repo_include_list_with_repos_to_exclude(self):
        org = organization.Organization(organization='cloudify-cosmo')
        all_repo = [{'name': 'a', 'clone_url': 'a'},
                    {'name': 'b', 'clone_url': 'b'},
                    {'name': 'c', 'clone_url': 'c'},
                    {'name': 'd', 'clone_url': 'd'},
                    {'name': 'e', 'clone_url': 'e'},
                    {'name': 'f', 'clone_url': 'f'},
                    {'name': 'g', 'clone_url': 'g'}]
        repos_to_exclude = ['a', 'c', 'd', 'f']
        repos = org.get_repo_include_list(all_repos=all_repo,
                                          repos_to_exclude=repos_to_exclude)
        self.assertEqual("['b', 'e', 'g']", str(repos))

    def test_get_repo_include_list_with_repos_to_exclude_and_include(self):
        org = organization.Organization(organization='cloudify-cosmo')
        all_repo = [{'name': 'a', 'clone_url': 'a'},
                    {'name': 'b', 'clone_url': 'b'}]
        repos_to_exclude = ['a', 'c', 'd', 'f']
        repos_to_include = ['b', 'e', 'g']
        result = self.assertRaises(
            SystemExit, org.get_repo_include_list,
            all_repos=all_repo, repos_to_exclude=repos_to_exclude,
            repos_to_include=repos_to_include)
        self.assertEqual('1', str(result))
