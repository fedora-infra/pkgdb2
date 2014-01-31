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

import pkgdb2
from pkgdb2.lib import model
from tests import (Modeltests, FakeFasUser,
                   create_package_acl, create_package_acl2,
                   create_package_critpath)


class FlaskApiExtrasTest(Modeltests):
    """ Flask API extras tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskApiExtrasTest, self).setUp()

        pkgdb2.APP.config['TESTING'] = True
        pkgdb2.SESSION = self.session
        pkgdb2.api.extras.SESSION = self.session
        self.app = pkgdb2.APP.test_client()

        # Let's make sure the cache is empty for the tests
        pkgdb2.CACHE.invalidate()

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

        output = self.app.get('/api/bugzilla/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/bugzilla/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        expected = {
            u'bugzillaAcls': {},
            u'title': u'Fedora Package Database -- Bugzilla ACLs'
        }

        self.assertEqual(data, expected)

        output = self.app.get(
            '/api/bugzilla/',
            environ_base={'HTTP_ACCEPT': 'application/json'})
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        self.assertEqual(data, expected)

    def test_api_bugzilla_filled(self):
        """ Test the api_bugzilla function with a filled database. """
        # Fill the DB
        create_package_acl2(self.session)

        output = self.app.get('/api/bugzilla/')
        self.assertEqual(output.status_code, 200)

        expected = """# Package Database VCS Acls
# Text Format
# Collection|Package|Description|Owner|Initial QA|Initial CCList
# Backslashes (\) are escaped as \u005c Pipes (|) are escaped as \u007c

Fedora|fedocal|A web-based calendar for Fedora|orphan||pingou,toshio
Fedora|geany|A fast and lightweight IDE using GTK2|group::gtk-sig||
Fedora|guake|Top down terminal for GNOME|pingou||spot"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/bugzilla/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/bugzilla/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            u'bugzillaAcls': {
                u'Fedora': [
                    {
                        "fedocal": {
                            "owner": "orphan",
                            "cclist": {
                                "groups": [],
                                "people": ["pingou", 'toshio']
                            },
                            "qacontact": None,
                            "summary": "A web-based calendar for Fedora"
                        }
                    },
                    {
                        u'geany': {
                            u'owner': u'@gtk-sig',
                            u'cclist': {
                                u'groups': [],
                                u'people': []
                            },
                            u'qacontact': None,
                            u'summary': u'A fast and lightweight IDE using '
                            'GTK2'
                        }
                    },
                    {
                        u'guake': {
                            u'owner': u'pingou',
                            u'cclist': {
                                u'groups': [],
                                u'people': [u'spot']
                            },
                            u'qacontact': None,
                            u'summary': u'Top down terminal for GNOME'
                        }
                    },
                ]
            },
            u'title': u'Fedora Package Database -- Bugzilla ACLs'
        }

        self.assertEqual(data, expected)

        # Filter for a collection
        output = self.app.get('/api/bugzilla/?collection=Fedora EPEL')
        self.assertEqual(output.status_code, 200)

        expected = """# Package Database VCS Acls
# Text Format
# Collection|Package|Description|Owner|Initial QA|Initial CCList
# Backslashes (\) are escaped as \u005c Pipes (|) are escaped as \u007c

"""
        self.assertEqual(output.data, expected)

    def test_api_notify_empty(self):
        """ Test the api_notify function with an empty database. """

        # Empty DB
        output = self.app.get('/api/notify/')
        self.assertEqual(output.status_code, 200)

        expected = ""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/notify/?format=random')
        self.assertEqual(output.status_code, 200)
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

        output = self.app.get(
            '/api/notify/',
            environ_base={'HTTP_ACCEPT': 'application/json'})
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        self.assertEqual(data, expected)

    def test_api_notify_filled(self):
        """ Test the api_notify function with a filled database. """
        # Filled DB
        create_package_acl(self.session)

        output = self.app.get('/api/notify/')
        self.assertEqual(output.status_code, 200)

        expected = """geany|group::gtk-sig
guake|pingou
"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/notify/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/notify/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            u'title': u'Fedora Package Database -- Notification List',
            u'packages': [
                {u'geany': [u'group::gtk-sig']},
                {u'guake': [u'pingou']},
            ],
            u'name': None,
            u'version': None,
            u'eol': False
        }
        self.assertEqual(data, expected)

        output = self.app.get('/api/notify/?name=Fedora')
        self.assertEqual(output.status_code, 200)

        expected = """geany|group::gtk-sig
