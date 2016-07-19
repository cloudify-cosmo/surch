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
import shutil

import testtools

from surch import utils
from surch.plugins import vault
from surch.plugins import handler
from surch.plugins import pagerduty

path = os.path.abspath(__file__)
path = path.rsplit('/', 1)[0]
config_file_path = os.path.join(path, 'config/plugin_conf.yaml')
results_file_path = os.path.join(path, 'config/results.json')

paths_keys = {u'auth': None,
              u'data': {u'keys': [u'Jenkins', u'ec2automation']},
              u'lease_duration': 0,
              u'lease_id': u'',
              u'renewable': False,
              u'warnings': None}

paths_secrets = {u'lease_id': u'',
                 u'warnings': None,
                 u'auth': None,
                 u'lease_duration': 7776000,
                 u'data': {u'JENKINS_password': u'jenkins',
                           u'aws_password': u'aws',
                           u'azure_tenant': u'azure',
                           u'JENKINS_id': u'username'},
                 u'renewable': False}

temp_secrets = {u'lease_id': u'',
                u'warnings': None,
                u'auth': None,
                u'lease_duration': 7776000,
                u'data': {u'TEMP1': u'1',
                          u'TEMP2': u'2'},
                u'renewable': False}


class TestHandler(testtools.TestCase):
    def test_plugins_handle(self):
        plugins_list = (u'pagerduty',)
        config_file = config_file_path
        plugins_list = handler.plugins_handle(plugins_list=plugins_list,
                                              config_file=config_file)
        self.assertTrue("['pagerduty']" in str(plugins_list))

    @mock.patch.object(handler, 'vault_trigger',
                       mock.Mock(return_value=('string-2', 'string-2')))
    def test_merge_all_search_list(self):
        source = ('vault')
        config_file = config_file_path
        search_list = ('string-3', 'string-3')
        search_list = \
            handler.merge_all_search_list(source, config_file, search_list)
        self.assertTrue(
            'string-1' and 'string-2' and 'string-3' in search_list)


class TestPagerduty(testtools.TestCase):
    def test_pagerduty_trigger_200(self):
        api_key = 'zOjKTFAIRSufjZeAExYD'
        service_key = 'qq6ed4o6ytle6ohmusmhtm41n3fuihef'
        trigger = pagerduty.trigger(results_file_path, api_key, service_key)
        self.assertTrue('<Response [200]>' in str(trigger))

    def test_pagerduty_trigger_400(self):
        api_key = 'zOjKTFAIRSufjZeAEx'
        service_key = 'qq6ed4o6ytle6ohmusmhtm41n3fuih'
        trigger = pagerduty.trigger(results_file_path, api_key, service_key)
        self.assertTrue('<Response [400]>' in str(trigger))


class TestVault(testtools.TestCase):
    @mock.patch('hvac.Client.list', return_value=paths_keys)
    @mock.patch('hvac.Client.read', return_value=paths_secrets)
    def test_vault_read(self, *args):
        working_dir = os.path.join(path, 'work-dir')
        shutil.rmtree(working_dir, ignore_errors=True)
        os.makedirs(working_dir)
        content = vault.get_search_list(vault_url='url', vault_token='token',
                                        secret_path='secret/builds/jenkins',
                                        key_list=None)
        print content
        self.assertIn('aws', content)
        self.assertIn('username', content)
        self.assertIn('jenkins', content)
        utils.remove_repos_folder(working_dir)
