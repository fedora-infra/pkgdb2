# -*- coding: utf-8 -*-

"""
Simple script used to import the monitoring status of packages from the wiki
page: http://fedoraproject.org/wiki/Upstream_release_monitoring
into pkgdb: https://admin.fedoraproject.org/pkgdb/


Part of this code is taken from cnucnu which has been written by Till Maas
https://fedorapeople.org/cgit/till/public_git/cnucnu.git/

"""

import argparse
import fnmatch
import logging
import re
import string
import subprocess

import fedora.client
import pkgdb2client

PKGDBLOG = logging.getLogger("pkgdb2client")


class MediaWiki(fedora.client.Wiki):
    def __init__(self, base_url='https://fedoraproject.org/w/', *args, **kw):
        super(MediaWiki, self).__init__(base_url, *args, **kw)

    def json_request(self, method="api.php", req_params=None, auth=False, **kwargs):
        if req_params:
            req_params["format"] = "json"

        data =  self.send_request(method, req_params, auth, **kwargs)

        if 'error' in data:
            raise Exception(data['error']['info'])
        return data

    def get_pagesource(self, titles):
        data = self.json_request(req_params={
                'action' : 'query',
                'titles' : titles,
                'prop'   : 'revisions',
                'rvprop' : 'content'
                }
                )
        return data['query']['pages'].popitem()[1]['revisions'][0]['*']


class Repository:
    def __init__(self):
        self.name = 'Fedora Rawhide'
        self.path = 'http://kojipkgs.fedoraproject.org/mash/rawhide/source/SRPMS'
        self.repoid = "cnucnu-%s" % "".join(
            c for c in self.name if c in string.letters)

        self.repofrompath = "%s,%s" % (self.repoid, self.path)

        self._nvr_dict = None

    @property
    def nvr_dict(self):
        if not self._nvr_dict:
            self._nvr_dict = self.repoquery()
        return self._nvr_dict

    def repoquery(self, package_names=[]):
        # TODO: get rid of repofrompath message even with --quiet
        cmdline = ["/usr/bin/repoquery",
                   "--quiet",
                   "--archlist=src",
                   "--all",
                   "--repoid",
                   self.repoid,
                   "--qf",
                   "%{name}\t%{version}\t%{release}"]
        if self.repofrompath:
            cmdline.extend(['--repofrompath', self.repofrompath])
        cmdline.extend(package_names)

        repoquery = subprocess.Popen(cmdline, stdout=subprocess.PIPE)
        (list_, stderr) = repoquery.communicate()
        new_nvr_dict = {}
        for line in list_.split("\n"):
            if line != "":
                name, version, release = line.split("\t")
                new_nvr_dict[name] = (version, release)
        return new_nvr_dict


def match_interval(text, regex, begin_marker, end_marker):
    """ returns a list of match.groups() for all lines after a line
    like begin_marker and before a line like end_marker
    """

    inside = False
    for line in text.splitlines():
        if not inside:
            if line == begin_marker:
                inside = True
        else:
            match = regex.match(line)
            if match:
                yield match.groups()
            elif line == end_marker:
                inside = False
                break


def get_packages():
    ''' Retrieve the list of packages that have been marked as 'to monitor'
    in the wiki.
    '''
    print 'Building rawhide repo info'
    repo = Repository()

    print 'Retrieving package list from the wiki'
    mediawiki = {
        'base url': 'https://fedoraproject.org/w/',
        'page': 'Upstream_release_monitoring'
    }

    w = MediaWiki(base_url=mediawiki["base url"])
    page_text = w.get_pagesource(mediawiki["page"])

    ignore_owner_regex = re.compile('\\* ([^ ]*)')

    packages = []
    package_line_regex = re.compile(
        '^\s+\\*\s+(\S+)\s+(.+?)\s+(\S+)\s*$')
    for package_data in match_interval(
        page_text, package_line_regex,
            "== List Of Packages ==", "<!-- END LIST OF PACKAGES -->"):
        (name, regex, url) = package_data
        # fnmatch.filter() is very slow, therefore check first if any
        # wildcard chars exist
        if "*" in name or "?" in name or "[" in name:
            matched_names = fnmatch.filter(repo.nvr_dict.keys(), name)
            if len(matched_names) == 0:
                # Add non-matching name to trigger an error/warning
                # later FIXME: Properly report bad names
                matched_names = [name]
        else:
            matched_names = [name]
        for name in matched_names:
            packages.append(name)

    print '%s packages retrieved in the wiki' % len(packages)
    return packages


def get_args():
    ''' Set and return the command line arguments. '''
    parser = argparse.ArgumentParser(
        description='Script syncing monitoring flag status from the wiki to'
        ' pkgdb.'
    )
    parser.add_argument(
        '--url',
        default='https://admin.stg.fedoraproject.org/pkgdb',
        help='URL of the pkgdb instance to use, defaults to: '
        'https://admin.stg.fedoraproject.org/pkgdb'
    )
    parser.add_argument(
        '--prod', default=False, action='store_true',
        help='If set, changes the URL used to '
        'https://admin.fedoraproject.org/pkgdb'
    )

    return parser.parse_args()


def main():
    ''' Retrieve the list of packages to monitor and set the monitoring
    flag in pkgdb
    '''
    args = get_args()

    pkgs = get_packages()

    url = arg.url
    if args.prod:
        url = 'https://admin.fedoraproject.org/pkgdb'

    pkgdbclient = pkgdb2client.PkgDB(
        url,
        insecure=True,
        login_callback=pkgdb2client.ask_password
    )

    for pkg in pkgs:
        args = {
            'pkgnames': pkg,
        }
        try:
            pkgdbclient.handle_api_call(
                '/package/%s/monitor/1' % pkg, data=args
            )
        except pkgdb2client.PkgDBException as err:
            print pkg, err


if __name__ == '__main__':
    PKGDBLOG.setLevel(logging.DEBUG)
    main()
