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


@main.group()
def repos():
    pass


@repos.command(name='args')
@click.option('-S', '--strings', required=True, multiple=True,
              help='List of secrets you want to search.')
@click.option('-u', '--url', required=True,
              help='Git http url.')
@click.option('-p', '--path', required=False, default=DEFAULT_PATH,
              help='This path contain the repos clone.')
@click.option('-l', '--log', required=False, default=LOG_PATH,
              help='Log file for bad commits')
@click.option('-v', '--verbose', default=False, is_flag=True)
@click.option('-q', '--quiet', default=True, is_flag=False)
def repository_args(strings, url, log, path, verbose, quiet):
    """check single repository"""
    logger.configure()
    repo.repo_search(search_list=strings, url=url, local_path=path, log_path=log,
                verbose=verbose, quiet_git=quiet)


@repos.command(name='conf')
@click.option('-c', '--config', required=True,
              help='Config var file full path.')
@click.option('-v', '--verbose', default=False, is_flag=True)
@click.option('-q', '--quiet', default=False, is_flag=True)
def repository_conf(config, verbose, quiet):
    """ Validate config file."""
    logger.configure()
    config_file_extension = os.path.splitext(config)[1].lower()
    if config_file_extension == '.yaml' or config_file_extension == '.yml':
        repository = repo.Repo.from_config_file(config, verbose, quiet)
        repository._search()
    else:
        lgr.error('Config file is not .YAML/.YML')


@main.group()
def org():
    pass


@org.command(name='args')
@click.option('-S', '--search', required=True, multiple=True,
              help='List of secrets you want to search.')
@click.option('-i', '--ignore', default=(' ', ' '), multiple=True,
              help="List of repo you didn't want to check.")
@click.option('-O', '--organization', required=True,
              help='Organization name.')
@click.option('-U', '--user', required=True,
              help='Git user name for authenticate.')
@click.password_option('-P', '--password', required=True,
                       help='Git user password for authenticate')
@click.option('-p', '--path', required=False, default=DEFAULT_PATH,
              help='This path contain the repos clone.')
@click.option('-l', '--log', required=False, default=LOG_PATH,
              help='Log file for bad commits')
@click.option('-v', '--verbose', default=False, is_flag=True)
@click.option('-q', '--quiet', default=False, is_flag=True)
def organization_args(search, ignore, organization, user,
                      password, log, path, verbose, quiet):
    """ No config file, manual surch"""
    logger.configure()
    organization.search(search_list=search, skipped_repo=ignore,
                        organization=organization, git_user=user,
                        git_password=password, local_path=path, log_path=log,
                        verbose=verbose, quiet_git=quiet)


@org.command(name='conf')
@click.option('-c', '--config', required=True,
              help='Config var file full path.')
@click.option('-v', '--verbose', default=False, is_flag=True)
@click.option('-q', '--quiet', default=False, is_flag=True)
def organization_conf(config, verbose, quiet):
    """ Validate config file."""
    logger.configure()
    config_file_extension = os.path.splitext(config)[1].lower()
    if config_file_extension == '.yaml' or config_file_extension == '.yml':
        organization_local = organization.Organization.from_config_file(config, verbose, quiet)
        organization_local._search()
    else:
        lgr.error('Config file is not .YAML/.YML')

main.add_command(repository_args)
main.add_command(repository_conf)
main.add_command(organization_conf)
main.add_command(organization_args)