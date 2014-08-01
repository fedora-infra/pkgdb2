# -*- coding: utf-8 -*-
#
# Copyright © 2013-2014  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
#

'''
pkgdb default configuration.
'''

from datetime import timedelta

# Set the time after which the session expires
PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

# Root of the website url, so for example if you have it running at
#    http://project/pkgdb
# SITE_ROOT is http://project
# SITE_URL is http://project/pkgdb
SITE_ROOT = 'http://127.0.0.1:5000'
# Full URL to the website hosting the pkgdb2 instance. This is required
# to make the opensearch fully working.
SITE_URL = SITE_ROOT

# url to the database server:
DB_URL = 'sqlite:////var/tmp/pkgdb2_dev.sqlite'

# the number of items to display on the search pages
ITEMS_PER_PAGE = 50

# secret key used to generate unique csrf token
SECRET_KEY = '<insert here your own key>'

# List the ACL which are auto-approved (don't need reviewing)
AUTO_APPROVE = ['watchcommits', 'watchbugzilla']

# FAS group for the pkgdb admin
ADMIN_GROUP = ['sysadmin-main', 'sysadmin-cvs']

# The default backend for dogpile
# Options are listed at:
# http://dogpilecache.readthedocs.org/en/latest/api.html  (backend section)
#PKGDB2_CACHE_BACKEND = 'dogpile.cache.memory'
PKGDB2_CACHE_BACKEND = 'dogpile.cache.memcached'
PKGDB2_CACHE_KWARGS = {
    'arguments': {
        'url': "127.0.0.1:11211",
    }
}

# Bugzilla information
PKGDB2_BUGZILLA_IN_TESTS = False
PKGDB2_BUGZILLA_NOTIFICATION = False
PKGDB2_BUGZILLA_URL = 'https://bugzilla.redhat.com'
PKGDB2_BUGZILLA_USER = None
PKGDB2_BUGZILLA_PASSWORD = None

# Settings specific to the ``pkgdb-sync-bugzilla`` script/cron
PKGDB2_BUGZILLA_NOTIFY_EMAIL = [
    'toshio@fedoraproject.org',
    'kevin@fedoraproject.org',
    'pingou@fedoraproject']
BUGZILLA_COMPONENT_API = "component.get"

# FAS information
PKGDB2_FAS_URL = None
PKGDB2_FAS_USER = None
PKGDB2_FAS_PASSWORD = None
PKGDB2_FAS_INSECURE = False

# pkgdb notifications
PKGDB2_FEDMSG_NOTIFICATION = True
PKGDB2_EMAIL_NOTIFICATION = False
PKGDB2_EMAIL_TO = '{pkg_name}-owner@fedoraproject.org'
PKGDB2_EMAIL_FROM = 'nobody@fedoraproject.org'
PKGDB2_EMAIL_SMTP_SERVER = 'localhost'
PKGDB2_EMAIL_CC = None

MAIL_ADMIN = 'pingou@pingoured.fr'

# List the packages that are not accessible to the provenpackager group
PKGS_NOT_PROVENPACKAGER = ['firefox', 'thunderbird', 'xulrunner']
