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
import json
import time

import requests

from surch import logger
from . import handler

lgr = logger.init()


class Pagerduty(object):
    def __init__(self, results_file_path, api_key, service_key, msg=None):
        self.dicts_number =\
            handler.count_dicts_in_results_file(results_file_path)
        self.today_date = time.strftime('%Y-%m-%d')
        self.msg = msg or 'Surch alert run check on {0} and found {1} commits.'\
            .format(self.today_date, self.dicts_number)
        self.api_key = api_key
        self.service_key = service_key

    def trigger_incident(self):
        headers = {'Authorization': 'Token token={0}'.format(self.api_key),
                   'Content-type': 'application/json', }
        payload = json.dumps({
            "service_key": self.service_key,
            "incident_key": "srv01/HTTP",
            "event_type": "trigger",
            "description": self.msg,
            "client": "Surch service",
            "details": {"ping time": "1500ms",
                        "load avg": 0.75}})
        requests.post(
            'https://events.pagerduty.com/generic/2010-04-15/create_event.json',
            headers=headers, data=payload, )

    def trigger(self):
        if self.dicts_number > 0:
            self.trigger_incident()
            lgr.info('Pagerduty alert: "{0}"'.format(self.msg))


def trigger(results_file_path, api_key, service_key, msg=None):
    pager = Pagerduty(results_file_path=results_file_path, api_key=api_key,
                      service_key=service_key, msg=msg)
    pager.trigger()