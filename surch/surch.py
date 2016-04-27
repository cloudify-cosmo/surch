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
import time
import logging
import tempfile
import subprocess

import yaml
import click
import retrying
import requests
from tinydb import TinyDB

from . import logger

# This strings is for getting the repo git url list , it get organization,
#  repository_per_page vars
API_URL_REPO_DETAILS = \
    'https://api.github.com/orgs/{0}/repos?type={1}&per_page={2}&page={3}'
# This string is a template for blob_url to redirect you
# for the problematic commit.
# It get organization, repository_name, sha, file_name
BLOB_URL_TEMPLATE = 'https://github.com/{0}/{1}/blob/{2}/{3}'
# Get organization details
API_URL_ORGANIZATION_DETAILS = 'https://api.github.com/orgs/{0}'


lgr = logger.init()


class Surch(object):
    HOME_PATH = os.path.expanduser("~")
    DEFAULT_PATH = os.path.join(HOME_PATH, 'surch')
    LOG_PATH = os.path.join(HOME_PATH, 'problematic_commit.json')

    def __init__(self, search_list, skipped_repo, organization, git_user,
                 git_password, local_path=DEFAULT_PATH, log_path=LOG_PATH,
                 verbose=False, quiet_git=True):
        """ Surch instance define var from CLI or config file

        :param search_list: list of secrets you want to search
        :type search_list: (tupe, list)
        :param skipped_repo: list of repo you didn't want to check
        :type skipped_repo: (tupe, list)
        :param organization: organization name
        :type organization: basestring
        :param git_user: git user name for authenticate
        :type git_user: basestring
        :param git_password:git user password for authenticate
        :type git_password: basestring
        :param local_path: this path contain the repos clone
        :type local_path: basestring
        :param verbose: user verbose mode
        :type verbose: bool
        """
        self.error_summary = []
        self.git_user = git_user
        self.db = TinyDB(
            log_path, sort_keys=True, indent=4, separators=(',', ': '))
        self.search_list = search_list
        self.ignore_repository = skipped_repo or []
        self.organization = organization
        self.git_password = git_password
        if not os.path.isdir(local_path):
            os.makedirs(local_path)
        self.local_path = os.path.join(local_path, organization)
        self.quiet_git = '--quiet' if quiet_git else ''

        lgr.setLevel(logging.DEBUG if verbose else logging.INFO)

    @classmethod
    def from_config_file(cls, config_file, verbose=False, quiet_git=True):
        """ Define vars from "config.yaml" file"""
        with open(config_file) as config:
            conf_vars = yaml.load(config.read())
        conf_vars.setdefault('verbose', verbose)
        conf_vars.setdefault('quiet_git', quiet_git)
        return cls(**conf_vars)

    # TODO: create method for extracting relevant data
    def get_github_repo_list(self, url_type='clone_url',
                             repository_type='public', repository_per_page=100):
        """ This method get from git hub the git url list for clonnig

        :param repository_type: repository type (all, private, public, fork)
        default: 'public'
        :type repository_type: basestring
        :param repository_per_page: this for getting the
                                        MAX information in 1 page
        default: 100
        :type repository_per_page: int
        :return:
        """
        self.all_data = []
        all_data = requests.get(API_URL_ORGANIZATION_DETAILS.
                                format(self.organization),
                                auth=(self.git_user, self.git_password))

        repository_number = all_data.json()['{0}_repos'.format(repository_type)]
        last_page_number = repository_number / repository_per_page
        if (repository_number % repository_per_page) > 0:
            # Adding 2 because 1 for the extra repos that mean more page,
            #  and 1 for the next for loop.
            last_page_number += 2

            for page_num in range(1, last_page_number):
                all_data = requests.get(
                    API_URL_REPO_DETAILS.format(self.organization,
                                                repository_type,
                                                repository_per_page, page_num),
                    auth=(self.git_user, self.git_password))
                for repo in all_data.json():
                    self.all_data.append(repo)
                self.repository_specific_data = \
                    self._parase_json_list_of_dict(['name', url_type])

    def _write_dict_to_db(self, sha, files_name, repository,  users, blob_url):
        self.db.insert({'organization_name': self.organization,
                        'repository_name': repository,
                        'commit_sha': sha,
                        'file_name': files_name,
                        'users': users,
                        'blob_url': blob_url})

    def _parase_json_list_of_dict(self, list_of_arguments):
        return [
            dict((key, data[key]) for key in list_of_arguments)
            for data in self.all_data
        ]

    def clone_repo(self, url_type='clone_url'):
        """ This method run clone or pull for the repo list

        :param url_type: url type (git_url, ssh_url, clone_url, svn_url)
        default:'clone_url'
        :type url_type: basestring
        :return: cloned repo
        """
        start = time.time()
        lgr.info('Clone or pull from {0} organization or user'
                 .format(self.organization))
        for repository in self.repository_specific_data:
            if repository['name'] not in self.ignore_repository:
                full_path = os.path.join(self.local_path, repository['name'])
                self._clone_or_pull(full_path, repository['name'],
                                    repository[url_type])
        total = _calculate_performance_to_second(start, time.time())
        lgr.debug('git clone\pull time: {0} seconds'.format(total))

    @retrying.retry(stop_max_attempt_number=3)
    def _clone_or_pull(self, full_path, repository_name, url):
        """ This method check if the repo exsist in the
         path and run clone or pull"""

        if os.path.isdir(full_path):
            try:
                lgr.info('Pull {0} repository.'.format(repository_name))
                git_pull = subprocess.check_output(
                    'git -C {0} pull {1}'.format(full_path, self.quiet_git),
                    shell=True)
            except subprocess.CalledProcessError as git_error:
                err = 'Error while run "git pull" on {0} : {1}'\
                    .format(repository_name, git_error)
                lgr.error(err)
                self.error_summary.append(err)
                pass
        else:
            try:
                lgr.info('Clone {0} repository.'.format(repository_name))
                git_clone = subprocess.check_output(
                    'git clone {0} {1} {2}'.format(self.quiet_git, url,
                                                   full_path), shell=True)
            except subprocess.CalledProcessError as git_error:
                err = 'Error while run "git clone" {0} : {1}'\
                    .format(repository_name, git_error)
                lgr.error(err)
                self.error_summary.append(err)
                pass

    def search_in_commits(self):
        """ This method search the secrets in the commits

        :return: problematic_commits blob_url
        """
        start = time.time()
        directories_list = self._get_directory_list()
        strings_list_to_search = self._create_search_strings()
        self.find_problematic_commits(directories_list, strings_list_to_search)
        total = _calculate_performance_to_second(start, time.time())
        lgr.debug('Search time: {0} seconds'.format(total))

    def _get_directory_list(self):
        """ Get list of the clone directory in the path"""
        full_path_list = []
        for item in os.listdir(self.local_path):
            path = os.path.join(self.local_path, item)
            if os.path.isdir(path):
                full_path_list.append(path)
        return full_path_list

    def _create_search_strings(self):
        """ Create part of the grep command from search list"""
        search_strings = self.search_list[0]
        self.search_list.remove(search_strings)
        for string in self.search_list:
            search_strings = "{0} --or -e '{1}'".format(search_strings, string)
        return search_strings

    def find_problematic_commits(self, directories, string_to_search):
        """ Search secret string in the commits file and
            save the blob_url of the bad files """
        for directory in directories:
            lgr.info('Now scan the {0} directory'.format(directory))
            self.repository_name = directory.split('/', -1)[-1]
            self._find_problematic_commits_in_directory(directory,
                                                        string_to_search)

    def _find_problematic_commits_in_directory(self, directory,
                                               string_to_search):
        """ Create list of all problematic commits"""
        bad_files = []
        for commit in self._get_all_commits_list(directory):
            bad_files.append(self._get_bad_files(directory,
                                                 commit, string_to_search))
        return self._write_to_db(bad_files)

    def _get_all_commits_list(self, directory):
        """ Get the sha(number) of the commit """
        try:
            commits = subprocess.check_output(
                'git -C {0} rev-list --all'.format(directory), shell=True)
            return commits.splitlines()
        except subprocess.CalledProcessError:
            return []

    def _get_bad_files(self, directory, commit, string_to_search):
        """ Run git grep"""
        try:
            bad_files = subprocess.check_output(
                'git -C {0} grep -l -e {1} {2}'.format(directory,
                                                       string_to_search,
                                                       commit), shell=True)
            return bad_files.splitlines()
        except subprocess.CalledProcessError:
            return []

    def _write_to_db(self, bad_commits):
        """ Create the blob_url from sha:filename and write to json"""
        urls_blob = []
        for bad_files in bad_commits:
            for bad_file in bad_files:
                try:
                    sha, file_name = bad_file.rsplit(':', 1)
                    blob_url = BLOB_URL_TEMPLATE.format(self.organization,
                                                        self.repository_name,
                                                        sha, file_name)
                    urls_blob.append(blob_url)
                    self._write_dict_to_db(sha, file_name, self.repository_name,
                                           '', blob_url)
                except IndexError:
                    # The structre of the output is
                    # sha:filename
                    # sha:filename
                    # filename
                    # None
                    # and we need both sha and filename and when we don't \
                    #  get them we do pass
                    pass
        return urls_blob

    def _print_error_summary(self):
        if self.error_summary:
            lgr.info(
                'Summary of all errors: \n{0}'.format(
                    '\n'.join(self.error_summary)))

    def check_on_organization(self):
        start = time.time()
        self.get_github_repo_list()
        self.clone_repo()
        self.search_in_commits()
        total = _calculate_performance_to_second(start, time.time())
        lgr.debug('Total time: {0} seconds'.format(total))
        self._print_error_summary()


