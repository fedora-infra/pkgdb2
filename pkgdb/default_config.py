# -*- coding: utf-8 -*-
#
# Copyright © 2013  Red Hat, Inc.
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


# url to the database server:
DB_URL = 'sqlite:////var/tmp/packagedb2.sqlite'

# the number of items to display on the search pages
ITEMS_PER_PAGE = 50

# secret key used to generate unique csrf token
SECRET_KEY = '<insert here your own key>'

# List the ACL which are auto-approved (don't need reviewing)
AUTO_APPROVE = ['watchcommits', 'watchbugzilla']

# FAS group for the pkgdb admin
ADMIN_GROUP = ('sysadmin-main', 'sysadmin-cvs')

# The default backend for dogpile
# Options are listed at:
# http://dogpilecache.readthedocs.org/en/latest/api.html  (backend section)
PKGDB_CACHE_BACKEND = 'dogpile.cache.memory'


# Bugzilla information
PKGDB_BUGZILLA_IN_TESTS = False
PKGDB_BUGZILLA_NOTIFICATION = False
PKGDB_BUGZILLA_URL = 'https://bugzilla.redhat.com'
PKGDB_BUGZILLA_USER = None
PKGDB_BUGZILLA_PASSWORD = None

# FAS information
PKGDB_FAS_URL = None
PKGDB_FAS_USER = None
PKGDB_FAS_PASSWORD = None
