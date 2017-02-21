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

import sys

import os
import click

from . import repo
from . import utils
from . import constants
from . import organization
from .exceptions import SurchError

utils._create_surch_env()

CLICK_CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help'],
    token_normalize_func=lambda param: param.lower())


config_file = click.option(
    '-c',
    '--config-file',
    default=None,
    type=click.Path(exists=False, file_okay=True),
    help='A path to a Surch config file')

search_string = click.option(
    '-s',
    '--string',
    multiple=True,
    help='String you would like to search for.\n'
         'This can be passed multiple times')

cloned_repos_dir = click.option(
    '-p',
    '--cloned-repos-dir',
    default=None,
    help='Directory to clone repository to.\n'
         '[defaults to {0}/<repo-name>]'.format(constants.CLONED_REPOS_PATH))

log_path = click.option(
    '-l',
    '--log',
    default=constants.RESULTS_PATH,
    help='All results will be logged to this directory.\n'
         '[defaults to \r{0}]'.format(constants.RESULTS_PATH))

remove_clone = click.option(
    '-R',
    '--remove',
    default=False,
    is_flag=True,
    help='Remove clone repo directory.\n'
         'Don\'t used when -p and -l is the same path.')

pager = click.option(
    '--pager',
    multiple=True,
    default=[],
    help='Pager plugin to use')

source = click.option(
    '--source',
    multiple=True,
    default=[],
    help='Data source plugin to use')

printout = click.option('--print-result', default=False, is_flag=True)
verbose = click.option('-v', '--verbose', default=False, is_flag=True)


exclude_repo = click.option(
    '--exclude-repo',
    default='',
    multiple=True,
    help='Repo you would like to exclude. '
    'This can be passed multiple times')

include_repo = click.option(
    '--include-repo',
    default='',
    multiple=True,
    help='Repo you would like to include. '
    'This can be passed multiple times.')

github_user = click.option(
    '-U',
    '--user',
    default=None,
    help='GitHub username')

github_password = click.option(
    '-P',
    '--password',
    default=None,
    help='GitHub password')


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
def main():
    pass


@main.command(name='repo')
@click.argument('repo_url',
                required=True)
@search_string
@cloned_repos_dir
@log_path
@verbose
@remove_clone
# @config_file
# @log_path
# @pager
# @source
# @printout
def surch_repo(repo_url, cloned_repos_dir, string, log, verbose,
               remove, **kwargs):
    """Search a single repository.

        You can add user_name and password. Used surch like that:

         "surch repo 'https://<user>:<pass>@github.com/cloudify-cosmo/surch.git'"
        """
    repo_name, organization = utils._get_repo_and_organization_name(repo_url)
    cloned_repos_dir = cloned_repos_dir or os.path.join(
        constants.CLONED_REPOS_PATH, organization, repo_name)
    try:
        repo.search(repo_url=repo_url, cloned_repo_dir=cloned_repos_dir,
                    search_list=string, results_file_path=log,
                    remove_clone=remove, verbose=verbose)
    except SurchError as ex:
        sys.exit(ex)


#
# @main.command(name='org')
# @click.argument('organization-name', required=False)
# @config_file
# @search_string
# @cloned_repos_path
# @log_path
# @remove_clone
# @exclude_repo
# @include_repo
# @github_user
# @github_password
# @pager
# @source
# @printout
# @verbose
# def surch_org(organization_name,
#               config_file,
#               string,
#               include_repo,
#               pager,
#               exclude_repo,
#               user,
#               print_result,
#               remove,
#               password,
#               source,
#               cloned_repos_dir,
#               log,
#               verbose):
#     """Search all or some repositories in an organization
#     """
#     try:
#         organization.search(
#             pager=pager,
#             source=source,
#             git_user=user,
#             results_dir=log,
#             verbose=verbose,
#             repos_to_skip=exclude_repo,
#             repos_to_check=include_repo,
#             git_password=password,
#             config_file=config_file,
#             remove_cloned_dir=remove,
#             search_list=list(string),
#             print_result=print_result,
#             organization=organization_name,
#             cloned_repos_dir=cloned_repos_dir)
#     except SurchError as ex:
#         sys.exit(ex)
#
#
# @main.command(name='user')
# @click.argument('username', required=False)
# @config_file
# @search_string
# @cloned_repos_path
# @log_path
# @remove_clone
# @exclude_repo
# @include_repo
# @github_user
# @github_password
# @pager
# @source
# @printout
# @verbose
# def surch_user(user_name,
#                config_file,
#                string,
#                include_repo,
#                pager,
#                exclude_repo,
#                user,
#                remove,
#                password,
#                cloned_repos_dir,
#                log,
#                print_result,
#                source,
#                verbose):
#     """Search all or some repositories for a user
#     """
#     try:
#         organization.search(
#             pager=pager,
#             source=source,
#             git_user=user,
#             results_dir=log,
#             verbose=verbose,
#             repos_to_skip=exclude_repo,
#             repos_to_check=include_repo,
#             is_organization=False,
#             git_password=password,
#             config_file=config_file,
#             remove_cloned_dir=remove,
#             search_list=list(string),
#             print_result=print_result,
#             organization=user_name,
#             cloned_repos_dir=cloned_repos_dir)
#     except SurchError as ex:
#         sys.exit(ex)
