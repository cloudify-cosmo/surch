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
  --help  Show this message and exit.

Commands:
  org   Search all or some repositories in an...
  repo  Search a single repository
  user  Search all or some repositories for a user

```

### Search in a single repository

```shell
$ surch repo http://github.com/cloudify-cosmo/surch --string Surch --string Burch
...

INFO - Cloning repo surch from org cloudify-cosmo to /home/nir0s/.surch/clones/cloudify-cosmo/surch...
INFO - Scanning repo `surch` for 2 string(s)...
INFO - Writing results to: /home/nir0s/.surch/results/cloudify-cosmo/results.json...
INFO - Found 110 results in 33 commits.
...

$ cat ~/.surch/results/cloudify-cosmo/results.json
...

{
    "_default": {
        "1": {
            "blob_url": "https://github.com/cloudify-cosmo/surch/blob/c4c72136c168514c0f17f8b03f0495eb8f5ee9fd/README.rst",
            "commit_sha": "c4c72136c168514c0f17f8b03f0495eb8f5ee9fd",
            "commit_time": "Thu May 19 17:49:30 2016",
            "email": "Havivv1305@gmail.com",
            "filepath": "README.rst",
            "organization_name": "cloudify-cosmo",
            "repository_name": "surch",
            "username": "haviv"
        },
        "2": {
            "blob_url": "https://github.com/cloudify-cosmo/surch/blob/c4c72136c168514c0f17f8b03f0495eb8f5ee9fd/surch/organization.py",
            "commit_sha": "c4c72136c168514c0f17f8b03f0495eb8f5ee9fd",
            "commit_time": "Thu May 19 17:49:30 2016",
            "email": "Havivv1305@gmail.com",
            "filepath": "surch/organization.py",
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
$ surch user havivw --string banana
...

INFO - Retrieving list of repositories for the organization...
INFO - Cloning repo cloudify-interactive-tutorial from org Havivw to /home/nir0s/.surch/clones/Havivw/cloudify-interactive-tutorial...
INFO - Scanning repo `cloudify-interactive-tutorial` for 1 string(s)...
INFO - Writing results to: /home/nir0s/.surch/results/Havivw/results.json...
INFO - Found 0 results in 45 commits.
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