def _calculate_performance_to_second(start, end):
    """ Calculate the runnig time"""
    return str(round(end - start, 3))


@click.group()
def main():
    pass


@click.command()
@click.option('-S', '--search', required=True, multiple=True,
              help='List of secrets you want to search.')
@click.option('-i', '--ignore', default=(' ', ' '), multiple=True,
              help='List of repo you didn\'t want to check.')
@click.option('-O', '--organization', required=True,
              help='Organization name.')
@click.option('-U', '--user', required=True,
              help='Git user name for authenticate.')
@click.password_option('-P', '--password', required=True,
                       help='Git user password for authenticate')
@click.option('-p', '--path', required=False, default=tempfile.gettempdir(),
              help='This path contain the repos clone.')
@click.option('-l', '--log', required=False, default='~/bad_commit.log',
              help='Log file for bad commits')
@click.option('-v', '--verbose', default=False, is_flag=True)
@click.option('-q', '--quiet', default=False, is_flag=True)
def args(search, ignore, organization, user, password, log, path,
         verbose, quiet):
    """ No config file, manual surch"""
    logger.configure()
    surch = Surch(search_list=search, skipped_repo=ignore,
                  organization=organization, git_user=user,
                  git_password=password, local_path=path,
                  log_path=log, verbose=verbose, quiet_git=quiet)
    surch.check_on_organization()


