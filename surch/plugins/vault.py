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
import re
import os
from collections import deque

import hvac

KEY_LIST = ('.*password.*', '.*secret.*', '.*id.*', '*endpoint*',
            '*tenant*', '*api*')


class Vault(object):
    def __init__(self, vault_url, vault_token, secret_path, key_list=KEY_LIST):
        self.secret_path = secret_path
        self.key_list = key_list
        self.client = hvac.Client(url=vault_url, token=vault_token)
        print '0'*20
        print self.client
        print '0'*20
        
    def keys_list(self, extra_path=''):
        all_data = self.client.list(os.path.join(self.secret_path, extra_path))
        data = all_data['data']
        return data['keys']

    def get_search_list(self):
        search_list = []
        secret_names = deque()
        secret_names.extend(self.keys_list())

        while len(secret_names) != 0:
            secret = secret_names.popleft().encode('ascii')
            if secret.endswith('/'):
                keys = self.keys_list(extra_path=secret)
                secret_names.extend(
                    [os.path.join(secret, key) for key in keys])
                continue

            secret_from_vault = self.client.read(
                '{0}/{1}'.format(self.secret_path, secret))
            secret_from_vault = secret_from_vault['data']
            for key, value in secret_from_vault.items():
                for regex in self.key_list:
                    p = re.compile(regex.lower())
                    if value:
                        if p.match(key.lower()):
                            if 'ssh-rsa' not in value.lower():
                                try:
                                    value = "{0}".format(value.encode('ascii'))
                                    if 'password' not in value.lower():
                                        search_list.append(re.escape(value))
                                    else:
                                        pass
                                except AttributeError:
                                    search_list.append(value)
        return search_list


def get_search_list(vault_url, vault_token, secret_path, key_list=None):
    key_list = KEY_LIST if not key_list else key_list
    vault = Vault(vault_url=vault_url, vault_token=vault_token,
                  secret_path=secret_path, key_list=key_list)
    return vault.get_search_list()