guake|pingou
"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/notify/?name=Fedora&version=18')
        self.assertEqual(output.status_code, 200)

        expected = """guake|pingou
"""
        self.assertEqual(output.data, expected)

    def test_api_vcs_empty(self):
        """ Test the api_vcs function with an empty database. """

        # Empty DB
        output = self.app.get('/api/vcs/')
        self.assertEqual(output.status_code, 200)

        expected = """# VCS ACLs
# avail|@groups,users|rpms/Package/branch

"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/vcs/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/vcs/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        expected = {
            u'packageAcls': {},
            u'title': u'Fedora Package Database -- VCS ACLs'
        }

        self.assertEqual(data, expected)

        output = self.app.get(
            '/api/vcs/',
            environ_base={'HTTP_ACCEPT': 'application/json'})
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        self.assertEqual(data, expected)

    def test_api_vcs_filled(self):
        """ Test the api_vcs function with a filled database. """
        # Filled DB
        create_package_acl2(self.session)

        output = self.app.get('/api/vcs/')
        self.assertEqual(output.status_code, 200)

        expected = """# VCS ACLs
# avail|@groups,users|rpms/Package/branch

avail | @provenpackager,pingou | rpms/fedocal/f17
avail | @provenpackager,pingou | rpms/fedocal/f18
avail | @provenpackager,pingou,toshio | rpms/fedocal/master
avail | @provenpackager,@gtk-sig, | rpms/geany/master
avail | @provenpackager,pingou | rpms/guake/f18
avail | @provenpackager,pingou,spot | rpms/guake/master"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/vcs/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/vcs/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            u'packageAcls': {
                u'guake': {
                    u'f18': {
                        u'commit': {
                            u'groups': [u'provenpackager'],
                            u'people': [u'pingou']
                        }
                    },
                    u'master': {
                        u'commit': {
                            u'groups': [u'provenpackager'],
                            u'people': [u'pingou', u'spot']
                        }
                    }
                },
                u'geany': {
                    u'master': {
                        u'commit': {
                            u'groups': [u'provenpackager', u'gtk-sig'],
                            u'people': []
                        }
                    }
                },
                "fedocal": {
                    "f18": {
                        "commit": {
                            "groups": ["provenpackager"],
                            "people": ["pingou"]
                        }
                    },
                    "master": {
                        "commit": {
                            "groups": ["provenpackager"],
                            "people": ["pingou", "toshio"]
                        }
                    },
                    "f17": {
                        "commit": {
                            "groups": ["provenpackager"],
                            "people": ["pingou"]
                        }
                    }
                }
            },
            u'title': u'Fedora Package Database -- VCS ACLs'}

        self.assertEqual(data, expected)

    def test_api_critpath_empty(self):
        """ Test the api_critpath function with an empty database. """

        # Empty DB
        output = self.app.get('/api/critpath/')
        self.assertEqual(output.status_code, 200)

        expected = ""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/critpath/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/critpath/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        expected = {"pkgs": {}}

        self.assertEqual(data, expected)

        output = self.app.get(
            '/api/critpath/',
            environ_base={'HTTP_ACCEPT': 'application/json'})
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        self.assertEqual(data, expected)

    def test_api_critpath_filled(self):
        """ Test the api_critpath function with a filled database. """
        # Fill the DB
        create_package_acl(self.session)
        create_package_critpath(self.session)

        output = self.app.get('/api/critpath/')
        self.assertEqual(output.status_code, 200)

        expected = """== devel ==
* kernel
== F-18 ==
* kernel
"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/critpath/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/critpath/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            u'pkgs': {
                u'F-18': [
                    u"kernel"
                ],
                u'devel': [
                    u"kernel"
                ]
            },
        }

        self.assertEqual(data, expected)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskApiExtrasTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