@click.command()
@click.option('-c', '--config', required=True,
              help='Config var file full path.')
@click.option('-v', '--verbose', default=False, is_flag=True)
@click.option('-q', '--quiet', default=False, is_flag=True)
def conf(config, verbose, quiet):
    """ Validate config file."""
    logger.configure()
    file_extension = os.path.splitext(config)[1].lower()
    if file_extension == '.yaml' or file_extension == '.yml':
        surch = Surch.from_config_file(config, verbose, quiet)
        surch.check_on_organization()
    else:
        lgr.error('Config file is not .YAML/.YML')


@click.command()
@click.option('-i', '--ignore', default=(' ', ' '), multiple=True,
              help='List of repo you didn\'t want to check.')
@click.option('-S', '--search', required=True, multiple=True,
              help='List of sensitive info.')
@click.option('-p', '--path', required=False, default=tempfile.gettempdir(),
              help='Local path with the clone repo (directory) for search')
@click.option('-l', '--log', required=False, default='~/bad_commit.log',
              help='Log file for bad commits')
@click.option('-O', '--organization', required=True,
              help='Organization name')
@click.option('-v', '--verbose', default=False, is_flag=True)
@click.option('-q', '--quiet', default=True, is_flag=False,
              help='IF on its mean no quiet')
def check(ignore, path, search, log, organization, verbose, quiet):
    """ Search secret in the local path repository."""
    logger.configure()
    surch = Surch(search_list=search, skipped_repo=ignore,
                  organization=organization, git_user=' ',
                  git_password=' ', local_path=path,
                  log_path=log, verbose=verbose, quiet_git=quiet)
    surch.search_in_commits()

main.add_command(args)
main.add_command(conf)
main.add_command(check)