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


def setup_logger():
    """Define logger level
    """
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger = logging.getLogger('surch')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

logger = setup_logger()


def merge_2_list(list1, list2):
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


def remove_repos_folder(path=None):
    """print log and removing directory"""
    logger.info('Removing: {0}...'.format(path))
    shutil.rmtree(path)


def print_errors_summary(error_summary):
    logger.info('Summary of all errors: \n{0}'.format(
        '\n'.join(error_summary)))


def print_result_file(result_file=None):
    with open(result_file) as results_file:
        results = results_file.read()
    logger.info(results)


def convert_to_seconds(start, end):
    return str(round(end - start, 3))


def find_string_between_strings(string, first, last):
    try:
        start = string.index(first) + len(first)
        end = string.index(last, start)
        return string[start:end]
    except ValueError:
        return ' '


def check_if_executable_exists_else_exit(executable):
    if not find_executable(executable):
        logger.error(
            '{0} executable not found and is required'.format(executable))
        sys.exit(1)


def handle_results_file(results_file_path,
                        consolidate_log):
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
