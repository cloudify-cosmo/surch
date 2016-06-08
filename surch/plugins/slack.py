import json
import time

import requests

from .. import logger

lgr = logger.init()


class Slack(object):
    def __init__(self,
                 channel,
                 results_file_path,
                 incoming_webhooks_url,
                 msg=None,
                 sender_name="Surch-Bot"):

        self.dicts_number = \
            self.count_dicts_in_results_file(results_file_path)
        self.today_date = time.strftime('%Y-%m-%d')
        self.msg = msg or 'Surch alert run check on {0} and found {1} commits.'\
            .format(self.today_date, self.dicts_number)
        self.incoming_webhooks_url = incoming_webhooks_url
        self.channel = channel
        self.sender_name = sender_name

    @staticmethod
    def count_dicts_in_results_file(file_path):
        i = 0
        try:
            with open(file_path) as results_file:
                results = json.load(results_file)
            for key, value in results.items():
                for k, v in value.items():
                    i += 1
        except:
            pass
        return i

    def trigger_incident(self):
        headers = {'Content-type': 'application/json', }
        payload = json.dumps({"channel": self.channel,
                              "username":self.sender_name,
                              "text": self.msg})
        requests.post(self.incoming_webhooks_url,
                      headers=headers, data=payload, )

    def trigger(self):
        if self.dicts_number > 0:
            self.trigger_incident()
            lgr.info('Slack alert: "{0}"'.format(self.msg))


def trigger(results_file_path, incoming_webhooks_url, channel, msg=None):
    slack = Slack(msg=msg,
                  channel=channel,
                  results_file_path=results_file_path,
                  incoming_webhooks_url=incoming_webhooks_url)
    slack.trigger()



