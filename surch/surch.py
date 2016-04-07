import os
import time
import subprocess

import yaml
import requests

GET_GIT_REPO_DETAILS_API_URL = 'https://api.github.com/orgs/{0}/repos?per_page={1}'
GIT_PULL_COMMAND = 'git -C {0} pull'
GIT_CLONE_COMMAND = 'git clone --quiet {0} {1}'
BLOB_URL_TEMPLATE = 'https://github.com/{0}/{1}/blob/{2}/{3}'
GIT_GREP_COMMAND = 'git -C {0} grep -l -e {1} {2}'
GET_COMMITS_COMMAND = 'git -C {0} rev-list --all'

class Surch():
    def define_var_from_config_file(self, config_file):
        with open(config_file, 'r') as config:
            conf_vars = yaml.load(config.read())
        self.search_list = conf_vars.get('search_list')
        self.ignore_repo = conf_vars.get('skipped_repo')
        self.organization = conf_vars.get('organization')
        self.git_cred = conf_vars.get('git_user') + ':' + conf_vars.get('git_password')
        self.git_user = conf_vars.get('git_user')
        self.git_password = conf_vars.get('git_password')
        self.local_path = conf_vars.get('local_path')

    def get_github_repo_list(self, user, password, organization, repo_per_page=100000):
        ''' api request for git url to clone'''
        github_repo_urls = []
        data = requests.get(GET_GIT_REPO_DETAILS_API_URL.format(organization, repo_per_page), auth=(user, password))
        data = data.json()
        for repo_data in data:
            github_repo_urls.append(repo_data['clone_url'])
        return github_repo_urls

    def clone_repo(self, github_repo_urls, path):
        ''' clone or pull git repos'''
        start = time.time()
        for url in github_repo_urls:
            name_git = url.rsplit('/', 1)[-1]
            full_path = os.path.join(path, name_git.rsplit('.', 1)[0])
            if os.path.exists(full_path):
                print 'pull request (update) {0} repo. from {1} org/user.'.format(name_git, self.organization)
                git_pull = subprocess.check_output(GIT_PULL_COMMAND.format(full_path), shell=True)
            else:
                print 'clone {0} repo. from {1} org/user.'.format(name_git, self.organization)
                git_clone = subprocess.check_output(GIT_CLONE_COMMAND.format(str(url), full_path), shell=True)
        print 'git_clone\pull time: ' + print_performance(start, time.time()) + ' seconds'

    def get_skipped_repo(self, ignore_list, path):
        ''' get repo list to ignore and create full path list to ignore '''
        ignore_list = ignore_list or []
        skipped_repo = []
        for repo in ignore_list:
            skipped_repo.append(os.path.join(path, repo))
        return skipped_repo

    def _create_search_strings(self, search_list):
        ''' create part of the grep command'''
        search_strings = 'rootkey.csv'
        for string in search_list:
            search_strings = "{0} --or -e '{1}'".format(search_strings, string)
        return search_strings

    def get_directory_list(self, path=os.getcwd(), skipped_list=None):
        ''' get list of the clone directory'''
        skipped_list = skipped_list or []
        repo_list = []
        full_path_list = []
        for item in os.listdir(path):
            full_path_list.append(os.path.join(path, item))
        all_repo = [d for d in full_path_list if os.path.isdir(d)]
        for repo in all_repo:
            if repo not in skipped_list:
                repo_list.append(repo)
        return repo_list

    def search_in_commits(self, ignore_repo, local_path, search_list):
        ''' save the blob url of problematic commits '''
        start = time.time()
        skipped_repo = self.get_skipped_repo(ignore_repo, local_path)
        directories = self.get_directory_list(local_path, skipped_list=skipped_repo)
        string_to_search = self._create_search_strings(search_list)
        with open('bad_comm', 'w') as db:
            db.writelines(self.find_problematic_commits(directories, string_to_search))
        print 'search_in_commit time: ' + print_performance(start, time.time()) + ' seconds'

    def find_problematic_commits(self, directories, string_to_search):
        ''' search secret string in the commits file and save the blob_url of the bad files '''
        urls_blob = []
        for directory in directories:
            print directory
            repo_name = directory.split('/', -1)[-1]
            urls_blob += self.find_problematic_commits_in_directory(directory, string_to_search, repo_name,
                                                                    self.organization)
        return urls_blob

    def get_all_commits_list(self, directory):
        ''' get the sha(number) of the commit '''
        try:
            commits = subprocess.check_output(GET_COMMITS_COMMAND.format(directory), shell=True)
            return commits.splitlines()
        except subprocess.CalledProcessError:
            return []

    def get_url_blob(self, bad_commits, organization, repo_name):
        '''create the blob_url from sha:filename'''
        blob_url = []
        url_blob = []
        for file in bad_commits:
            if file:
                blob_url = file.splitlines()
        for item in blob_url:
            if item:
                try:
                    sha = item.rsplit(':', 1)[0]
                    file_name = item.rsplit(':', 1)[1]
                    url_blob.append(BLOB_URL_TEMPLATE.format(organization, repo_name, sha, file_name))
                except IndexError:
                    '''the structre of the output is
                       sha:filename
                       sha:filename
                       sha:filename
                       filename
                       filename
                       None
                       and we need both sha and filename and when we dont get them we need it pass'''
                    pass
        return url_blob

    def get_bad_files(self, directory, commit, string_to_search):
        '''run git grep'''
        try:
            bad_files = subprocess.check_output(GIT_GREP_COMMAND.format(directory, string_to_search, commit), shell=True)
            print 'success read commit {0}:{1}'.format(directory, commit)
            return bad_files.splitlines()
        except subprocess.CalledProcessError :
            print 'Can\'t read this commit {0}:{1}'.format(directory, commit)
            return ()


    def find_problematic_commits_in_directory(self, directory, string_to_search, repo_name, organization):
        '''create list of all problematic commits'''
        bad_files = []
        for commit in self.get_all_commits_list(directory):
            bad_files += self.get_bad_files(directory, commit, string_to_search)
        return self.get_url_blob(bad_files, organization, repo_name)

    def __main__(self):
        start = time.time()
        self.define_var_from_config_file('/home/haviv/ops/surch-config.yaml')
        clone_urls = self.get_github_repo_list(self.git_user, self.git_password, self.organization)
        self.clone_repo(clone_urls, self.local_path)

        self.search_in_commits(self.ignore_repo, self.local_path, self.search_list)
        print 'total time: ' + print_performance(start, time.time()) + ' seconds'



def print_performance(start, end):
    ''' calculate the runnig time'''
    return str(round(end - start, 3))

a = Surch()
a.__main__()