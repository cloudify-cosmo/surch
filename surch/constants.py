import os

HOME_DIR = os.path.expanduser("~")
DEFAULT_PATH = os.path.join(HOME_DIR, '.surch')
CLONED_REPOS_PATH = os.path.join(DEFAULT_PATH, 'clones')
RESULTS_PATH = os.path.join(DEFAULT_PATH, 'results')

GITHUB_API_URL = 'https://api.github.com/{0}/{1}'
GITHUB_REPO_DETAILS_API_URL = \
    ''.join([GITHUB_API_URL, '/repos?type={2}&per_page={3}&page={4}'])

GITHUB_BLOB_URL = 'https://github.com/{0}/{1}/blob/{2}/{3}'
