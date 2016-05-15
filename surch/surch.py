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

import click
import shutil

from . import logger, repo, organization, constants, pagerduty

lgr = logger.init()


@click.group()
def main():
    pass


@main.command(name='repo')
@click.argument('repo_url')
@click.option('-c', '--config-file', default=None,
              type=click.Path(exists=False, file_okay=True),
              help='A path to a Surch config file')
@click.option('-s', '--string', multiple=True,
              help='String you would like to search for. '
                   'This can be passed multiple times.')
@click.option('-p', '--cloned-repo-path', default=constants.DEFAULT_PATH,
              help='Directory to clone repository to.')
@click.option('-l', '--log', default=constants.RESULTS_PATH,
              help='All results will be logged to this file. '
                   '[defaults to {0}]'.format(constants.RESULTS_PATH))
@click.option('-R', '--remove', default=False, is_flag=True,
              help='Remove clones repos')
@click.option('--pager', default=False,
              help='This arg need to be api_key::service_key')
@click.option('-v', '--verbose', default=False, is_flag=True)
def surch_repo(repo_url, config_file, string, pager,
               remove, cloned_repo_path, log, verbose):
    """Search a single repository"""
    logger.configure()
    repo.search(
        config_file=config_file,
        search_list=list(string),
        repo_url=repo_url,
        cloned_repo_path=cloned_repo_path,
        results_file_path=log,
        verbose=verbose)
    if pager:
        pagerduty.trigger(log_path=log, keys=pager)

    if remove:
        shutil.rmtree(cloned_repo_path)


@main.command(name='org')
@click.argument('organization_name', required=False)
@click.option('-c', '--config-file', default=None,
              type=click.Path(exists=False, file_okay=True),
              help='A path to a Surch config file')
@click.option('-s', '--string', multiple=True,
              help='String you would like to search for. '
                   'This can be passed multiple times.')
@click.option('--skip', default='', multiple=True,
              help='Repo you would like to skip. '
                   'This can be passed multiple times.')
@click.option('-U', '--user', default=None,
              help='Git user name for authenticate.')
@click.option('-P', '--password', default=None, required=False,
              help='Git user password for authenticate')
@click.option('-p', '--cloned-repos-path', default=constants.DEFAULT_PATH,
              help='Directory to contain all cloned repositories.')
@click.option('-l', '--log', default=constants.RESULTS_PATH,
              help='All results will be logged to this file. '
                   '[defaults to {0}]'.format(constants.RESULTS_PATH))
@click.option('-R', '--remove', default=False, is_flag=True,
              help='Remove clones repos')
@click.option('--pager', default=False,
              help='This arg need to be api_key::service_key')
@click.option('-v', '--verbose', default=False, is_flag=True)
def surch_org(organization_name, config_file, string, skip, user,
              pager, remove, password, cloned_repos_path, log, verbose):
    """Surch all repositories in an organization"""
    logger.configure()
    organization.search(
        config_file=config_file,
        search_list=list(string),
        repos_to_skip=skip,
        organization=organization_name,
        git_user=user,
        git_password=password,
        cloned_repos_path=cloned_repos_path,
        results_file_path=log,
        verbose=verbose)
    if pager:
        pagerduty.trigger(log_path=log, keys=pager)

    if remove:
        shutil.rmtree(cloned_repos_path)
