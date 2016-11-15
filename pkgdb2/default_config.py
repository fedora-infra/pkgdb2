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

# Name used to reference ourselves
PROJECT_NAME = 'Fedora'

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

### Blacklisted items
REQUEST_BLACKLIST = []

# List of FAS user that can be automatically approved w/o checking if they
# are packagers
AUTOAPPROVE_PKGERS = []

# FAS group for the pkgdb admin
ADMIN_GROUP = ['sysadmin-main', 'sysadmin-cvs']

# The default backend for dogpile
# Options are listed at:
# https://dogpilecache.readthedocs.org/en/latest/api.html  (backend section)
#PKGDB2_CACHE_BACKEND = 'dogpile.cache.memory'
PKGDB2_CACHE_BACKEND = 'dogpile.cache.memcached'
PKGDB2_CACHE_KWARGS = {
    'arguments': {
        'url': "127.0.0.1:11211",
    }
}

# Information regarding where the application is deployed
SITE_ROOT = 'https://admin.fedoraproject.org'
SITE_URL = '%s/pkgdb' % SITE_ROOT

# Bugzilla information
PKGDB2_BUGZILLA_IN_TESTS = False
PKGDB2_BUGZILLA_NOTIFICATION = False
PKGDB2_BUGZILLA_URL = 'https://bugzilla.redhat.com'
PKGDB2_BUGZILLA_USER = None
PKGDB2_BUGZILLA_PASSWORD = None

# Settings specific to the ``pkgdb-sync-bugzilla`` script/cron
PKGDB2_BUGZILLA_NOTIFY_EMAIL = [
    'kevin@fedoraproject.org',
    'pingou@fedoraproject']
BUGZILLA_COMPONENT_API = "component.get"
PKGDB2_BUGZILLA_NOTIFY_USER = None
PKGDB2_BUGZILLA_NOTIFY_PASSWORD = None
PKGDB2_BUGZILLA_DRY_RUN = False

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

# Make browsers send session cookie only via HTTPS
# False by default so that pkgdb2 works out of the box, you will want to set it
# to True in production
SESSION_COOKIE_SECURE = False

# Set a default application root to prevent any potential cookie conflict if
# pgkdb is not deployed at the root of the server
APPLICATION_ROOT = '/'

# Setting for the update_package_info script
REPO_MAP = [
    ('rawhide', 'fedora/linux/development/rawhide/source'),
    ('f23_up', 'fedora/linux/updates/23'),
    ('f22_up', 'fedora/linux/updates/21'),
    ('f22_rel', 'fedora/linux/releases/22/Everything/source'),
    ('f21_up', 'fedora/linux/updates/21'),
    ('f21_rel', 'fedora/linux/releases/21/Everything/source'),
    ('el7', 'epel/7'),
    ('el6', 'epel/6'),
    ('el5', 'epel/5'),
]

BASE_REPO_URL = 'https://dl.fedoraproject.org/pub/%s/SRPMS/'

# Anitya settings
PKGDB2_ANITYA_DISTRO='Fedora'
PKGDB2_ANITYA_URL='https://release-monitoring.org'


# PkgDB sync bugzilla email
PKGDB_SYNC_BUGZILLA_EMAIL = """Greetings.

You are receiving this email because there's a problem with your
bugzilla.redhat.com account.

If you recently changed the email address associated with your
Fedora account in the Fedora Account System, it is now out of sync
with your bugzilla.redhat.com account. This leads to problems
with Fedora packages you own or are CC'ed on bug reports for.

Please take one of the following actions:

a) login to your old bugzilla.redhat.com account and change the email
address to match your current email in the Fedora account system.
https://bugzilla.redhat.com login, click preferences, account
information and enter new email address.

b) Create a new account in bugzilla.redhat.com to match your
email listed in your Fedora account system account.
https://bugzilla.redhat.com/ click 'new account' and enter email
address.

c) Change your Fedora Account System email to match your existing
bugzilla.redhat.com account.
https://admin.fedoraproject.org/accounts login, click on 'my account',
then 'edit' and change your email address.

If you have questions or concerns, please let us know.

Your prompt attention in this matter is appreciated.

The Fedora admins.
"""

# If a namespace appears in this list, then you can only request packages for
# it from the list of mandated branches here. If the namespace doesn't appear
# here, then you can request any branches that you like.
# https://github.com/fedora-infra/pkgdb2/issues/341
PKGDB2_NAMESPACE_POLICY = {
    "modules": [
        "master",
    ],
}

# URLs used in the package's info page
# Watch for the `%s` in the URL it is mandatory and in each of these, it
# will be replaced by the package's name
PKGS_BUG_URL = 'https://apps.fedoraproject.org/packages/%s/bugs'
PKGS_PKG_URL = 'https://apps.fedoraproject.org/packages/%s'
CGIT_URL = 'http://pkgs.fedoraproject.org/cgit/%s/%s.git/'
BODHI_URL = 'https://bodhi.fedoraproject.org/updates/?packages=%s'
KOJI_URL = 'http://koji.fedoraproject.org/koji/search?'\
    'type=package&match=glob&terms=%s'
KOSCHEI_URL = 'https://apps.fedoraproject.org/koschei/package/%s'
