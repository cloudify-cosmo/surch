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
import shutil
import logging
from datetime import datetime
from distutils.spawn import find_executable

import yaml

from . import constants
from .exceptions import SurchError


def _create_surch_env():
    if not os.path.exists(constants.CLONED_REPOS_PATH):
        os.makedirs(constants.CLONED_REPOS_PATH)
    if not os.path.exists(constants.RESULTS_DIR_PATH):
        os.makedirs(constants.RESULTS_DIR_PATH)


def _get_repo_and_organization_name(repo_url, type=None):
    if not type:
        organization_name = repo_url.rsplit('.com/', 1)[-1].rsplit('/', 1)[0]
        repo_name = repo_url.rsplit('/', 1)[-1].rsplit('.', 1)[0]
        return repo_name.encode('ascii'), organization_name.encode('ascii')
    elif 'repo' in type:
        repo_name = repo_url.rsplit('/', 1)[-1].rsplit('.', 1)[0]
        return repo_name.encode('ascii')
    elif 'org' in type:
        organization_name = repo_url.rsplit('.com/', 1)[-1].rsplit('/', 1)[0]
        return organization_name.encode('ascii')


def setup_logger(verbose=False):
    """Define logger level
    """
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger = logging.getLogger('Surch')
    logger.addHandler(handler)
    if not verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)
    return logger


def set_logger(verbose):
    lgr = logger
    if verbose:
        lgr.setLevel(logging.DEBUG)
    return lgr

logger = setup_logger()


def merge_to_list(list1, list2):
    list = []
    for value in list1:
        value = value.encode('ascii')
        list.append(value)
    for value in list2:
        value = value.encode('ascii')
        list.append(value)
    return list


def read_config_file(config_file,
                     pager=None,
                     source=None,
                     verbose=False,
                     search_list=None,
                     print_result=False,
                     is_organization=True,
                     remove_cloned_dir=False):
    """Define vars from "config.yaml" file
    """
    with open(config_file) as config:
        conf_vars = yaml.load(config.read())

    search_list = search_list or []
    try:
        for value in search_list:
            value = value.encode('ascii')
            conf_vars['search_list'].append(value)
    except KeyError:
        search_list = search_list
    conf_vars.setdefault('pager', pager)
    conf_vars.setdefault('source', source)
    conf_vars.setdefault('config_file', config_file)
    conf_vars.setdefault('search_list', search_list)
    conf_vars.setdefault('print_result', print_result)
    conf_vars.setdefault('verbose', verbose)
    conf_vars.setdefault('is_organization', is_organization)
    conf_vars.setdefault('remove_cloned_dir', remove_cloned_dir)
    return conf_vars


def _remove_repos_folder(path=None, remove_cloned_dir=False):
    """print log and removing directory"""
    if remove_cloned_dir:
        logger.info('Removing: {0}...'.format(path))
        shutil.rmtree(path)


def convert_to_seconds(start, end):
    return str(round(end - start, 3))


def find_string_between_strings(string, first, last):
    try:
        start = string.index(first) + len(first)
        end = string.index(last, start)
        return string[start:end]
    except ValueError:
        return ' '


def assert_executable_exists(executable):
    if not find_executable(executable):
        raise SurchError(
            '{0} executable not found and is required'.format(executable))


def handle_results_file(results_file_path, consolidate_log):
    dirname = os.path.dirname(results_file_path)
    if not os.path.isdir(os.path.dirname(results_file_path)):
        os.makedirs(dirname)
    if os.path.isfile(results_file_path):
        if not consolidate_log:
            timestamp = str(datetime.now().strftime('%Y%m%dT%H%M%S'))
            new_log_file = results_file_path + '.' + timestamp
            logger.info(
                'Previous results file found. Backing up '
                'to {0}'.format(new_log_file))
            shutil.move(results_file_path, new_log_file)
