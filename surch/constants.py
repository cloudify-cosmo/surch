import os

DOT_SURCH = os.path.join(os.path.expanduser("~"), '.surch')
CLONED_REPOS_PATH = os.path.join(DOT_SURCH, 'clones')
RESULTS_PATH = os.path.join(DOT_SURCH, 'results.TinyDB')

GITHUB_API_URL = 'https://api.github.com/{0}/{1}'
GITHUB_REPO_DETAILS_API_URL = \
    ''.join([GITHUB_API_URL, '/repos?type={2}&per_page={3}&page={4}'])

GITHUB_BLOB_URL = 'https://github.com/{0}/{1}/blob/{2}/{3}'
