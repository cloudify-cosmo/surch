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
import click
from . import logger, repo, organization

lgr = logger.init()

HOME_PATH = os.path.expanduser("~")
DEFAULT_PATH = os.path.join(HOME_PATH, 'surch')
LOG_PATH = os.path.join(HOME_PATH, 'results.json')


@click.group()
def main():
    pass


@main.group(name='repo')
def repository():
    """ Run surch on repository """
    pass


@repository.command(name='search')
@click.argument('repo_url')
@click.option('-c', '--config', default=None,
              type=click.Path(exists=False, file_okay=True),
              help='Config var file full path.')
@click.option('-S', '--strings', required=True, multiple=True,
              help='List of secrets you want to search.')
@click.option('-p', '--path', required=False, default=DEFAULT_PATH,
              help='This path contain the repos clone.')
@click.option('-l', '--log', required=False, default=LOG_PATH,
              help='Log file for bad commits')
@click.option('-v', '--verbose', default=False, is_flag=True)
@click.option('-q', '--quiet', default=True, is_flag=False)
def repository_search(strings, repo_url, log, path, verbose, quiet, config):
    """check single repository"""
    logger.configure()
    if config:
        config_file_extension = os.path.splitext(config)[1].lower()
        if config_file_extension == '.yaml' or config_file_extension == '.yml':
            repository_local = repo.Repo.get_and_init_vars_from_config_file(
                config, verbose, quiet)
            repository_local.search()
        else:
            lgr.error('Config file is not .YAML/.YML')
    else:
        if path == DEFAULT_PATH:
            lgr.info('Default directory path is: {0}'.format(DEFAULT_PATH))
        if log == LOG_PATH:
            lgr.info('Default log path is: {0}'.format(LOG_PATH))
        repo.search(search_list=strings, repo_url=repo_url, local_path=path,
                    log_path=log, verbose=verbose, quiet_git=quiet)


@main.group()
def org():
    """ Run surch on organization """
    pass


@org.command(name='search')
@click.argument('organization_name')
@click.option('-c', '--config', default=None,
              type=click.Path(exists=False, file_okay=True),
              help='Config var file full path.')
@click.option('-S', '--search', required=True, multiple=True,
              help='List of secrets you want to search.')
@click.option('-i', '--ignore', default=(' ', ' '), multiple=True,
              help="List of repo you didn't want to check.")
@click.option('-U', '--user', default=None,
              help='Git user name for authenticate.')
@click.password_option('-P', '--password', default=None,
                       help='Git user password for authenticate')
@click.option('-p', '--path', required=False, default=DEFAULT_PATH,
              help='This path contain the repos clone.')
@click.option('-l', '--log', required=False, default=LOG_PATH,
              help='Log file for bad commits')
@click.option('-v', '--verbose', default=False, is_flag=True)
@click.option('-q', '--quiet', default=False, is_flag=True)
def organization_search(search, ignore, organization_name, user,
                        password, log, path, verbose, quiet, config):
    ''' Run surch on organization'''
    logger.configure()
    if config:
        config_file_extension = os.path.splitext(config)[1].lower()
        if config_file_extension == '.yaml' or config_file_extension == '.yml':
            repository_local = repo.Repo.get_and_init_vars_from_config_file(
                config, verbose, quiet)
            repository_local.search()
        else:
            lgr.error('Config file is not .YAML/.YML')
    else:
        if path == DEFAULT_PATH:
            lgr.info('Default directory path is: {0}'.format(DEFAULT_PATH))
        if log == LOG_PATH:
            lgr.info('Default log path is: {0}'.format(LOG_PATH))
        if not user or not password:
            lgr.info('**********ATTENSION********** \n'
                     'You run without authunticate git'
                     ' allows you to make up to 60 requests per hour')
        organization.search(search_list=search, skipped_repo=ignore,
                            organization=organization_name, git_user=user,
                            git_password=password, local_path=path,
                            log_path=log, verbose=verbose, quiet_git=quiet)


repository.add_command(repository_search)
org.add_command(organization_search)
