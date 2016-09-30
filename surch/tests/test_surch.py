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

import sh
import os
import json
import shutil
import tempfile

import mock
import testtools
import click.testing as clicktest

from .. import repo
from .. import utils
from .. import surch
from .. import constants
from .. import organization
from ..exceptions import SurchError


PATH = os.path.abspath(__file__).rsplit('/', 1)[0]
TEST_PATH = os.path.join(PATH, 'test')


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
    try:
        with open(file_path) as results_file:
            return len(json.load(results_file)['_default'])
    except:
        return 0


# class SurchTestCase(testtools.TestCase):
#     def setUp(self):
#         super(SurchTestCase, self).setUp()
#         constants.DOT_SURCH = tempfile.mkdtemp()

#     def tearDown(self):
#         super(SurchTestCase, self).tearDown()
#         shutil.rmtree(constants.DOT_SURCH)


class TestRepo(testtools.TestCase):
    def setUp(self):
        super(TestRepo, self).setUp()
        self.repo_dir = tempfile.mkdtemp(prefix='repo-')
        self.clone_dir = tempfile.mkdtemp(prefix='clone-')

        shutil.rmtree(self.repo_dir)
        sh.git.init(self.repo_dir)
        previous_dir = os.getcwd()
        os.chdir(self.repo_dir)
        sh.git.remote.add.origin('http://x.git')
        fd, the_file = tempfile.mkstemp(dir=self.repo_dir)
        with open(the_file, 'w') as f:
            f.write('import')
        os.close(fd)
        sh.git.add(the_file)
        sh.git.commit('-am', 'w00t')
        os.chdir(previous_dir)

    def tearDown(self):
        super(TestRepo, self).tearDown()
        # shutil.rmtree(constants.DOT_SURCH)
        shutil.rmtree(self.repo_dir)
        shutil.rmtree(self.clone_dir)

    def test_surch_repo_command_with_arguments_and_found_results(self):
        self.args = 'https://github.com/cloudify-cosmo/surch.git'
        opts = {
            '-s': 'import',
            '-p': self.clone_dir,
            '-l': self.clone_dir
        }
        _invoke_click('surch_repo', [self.repo_dir], opts)
        results_file_path = os.path.join(self.clone_dir, 'results.json')
        dicts_num = count_dicts_in_results_file(results_file_path)
        self.assertTrue(dicts_num > 0)
        with open(results_file_path) as results_file:
            results = (results_file.read())
        # utils.remove_repos_folder(TEST_PATH)

    def test_surch_repo_command_with_config_and_found_results(self):
        config_file_path = os.path.join(PATH, 'config/repo-config.yaml')
        self.args = ' '
        opts = {
            '-c': config_file_path,
            '-v': None}
        _invoke_click('surch_repo', [self.args], opts)
        result_path = os.path.join(
            constants.RESULTS_PATH, 'cloudify-cosmo/results.json')
        dicts_num = count_dicts_in_results_file(result_path)
        self.assertTrue(dicts_num > 0)
        utils.remove_repos_folder(constants.DOT_SURCH)

    def test_surch_repo_command_with_arguments_found_results_and_remove(self):
        result_path = os.path.join(TEST_PATH, 'results.json')
        repo_path = os.path.join(TEST_PATH, 'clones/surch')
        self.args = 'https://github.com/cloudify-cosmo/surch.git'
        opts = {
            '-s': 'import',
            '-p': os.path.join(TEST_PATH, 'clones'),
            '-l': TEST_PATH,
            '-R': None}
        _invoke_click('surch_repo', [self.args], opts)
        dicts_num = count_dicts_in_results_file(result_path)
        self.assertTrue(dicts_num > 0)
        self.assertFalse(os.path.isdir(repo_path))
        utils.remove_repos_folder(TEST_PATH)

    def test_surch_repo_command_with_arguments_without_string_opt(self):
        self.args = 'https://github.com/cloudify-cosmo/surch.git'
        opts = {
            '-p': TEST_PATH,
            '-l': TEST_PATH,
            '-v': None
        }
        result = _invoke_click('surch_repo', [self.args], opts)
        self.assertEqual(1, result.exit_code)
        utils.remove_repos_folder(TEST_PATH)

    def test_create_search_strings(self):
        repository = repo.Repo(
            repo_url='',
            search_list='',
            verbose=False,
            results_dir=None,
            print_result=False,
            cloned_repo_dir=None,
            consolidate_log=False,
            remove_cloned_dir=False)
        search_list = repository._create_search_string(['a', 'b', 'c'])
        success = search_list == "'a' --or -e 'b' --or -e 'c'"
        self.assertTrue(success)

    def test_clone_or_pull(self):
        repo_class = repo.Repo(
            repo_url='https://github.com/cloudify-cosmo/surch.git',
            search_list=['a', 'b', 'c'])
        repo_path = os.path.join(constants.CLONED_REPOS_PATH, 'surch')
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
        repo_class._clone_or_pull()
        repo_path = os.path.join(constants.CLONED_REPOS_PATH, 'surch')
        if not os.path.isdir(repo_path):
            repo_class._clone_or_pull()
        commits = repo_class._get_all_commits()
        self.assertTrue(commits > 0)
        utils.remove_repos_folder(constants.DOT_SURCH)

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
        self.assertTrue(dicts_num > 0)


