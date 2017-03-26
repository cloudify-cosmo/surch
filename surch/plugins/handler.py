from .. import utils
from . import pagerduty, vault
from ..exceptions import SurchError


logger = utils.logger
KEY_LIST = ('.*password.*', '.*key.*', '.*secret.*', '.*id.*', '.*endpoint.*',
            '.*tenant.*', '.*api.*')


def plugins_handle(plugins_list, config_file):
    if plugins_list:
        lowercase_list = []
        for value in plugins_list:
            value = value.encode('ascii')
            lowercase_list.append(value.lower())
            if config_file:
                pass
            else:
                raise SurchError("Used a config file when you want to use "
                                 "'--source/--pager'.")
        return lowercase_list
    else:
        return ('')


def pagerduty_trigger(config_file=None, log=None):
    if config_file:
        conf_var = utils.read_config_file(config_file=config_file)
        try:
            conf_var = conf_var['pagerduty']
        except KeyError as e:
            raise SurchError('Pagerduty error: can\'t run pagerduty - '
                             'no "{0}" in config file.'.format(e.message))
        try:
            pagerduty.trigger(results_file_path=log,
                              api_key=conf_var['api_key'],
                              service_key=conf_var['service_key'])
        except KeyError as e:
            raise SurchError('Pagerduty error: can\'t run pagerduty - "{0}" '
                             'argument is missing.'.format(e.message))
        except TypeError as e:
            raise SurchError('Pagerduty error: can\'t run '
                             'pagerduty - {0}.'.format(e.message))
    else:
        raise SurchError('Pagerduty error: Config file is missing.')


def vault_trigger(config_file=None):
    if config_file:
        conf_var = utils.read_config_file(config_file)
        try:
            conf_var = conf_var['vault']
        except KeyError as e:
            logger.error('Vault error: can\'t run vault - no "{0}" '
                         'in config file.'.format(e.message))
        try:
            key_list = conf_var['key_list']
        except KeyError:
            key_list = KEY_LIST
        try:
            return vault.get_search_list(vault_url=conf_var['vault_url'],
                                         vault_token=conf_var['vault_token'],
                                         secret_path=conf_var['secret_path'],
                                         key_list=key_list)
        except KeyError as e:
            raise SurchError('Vault error: can\'t run vault - "{0}" '
                             'argument is missing.'.format(e.message))
        except TypeError as e:
            logger.error('Vault error: can\'t run vault - '
                         '{0}.'.format(e.message))
    else:
        raise SurchError('Vault error: Config file is missing.')


def merge_all_search_list(source, config_file, search_list):
    if config_file:
        conf_vars = utils.read_config_file(config_file=config_file)
        search_list = utils.merge_to_list(
            search_list, conf_vars['search_list'])
    if 'vault' in source and config_file:
        vault_list = vault_trigger(config_file=config_file)
        search_list = utils.merge_to_list(vault_list, search_list)
    return search_list
