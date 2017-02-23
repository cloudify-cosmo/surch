import os
import requests

from .exceptions import SurchError
from . import organization, utils, constants


def _get_user_include_list(all_users, users_to_include=None,
                           users_to_exclude=None):
    """ Get include or exclude users list, return users list to search on"""
    if users_to_exclude and users_to_include:
        raise SurchError('You must supply at least one string to search for.')
    users_url_list = []
    if users_to_include:
        for user in users_to_include:
            for user_name in all_users:
                if user_name == user:
                    users_url_list.append(user_name)

    elif users_to_exclude:
        for user_name in all_users:
            if user_name not in users_to_exclude:
                users_url_list.append(user_name)
    else:
        for user_name in all_users:
            users_url_list.append(user_name)
    return users_url_list


def get_members_list_by_page(user, password, organization_name, page):
    get_data = requests.get(constants.GET_GIT_ORGANIZATION_MEMBERS.format(
        organization_name, page), auth=(user, password))
    all_data = get_data.json()
    return all_data


def get_members_list(user, password, organization_name, logger=utils.logger):
    logger.info('Get members list from organization {0}...'.format(organization_name))
    members_list = []
    page = 0
    all_data = get_members_list_by_page(user, password, organization_name, page)
    while len(all_data) != 0:
        for member in all_data:
            members_list.append(member['login'].encode('ascii'))
        page += 1
        all_data = get_members_list_by_page(user, password,
                                            organization_name, page)
    return list(set(members_list))


def check_user_list(users_to_check, members_list):
    not_exists = []
    for user in users_to_check:
        if user not in members_list:
            not_exists.append(user.encode('ascii'))
    return not_exists


def search(git_user, git_password, organization_name, search_list,
           results_file_path=None, cloned_repos_dir=None,
           users_to_skip=None, users_to_check=None, consolidate_log=False,
           remove_clones_dir=False, verbose=False):
    logger = utils.set_logger(verbose)
    utils.handle_results_file(results_file_path, consolidate_log)
    cloned_repos_dir = cloned_repos_dir or os.path.join(
        constants.CLONED_REPOS_PATH, organization_name)
    all_members = get_members_list(git_user, git_password,
                                   organization_name, logger)
    members_list = _get_user_include_list(all_members, users_to_check,
                                          users_to_skip)
    not_exists_users = check_user_list(users_to_check, members_list)
    if not_exists_users:
        logger.info('The following users "{0}" do not exist in the '
                    'organization {1}... '
                    '(check if username is case sensitive)...'.format(
            not_exists_users, organization_name))

    for member in members_list:
        organization.search(git_item_name=member,
                            git_user=git_user, git_password=git_password,
                            search_list=search_list, is_organization=False,
                            results_file_path=results_file_path,
                            cloned_repos_dir=cloned_repos_dir,
                            consolidate_log=True, remove_clones_dir=False,
                            verbose=verbose, from_members=True)
    utils._remove_repos_folder(cloned_repos_dir, remove_clones_dir)