class TestUtils(testtools.TestCase):
    def test_read_config_file(self):
        config_file_path = os.path.join(PATH, 'config/repo-config.yaml')
        config_file = utils.read_config_file(config_file_path)
        if 'organization_flag' and 'print_result' in config_file:
            success = True
        else:
            success = False
        self.assertTrue(success)

    def test_remove_folder(self):
        if not os.path.isdir(TEST_PATH):
            os.makedirs(TEST_PATH)
        utils.remove_repos_folder(TEST_PATH)
        self.assertFalse(os.path.isdir(TEST_PATH))

    def test_find_string_between_strings(self):
        string = utils.find_string_between_strings('bosurchom', 'bo', 'om')
        self.assertTrue(string == 'surch')

    @mock.patch.object(utils, 'str', mock.Mock(return_value='surch'))
    def test_handle_results_file(self):
        test_file_path = '{0}.json'.format(TEST_PATH)
        with open(test_file_path, 'a') as file:
            file.write('surch')
        utils.handle_results_file(test_file_path, False)
        success = os.path.isfile('{0}.json.surch'.format(TEST_PATH))
        if success:
            os.remove('{0}.json.surch'.format(TEST_PATH))
        self.assertTrue(success)

    def test_check_if_executable_exists_else_exit(self):
        result = self.assertRaises(
            SurchError, utils.assert_executable_exists,
            executable='executable_not_exist')
        self.assertEqual(
            'executable_not_exist executable not found and is required',
            str(result))


class TestOrg(testtools.TestCase):

    def test_surch_org_command_with_arguments_and_found_results(self):
        self.args = 'cloudify-cosmo'
        opts = {
            '-s': 'import',
            '-p': os.path.join(TEST_PATH, 'cloudify-cosmo/clones'),
            '-l': os.path.join(TEST_PATH, 'cloudify-cosmo'),
            '--include-repo=': 'surch',
            '-v': None,
            '-R': None
        }
        result = _invoke_click('surch_org', [self.args], opts)
        result_path = os.path.join(TEST_PATH, 'cloudify-cosmo/results.json')
        self.assertEqual(result.exit_code, 0)
        dicts_num = count_dicts_in_results_file(result_path)
        self.assertTrue(dicts_num > 0)
        self.assertFalse(os.path.isdir(
            '{0}cloudify-cosmo/clones/surch'.format(TEST_PATH)))
        utils.remove_repos_folder(TEST_PATH)

    def test_surch_org_command_with_user_arguments(self):
        self.args = 'Havivw'
        opts = {
            '-s': 'import',
            '-p': TEST_PATH,
            '-l': os.path.join(TEST_PATH, 'cloudify-cosmo'),
            '--include-repo=': 'surch',
            '-v': None}
        result = _invoke_click('surch_org', [self.args], opts)
        self.assertEqual(1, result.exit_code)

    def test_surch_org_command_with_config_no_auth_and_found_results(self):
        config_file_path = os.path.join(PATH, 'config/org-config_no_auth.yaml')
        self.args = ' '
        opts = {
            '-c': config_file_path,
            '-v': None}
        result = _invoke_click('surch_org', [self.args], opts)
        self.assertEqual(result.exit_code, 0)
        result_path = os.path.join(constants.RESULTS_PATH,
                                   'cloudify-cosmo/results.json')
        dicts_num = count_dicts_in_results_file(result_path)
        self.assertTrue(dicts_num > 0)
        utils.remove_repos_folder(constants.DOT_SURCH)

    def test_surch_user_command_with_arguments_and_found_results(self):
        test_path = os.path.join(PATH, 'test/Havivw')
        result_path = os.path.join(PATH, 'test/Havivw/results.json')
        self.args = 'Havivw'
        opts = {
            '-s': 'import',
            '-p': test_path,
            '-l': test_path,
            '--include-repo=': 'surch',
            '-v': None}
        result = _invoke_click('surch_user', [self.args], opts)
        self.assertEqual(result.exit_code, 0)
        dicts_num = count_dicts_in_results_file(result_path)
        self.assertTrue(dicts_num > 0)
        utils.remove_repos_folder(test_path)

    def test_surch_user_command_with_config_no_auth_and_found_results(self):
        config_file_path = os.path.join(PATH,
                                        'config/user-config_no_auth.yaml')
        self.args = ' '
        opts = {
            '-c': config_file_path,
            '-v': None
        }
        _invoke_click('surch_user', [self.args], opts)
        result_path = os.path.join(
            constants.RESULTS_PATH, 'Havivw/results.json')
        dicts_num = count_dicts_in_results_file(result_path)
        success = dicts_num > 0
        self.assertTrue(success)
        utils.remove_repos_folder(constants.DOT_SURCH)

    def test_surch_org_command_with_include_exclude_repo(self):
        self.args = 'cloudify-cosmo'
        opts = {
            '-s': 'surch',
            '--exclude-repo=': 'surch',
            '--include-repo=': 'surch',
            '-v': None}
        result = _invoke_click('surch_org', [self.args], opts)
        self.assertEqual(1, result.exit_code)

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
            SurchError, org.get_repo_include_list,
            all_repos=all_repo, repos_to_exclude=repos_to_exclude,
            repos_to_include=repos_to_include)
        self.assertEqual(
            'You can not both include and exclude repositories',
            str(result))
