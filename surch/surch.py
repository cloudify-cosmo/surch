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

import click

from . import utils
from . import constants
from . import commit, repo, organization, members
from .exceptions import SurchError

utils._create_surch_env()

CLICK_CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'],
                              token_normalize_func=lambda param: param.lower())


config_file = click.option('-c', '--config-file', default=None,
                           type=click.Path(exists=False, file_okay=True),
                           help='A path to a Surch config file')

search_string = click.option('-s', '--string', multiple=True, default=[],
                             help='String you would like to search for.\n'
                                  'This can be passed multiple times')

cloned_repos_dir = click.option(
    '-p', '--cloned-repos-dir', default=None,
    help='Directory to clone repository to.\n'
         '[defaults to {0}/<repo-name>]'.format(constants.CLONED_REPOS_PATH))

log_path = click.option(
    '-l', '--log', default=constants.RESULTS_PATH,
    help='All results will be logged to this directory.\n'
         '[defaults to \r{0}]'.format(constants.RESULTS_PATH))

remove_clone = click.option('-R', '--remove', default=False, is_flag=True,
                            help='Remove clone repo directory.\n'
                                 'Don\'t used when -p and -l is the same path.')

remove_member_clone = click.option('--remove-member-clone', default=False,
                                   is_flag=True,
                                   help='Remove member clone directory '
                                        'after finish check him.\n '
                                        'Don\'t used when -p and -l is '
                                        'the same path.')

remove_repo_clone = click.option('--remove-repo-clone', default=False,
                                 is_flag=True,
                                 help='Remove clone repo directory '
                                      'after finish to check him.\n'
                                      'Don\'t used when -p and -l is '
                                      'the same path.')

pager = click.option('--pager', multiple=True, default=[],
                     help='Pager plugin to use')

source = click.option('--source', multiple=True, default=[],
                      help='Data source plugin to use')

exclude_repo = click.option('--exclude-repo', default=None, multiple=True,
                            help='Repo you would like to exclude. '
                                 'This can be passed multiple times')
include_repo = click.option('--include-repo', default=None, multiple=True,
                            help='Repo you would like to include. '
                                 'This can be passed multiple times.')

exclude_user = click.option('--exclude-user', default=None, multiple=True,
                            help='User you would like to exclude. '
                                 'This can be passed multiple times')
include_user = click.option('--include-user', default=None, multiple=True,
                            help='User you would like to include. '
                                 'This can be passed multiple times.')

github_user = click.option('-U', '--user', default=None, help='GitHub username')
github_password = click.option('-P', '--password', default=None,
                               help='GitHub password')

printout = click.option('--print-result', default=False, is_flag=True)
verbose = click.option('-v', '--verbose', default=False, is_flag=True)


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
def main():
    pass

@main.command(name='commit')
@click.argument('commit_sha',
                required=True)
@search_string
@cloned_repos_dir
@log_path
@verbose
# @config_file
# @log_path
# @pager
# @source
# @printout
def surch_commit(commit_sha, cloned_repos_dir, string, log, verbose):
    """Search a single commit.
         "surch commit 08123a835a5344645fasdb015f786088045652c8 -p /home/user/surch -s hello"
        """
    try:
        commit.search(search_list=string, commit_sha=commit_sha,
                      cloned_repo_dir=cloned_repos_dir,
                      results_file_path=log, verbose=verbose)
    except SurchError as ex:
        sys.exit(ex)


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
def surch_repo(repo_url, cloned_repos_dir, string, log, verbose, remove):
    """Search a single repository.

        You can add user_name and password. Used surch like that:

         "surch repo 'https://<user>:<pass>@github.com/cloudify-cosmo/surch.git'"
        """
    try:
        repo.search(repo_url=repo_url, cloned_repo_dir=cloned_repos_dir,
                    search_list=string, results_file_path=log,
                    remove_clone_dir=remove, verbose=verbose)
    except SurchError as ex:
        sys.exit(ex)


@main.command(name='org')
@click.argument('organization-name', required=False)
@search_string
@cloned_repos_dir
@log_path
@verbose
@remove_clone
@github_user
@github_password
@exclude_repo
@include_repo
@remove_repo_clone
# @config_file
# @pager
# @source
# @printout
def surch_org(organization_name, string, include_repo, exclude_repo, user,
              remove, password, cloned_repos_dir, log, verbose,
              remove_repo_clone):
    """Search all or some repositories in an organization
    """
    try:
        organization.search(git_item_name=organization_name,
                            is_organization=True, git_user=user,
                            git_password=password, search_list=string,
                            results_file_path=log,
                            cloned_repos_dir=cloned_repos_dir,
                            repos_to_skip=exclude_repo,
                            repos_to_check=include_repo,
                            remove_clones_dir=remove, verbose=verbose,
                            remove_per_repo=remove_repo_clone)
    except SurchError as ex:
        sys.exit(ex)


@main.command(name='user')
@click.argument('username', required=False)
@search_string
@cloned_repos_dir
@log_path
@verbose
@remove_clone
@github_user
@github_password
@exclude_repo
@include_repo
@remove_repo_clone
# @config_file
# @pager
# @source
# @printout
def surch_user(username, string, include_repo, exclude_repo, user, remove,
               password, cloned_repos_dir, log, verbose):
    """Search all or some repositories in an organization
    """
    try:
        organization.search(git_item_name=username, is_organization=False,
                            git_user=user, git_password=password,
                            search_list=string, results_file_path=log,
                            cloned_repos_dir=cloned_repos_dir,
                            repos_to_skip=exclude_repo,
                            repos_to_check=include_repo,
                            remove_clones_dir=remove, verbose=verbose,
                            remove_per_repo=remove_repo_clone)
    except SurchError as ex:
        sys.exit(ex)


@main.command(name='members')
@click.argument('organization-name', required=False)
@search_string
@cloned_repos_dir
@log_path
@verbose
@remove_clone
@github_user
@github_password
@exclude_user
@include_user
@remove_repo_clone
@remove_member_clone
# @config_file
# @pager
# @source
# @printout
def surch_org_members(organization_name, string, include_user, exclude_user,
                      user, remove, password, cloned_repos_dir, log, verbose,
                      remove_repo_clone, remove_member_clone):
    """Search all or some members in an organization
    """
    try:
        members.search(git_user=user, git_password=password,
                       organization_name=organization_name, search_list=string,
                       results_file_path=log, cloned_repos_dir=cloned_repos_dir,
                       users_to_skip=exclude_user, users_to_check=include_user,
                       remove_clones_dir=remove, verbose=verbose,
                       remove_per_repo=remove_repo_clone,
                       remove_per_member=remove_member_clone)
    except SurchError as ex:
        sys.exit(ex)
