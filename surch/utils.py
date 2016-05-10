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

import yaml


def get_and_init_vars_from_config_file(config_file, verbose=False,
                                       quiet_git=True):
    """ Define vars from "config.yaml" file"""
    with open(config_file, 'r') as config:
        conf_vars = yaml.load(config.read())
    conf_vars.setdefault('verbose', verbose)
    conf_vars.setdefault('quiet_git', quiet_git)
    return conf_vars


def print_error_summary(error_summary, lgr):
    if error_summary:
        lgr.info(
            'Summary of all errors: \n{0}'.format(
                '\n'.join(error_summary)))


def convert_to_seconds(start, end):
    """ Calculate the runnig time"""
    return str(round(end - start, 3))


def find_string_between_strings(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ' '