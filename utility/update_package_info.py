#!/usr/bin/env python

"""
This script queries the summary and description information from
packages and update the pgkdb2 database with them.
"""

# These two lines are needed to run on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources
import os
import sys

PG_BAR = False
try:
    from progressbar import Bar, ETA, Percentage, ProgressBar, RotatingMarker
    PG_BAR = True
except ImportError:
    pass

if 'PKGDB2_CONFIG' not in os.environ \
        and os.path.exists('/etc/pkgdb2/pkgdb2.cfg'):
    print 'Using configuration file `/etc/pkgdb2/pkgdb2.cfg`'
    os.environ['PKGDB2_CONFIG'] = '/etc/pkgdb2/pkgdb2.cfg'


sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import pkgwat.api

import pkgdb2
import pkgdb2.lib


#
#https://fedorahosted.org/fedora-infrastructure/ticket/3792
#

class User(object):
    username = 'pkgdb_updater'
    cla_done = True
    groups = ['sysadmin-min']

count = 0
pbar = None
if PG_BAR:
    count = pkgdb2.lib.search_package(
        pkgdb2.SESSION, '*', status='Approved', count=True)
    widgets = ['ACLs: ', Percentage(), ' ', Bar(marker=RotatingMarker()),
               ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=count).start()

cnt = 0
updated = 0
for pkg in pkgdb2.lib.search_package(
        pkgdb2.SESSION, '*', status='Approved'):
    cnt += 1
    try:
        results = pkgwat.api.get(pkg.name)
    except KeyError:
        print 'No such package %s found on packages.' % pkg.name
        continue

    summary = results['summary']
    description = results['description']

    pkgdb2.lib.edit_package(
        session=pkgdb2.SESSION,
        package=pkg,
        pkg_summary=results.get('summary', None),
        pkg_description=results.get('description', None),
        pkg_upstream_url=results.get('upstream_url', None),
        user = User()
    )
    updated += 1
    if PG_BAR:
        pbar.update(cnt)
if PG_BAR:
    pbar.finish()

print '%s packages checked' % cnt
print '%s packages updated' % updated
