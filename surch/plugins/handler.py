import sys

from .. import utils
from . import pagerduty


logger = utils.logger


def plugins_handle(plugins_list, config_file):
    if plugins_list:
        lowercase_list = []
        for value in plugins_list:
            value = value.encode('ascii')
            lowercase_list.append(value.lower())
            if config_file:
                pass
            else:
                logger.error("Used a config file when you "
                             "want to use '--source/--pager'.")
                sys.exit(1)
        return lowercase_list
    else:
        return ('')


def pagerduty_trigger(config_file=None, log=None):
    if config_file:
        conf_var = utils.read_config_file(config_file=config_file)
        try:
            conf_var = conf_var['pagerduty']
        except KeyError as e:
            logger.error('Pagerduty error: '
                         'can\'t run pagerduty - no "{0}" '
                         'in config file.'.format(e.message))
            sys.exit(1)
        try:
            pagerduty.trigger(results_file_path=log,
                              api_key=conf_var['api_key'],
                              service_key=conf_var['service_key'])
        except KeyError as e:
            logger.error('Pagerduty error: can\'t run pagerduty - "{0}" '
                         'argument is missing.'.format(e.message))
            sys.exit(1)
        except TypeError as e:
            logger.error('Pagerduty error: '
                         'can\'t run pagerduty - {0}.'.format(e.message))
            sys.exit(1)
    else:
        logger.error('Pagerduty error: Config file is missing.')
        sys.exit(1)
