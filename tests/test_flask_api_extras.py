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
pkgdb tests for the Flask API regarding collections.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import json
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import pkgdb
from pkgdb.lib import model
from tests import (Modeltests, FakeFasUser, create_package_acl)


class FlaskApiExtrasTest(Modeltests):
    """ Flask API extras tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskApiExtrasTest, self).setUp()

        pkgdb.APP.config['TESTING'] = True
        pkgdb.SESSION = self.session
        pkgdb.api.extras.SESSION = self.session
        self.app = pkgdb.APP.test_client()

        # Let's make sure the cache is empty for the tests
        pkgdb.cache.invalidate()

    def test_api_bugzilla_empty(self):
        """ Test the api_bugzilla function with an empty database. """

        # Empty DB
        output = self.app.get('/api/bugzilla/')
        self.assertEqual(output.status_code, 200)

        expected = """# Package Database VCS Acls
# Text Format
# Collection|Package|Description|Owner|Initial QA|Initial CCList
# Backslashes (\) are escaped as \u005c Pipes (|) are escaped as \u007c

"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/bugzilla/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        expected = {
            u'bugzillaAcls': {},
            u'title': u'Fedora Package Database -- Bugzilla ACLs'
        }

        self.assertEqual(data, expected)

    def test_api_bugzilla_filled(self):
        """ Test the api_bugzilla function with a filled database. """
        # Fill the DB
        create_package_acl(self.session)

        output = self.app.get('/api/bugzilla/')
        self.assertEqual(output.status_code, 200)

        expected = """# Package Database VCS Acls
# Text Format
# Collection|Package|Description|Owner|Initial QA|Initial CCList
# Backslashes (\) are escaped as \u005c Pipes (|) are escaped as \u007c

Fedora|guake|Top down terminal for GNOME|pingou|toshio
Fedora|fedocal|A web-based calendar for Fedora|orphan|
Fedora|geany|A fast and lightweight IDE using GTK2|group::gtk-sig|"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/bugzilla/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        expected = {
            u'bugzillaAcls': {
                u'Fedora': [
                    {u'guake': {
                        u'owner': u'pingou',
                        u'cclist': {
                            u'groups': [],
                            u'people': [u'toshio']
                        },
                        u'qacontact': None,
                        u'summary': u'Top down terminal for GNOME'
                        }
                    },
                    {u'fedocal': {
                        u'owner': u'orphan',
                        u'cclist': {
                            u'groups': [],
                            u'people': []
                        },
                        u'qacontact': None,
                        u'summary': u'A web-based calendar for Fedora'
                        }
                    },
                    {u'geany': {
                        u'owner': u'group::gtk-sig',
                        u'cclist': {
                            u'groups': [],
                            u'people': []
                        },
                        u'qacontact': None,
                        u'summary': u'A fast and lightweight IDE using GTK2'
                        }
                    }
                ]
            },
            u'title': u'Fedora Package Database -- Bugzilla ACLs'
        }

        self.assertEqual(data, expected)

    def test_api_notify_empty(self):
        """ Test the api_notify function with an empty database. """

        # Empty DB
        output = self.app.get('/api/notify/')
        self.assertEqual(output.status_code, 200)

        expected = ""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/notify/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        expected = {
            u'packages': [],
            u'title': u'Fedora Package Database -- Notification List',
            u'name': None,
            u'version': None,
            u'eol': False
        }

        self.assertEqual(data, expected)

    def test_api_notify_filled(self):
        """ Test the api_notify function with a filled database. """
        # Filled DB
        create_package_acl(self.session)

        output = self.app.get('/api/notify/')
        self.assertEqual(output.status_code, 200)

        expected = """guake|pingou,toshio
geany|group::gtk-sig"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/notify/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            u'title': u'Fedora Package Database -- Notification List',
            u'packages': [
                {u'guake': [u'pingou', u'toshio']},
                {u'geany': [u'group::gtk-sig']}
            ],
            u'name': None,
            u'version': None,
            u'eol': False
        }
        self.assertEqual(data, expected)

    def test_api_vcs_empty(self):
        """ Test the api_vcs function with an empty database. """

        # Empty DB
        output = self.app.get('/api/vcs/')
        self.assertEqual(output.status_code, 200)

        expected = """# VCS ACLs
# avail|@groups,users|rpms/Package/branch

"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/vcs/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        expected = {
            u'packageAcls': {},
            u'title': u'Fedora Package Database -- VCS ACLs'
        }

        self.assertEqual(data, expected)

    def test_api_vcs_filled(self):
        """ Test the api_vcs function with a filled database. """
        # Filled DB
        create_package_acl(self.session)

        output = self.app.get('/api/vcs/')
        self.assertEqual(output.status_code, 200)

        expected = """# VCS ACLs
# avail|@groups,users|rpms/Package/branch

avail | @provenpackager,pingou | rpms/guake/f18
avail | @provenpackager,pingou,toshio | rpms/guake/master
avail | @provenpackager, | rpms/fedocal/f18
avail | @provenpackager, | rpms/fedocal/master
avail | @provenpackager, | rpms/geany/f18
avail | @provenpackager,@gtk-sig, | rpms/geany/master"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/vcs/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            u'packageAcls': {
                u'f18': {
                    u'commit': {
                        u'groups': [u'provenpackager'],
                        u'people': []
                    }
                },
                u'master': {
                    u'commit': {
                        u'groups': [u'provenpackager', u'gtk-sig'],
                        u'people': []
                    }
                }
            },
            u'title': u'Fedora Package Database -- VCS ACLs'}
        self.assertEqual(data, expected)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskApiExtrasTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
