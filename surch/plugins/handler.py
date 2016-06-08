import sys

from .. import utils, logger
from . import slack


lgr = logger.init()


def plugins_handle(plugins_list, config_file):
    if plugins_list:
        lowercase_list = []
        for value in plugins_list:
            value = value.encode('ascii')
            lowercase_list.append(value.lower())
            if config_file:
                pass
            else:
                lgr.error("Used a config file when you "
                          "want to use '--source/--pager'.")
                sys.exit(1)
        return lowercase_list
    else:
        return ('')


def slack_trigger(config_file=None, log=None):
    if config_file:
        conf_var = utils.read_config_file(config_file=config_file)
        try:
            conf_var = conf_var['slack']
        except KeyError as e:
            lgr.error('Slack error: '
                      'can\'t run slack - no "{0}" '
                      'in config file.'.format(e.message))
            sys.exit(1)
        try:
            slack.trigger(
                results_file_path=log,
                channel=conf_var['channel'],
                incoming_webhooks_url=conf_var['incoming_webhooks_url'])

        except KeyError as e:
            lgr.error('Slack error: can\'t run slack - "{0}" '
                      'argument is missing.'.format(e.message))
            sys.exit(1)
        except TypeError as e:
            lgr.error('Slack error: '
                      'can\'t run slack - {0}.'.format(e.message))
            sys.exit(1)
    else:
        lgr.error('Slack error: Config file is missing.')
        sys.exit(1)