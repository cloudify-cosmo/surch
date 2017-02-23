# Surch

[![Build Status](https://travis-ci.org/cloudify-cosmo/surch.svg?branch=master)](https://travis-ci.org/cloudify-cosmo/surch)
[![Build status](https://ci.appveyor.com/api/projects/status/xf1hp1bekf3qhtr8/branch/master?svg=true)](https://ci.appveyor.com/project/Cloudify/surch/branch/master)
[![PyPI](http://img.shields.io/pypi/dm/surch.svg)](http://img.shields.io/pypi/dm/surch.svg)
[![PypI](http://img.shields.io/pypi/v/surch.svg)](http://img.shields.io/pypi/v/surch.svg)

Surch searches GitHub organizations, a list of user repositories or single repositories for strings

Surch iterates through a single GitHub repository or a whole GitHub organization for different strings based on user input. Provided a repository, all commits and branches will be searched in.

The output is a file containing the blob url and additional information in which one of the strings was found.

The initial idea behind Surch was to look for secrets but it can be used to search for just about anything.

While [Gitrob](https://github.com/michenriksen/gitrob) provides mostly the same functionality (plus a whole plethora of additional features), we wanted something that would be lightweight and won't require a PostgreSQL server and other dependencies behind it. To that end, Surch requires no dependencies whatsoever aside from Python.

It's important to note that currently, Surch does not tell you what it found where. It simply tells you that it found one of the strings you searched for and in which commit it was found.

NOTE: For now we support in python 2.7 in the future we plain to support python 3


## Installation

```shell
pip install surch

# latest development version
pip install http://github.com/cloudify-cosmo/surch/archive/master.tar.gz
```


## Usage

```shell
$ surch --help

Usage: surch [OPTIONS] COMMAND [ARGS]...

Options:
  -h, --help  Show this message and exit.

Commands:
  members  Search all or some members in an organization
  org      Search all or some repositories in an...
  repo     Search a single repository.
  user     Search all or some repositories in an...


```

### Search in a single repository

```shell
$ surch repo http://github.com/cloudify-cosmo/surch --string Surch --string Burch
...

2016-07-14 08:41:57,769 - surch - INFO - Pulling repo: surch...
2016-07-14 08:41:58,540 - surch - INFO - Scanning repo surch for 2 string(s)...
2016-07-14 08:41:59,579 - surch - INFO - Writing results to: ~/.surch/results/results.db...
2016-07-14 08:42:13,008 - surch - INFO - Found 0 files with your strings.

...

$ cat ~/.surch/results/results.json
...

{
    "_default": {
        "1": {
            "blob_url": "https://github.com/cloudify-cosmo/surch/blob/72b389d6a9a393174a514a1cdb20d288deac7024/README.md",
            "branches_names": [
                "error-handling",
                "master",
                "plugins_tests"
            ],
            "commit_sha": "72b389d6a9a393174a514a1cdb20d288deac7024",
            "commit_time": "Thu Jul 14 08:55:40 2016",
            "email": "Havivv1305@gmail.com",
            "filepath": "README.md",
            "organization_name": "cloudify-cosmo",
            "repository_name": "surch",
            "username": "haviv"
        },
        "2": {
            "blob_url": "https://github.com/cloudify-cosmo/surch/blob/21444d12ec84fafd63796e14f51900da5c4bedd7/README.md",
            "branches_names": [
                "error-handling"
            ],
            "commit_sha": "21444d12ec84fafd63796e14f51900da5c4bedd7",
            "commit_time": "Tue Feb 21 13:01:15 2017",
            "email": "Havivv1305@gmail.com",
            "filepath": "README.md",
            "organization_name": "cloudify-cosmo",
            "repository_name": "surch",
            "username": "haviv"
        },

        ...
    }
}
```

### Search an entire organization or user repositories

NOTE: to search in an organization, replace `user` with `org`

```shell
$ surch user havivw --string surch
...

2016-07-14 08:47:16,294 - surch - WARNING - Choosing not to provide GitHub credentials limits requests to GitHub to 60/h. This might affect cloning.
2016-07-14 08:47:16,294 - surch - INFO - Retrieving repository information for this user:havivw...
2016-07-14 08:47:17,727 - surch - INFO - Previous results file found. Backing up to ~/.surch/results/results.json.20160714T084717
2016-07-14 08:47:17,729 - surch - INFO - Cloning repo cloudify-interactive-tutorial from org Havivw to ~/.surch/clones/cloudify-interactive-tutorial...
2016-07-14 08:47:22,677 - surch - INFO - Scanning repo cloudify-interactive-tutorial for 1 string(s)...
2016-07-14 08:47:23,215 - surch - INFO - Writing results to: ~/.surch/results/results.db...
2016-07-14 08:47:23,215 - surch - INFO - Found 0 files with your strings.
...

```

### Search an entire organization members repositories

NOTE: to search in all members an organization

```shell
$ surch members cloudify-cosmo -U <username> -P <password> --string surch
...

2017-02-23 20:45:40,015 - Surch - INFO - Get members list from organization cloudify-cosmo...
2017-02-23 20:45:42,499 - Surch - INFO - Retrieving repository information for this user: Havivw...
2017-02-23 20:45:44,078 - Surch - INFO - Cloning repo cloudify-interactive-tutorial from org/user Havivw to ~/.surch/clones/cloudify-cosmo/Havivw/cloudify-interactive-tutorial...
2017-02-23 20:45:48,721 - Surch - INFO - Found 45 commits in cloudify-interactive-tutorial...
2017-02-23 20:45:48,721 - Surch - INFO - Scanning repo cloudify-interactive-tutorial for 1 string(s)...
2017-02-23 20:45:49,282 - Surch - INFO - Writing results to: /home/haviv/.surch/results/results.db...
2017-02-23 20:45:49,282 - Surch - INFO - Found 0 files with your strings...

...

```

## Additional Info

* Cloned repositories are stored under ~/.surch/clones
* Result files are stored under ~/.surch/results

## Testing

NOTE: Running the tests require an internet connection

```shell
git clone git@github.com:cloudify-cosmo/surch.git
cd surch
pip install tox
tox
```

## Contributions..

..are always welcome.

