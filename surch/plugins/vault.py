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

import hvac

KEY_LIST = ('.*password.*', '.*secret.*', '.*id.*', '*endpoint*',
            '*tenant*', '*api*')


class Vault(object):
    def __init__(self, vault_url, vault_token, secret_path, key_list=KEY_LIST):
        self.vault_url = vault_url
        self.vault_token = vault_token
        self.secret_path = secret_path
        self.key_list = key_list

    def get_search_list(self):
        search_list = []
        client = hvac.Client(url=self.vault_url, token=self.vault_token)
        all_data = client.read('{0}?list=true'.format(self.secret_path))
        data = all_data['data']
        secret_names = data['keys']

        for secret in secret_names:
            secret = secret.encode('ascii')
            secret_from_vault = client.read('{0}/{1}'.format(self.secret_path,
                                                             secret))

            secret_from_vault = secret_from_vault['data']

            for key, value in secret_from_vault.items():
                for regex in self.key_list:
                    p = re.compile(regex.lower())
                    if value:
                        if p.match(key.lower()):
                            if 'ssh-rsa' not in value.lower():
                                try:
                                    value = "{0}".format(value.encode('ascii'))
                                    search_list.append(re.escape(value))
                                except AttributeError:
                                    search_list.append(value)
        return search_list


def get_search_list(vault_url, vault_token, secret_path, key_list=None):
    key_list = KEY_LIST if not key_list else key_list
    vault = Vault(vault_url=vault_url, vault_token=vault_token,
                  secret_path=secret_path, key_list=key_list)
    return vault.get_search_list()
