import json
import sys

from surch import utils, logger
from . import pagerduty

lgr = logger.init()


def pagerduty_trigger(config_file=None, log=None, verbose=False):
    if config_file:
        conf_var = utils.read_config_file(config_file, verbose)
        try:
            conf_var = conf_var['pagerduty']
        except KeyError as e:
            lgr.error('Pagerduty error: '
                      'can\'t run pagerduty - no "{0}" '
                      'in config file.'.format(e.message))
            sys.exit(1)
        try:
            pagerduty.trigger(results_file_path=log,
                              api_key=conf_var['api_key'],
                              service_key=conf_var['service_key'])
        except KeyError as e:
            lgr.error('Pagerduty error: can\'t run pagerduty - "{0}" '
                      'argument is missing.'.format(e.message))
            sys.exit(1)
        except TypeError as e:
            lgr.error('Pagerduty error: '
                      'can\'t run pagerduty - {0}.'.format(e.message))
            sys.exit(1)
    else:
        lgr.error('Pagerduty error: Config file is missing.')
        sys.exit(1)


def count_dicts_in_results_file(file_path):
    i = 0
    try:
        with open(file_path, 'r') as results_file:
            results = json.load(results_file)
        for key, value in results.items():
            for k, v in value.items():
                i += 1
    except:
        pass
    return i


def check_plugins(config_file=None, source=None):
    if source and config_file:
        pass
    else:
        lgr.error("Used a config file when you want to use '--source'.")
        sys.exit(1)


def show_result(log=None):
        with open(log, 'r') as results_file:
            results = results_file.read()
        lgr.info(results)


def convert_to_lowercase_list(list):
    lowercase_list = []
    for value in list:
        value = value.encode('ascii')
        lowercase_list.append(value.lower())
    return lowercase_list
