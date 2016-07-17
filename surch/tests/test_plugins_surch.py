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
import mock

import testtools

from surch import utils
import surch.surch as surch
from surch import constants
from surch.plugins import vault
from surch.plugins import handler
from surch.plugins import pagerduty

path = os.path.abspath(__file__)
path = path.rsplit('/', 1)[0]
config_file_path = os.path.join(path, 'config/plugin_conf.yaml')


class TestHandler(testtools.TestCase):
    def test_plugins_handle(self):
        plugins_list = (u'pagerduty',)
        config_file = config_file_path
        plugins_list = handler.plugins_handle(plugins_list=plugins_list,
                                              config_file=config_file)
        self.assertTrue("['pagerduty']" in str(plugins_list))

    @mock.patch.object(handler, 'vault_trigger',
                       mock.Mock(return_value=('string-4', 'string-5')))
    def test_merge_all_search_list(self):
        source = ('vault')
        config_file = config_file_path
        search_list = ('string-6', 'string-7')
        search_list = \
            handler.merge_all_search_list(source, config_file, search_list)
        self.assertTrue(
            'string-6' and 'string-4' and 'string-1' in search_list)
