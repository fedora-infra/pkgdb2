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

from mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import pkgdb2
from pkgdb2 import APP
from pkgdb2.lib import model
from tests import (Modeltests, FakeFasUser, FakeFasUserAdmin,
                   create_package_acl, user_set)


class FlaskApiAclsTest(Modeltests):
    """ Flask API ACLs tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskApiAclsTest, self).setUp()

        pkgdb2.APP.config['TESTING'] = True
        pkgdb2.SESSION = self.session
        pkgdb2.api.acls.SESSION = self.session
        self.app = pkgdb2.APP.test_client()

    @patch('pkgdb2.packager_login_required')
    def test_acl_update(self, login_func):
        """ Test the api_acl_update function.  """
        login_func.return_value = None

        output = self.app.post('/api/package/acl')
        self.assertEqual(output.status_code, 301)

        user = FakeFasUser()
        with user_set(APP, user):
            output = self.app.post('/api/package/acl/')
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "output": "notok",
                    "error_detail": [
                        "pkg_acl: Not a valid choice",
                        "pkg_name: This field is required.",
                        "acl_status: Not a valid choice",
                        "pkg_user: This field is required.",
                        "pkg_branch: This field is required."
                    ],
                    "error": "Invalid input submitted",
                }
            )

        create_package_acl(self.session)

        data = {
            'pkg_name': 'guake',
            'pkg_branch': 'devel',
            'pkg_acl': 'commit',
            'acl_status': 'Approved',
            'pkg_user': 'toshio',
        }

        # Check if it works authenticated
        user = FakeFasUser()

        with user_set(APP, user):
            exp = {
                "messages": [
                    "user: pingou set acl: commit of package: guake from: "
                    "Awaiting Review to: Approved on branch: devel"
                ],
                "output": "ok"
            }
            output = self.app.post('/api/package/acl/', data=data)
            json_out = json.loads(output.data)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(json_out, exp)

        # Check if it fails normally
        user.username = 'Ralph'

        with user_set(APP, user):
            exp = {
                "error": "You are not allowed to update ACLs of someone else.",
                "output": "notok"
            }
            output = self.app.post('/api/package/acl/', data=data)
            json_out = json.loads(output.data)
            self.assertEqual(output.status_code, 500)
            self.assertEqual(json_out, exp)

        # Check if it works for admins
        user = FakeFasUserAdmin()

        with user_set(APP, user):
            exp = {
                "messages": [
                    "user: admin set acl: commit of package: guake from: "
                    "Approved to: Approved on branch: devel"
                ],
                "output": "ok"
            }
            output = self.app.post('/api/package/acl/', data=data)
            json_out = json.loads(output.data)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(json_out, exp)

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_acl_reassign(self, login_func, mock_func):
        """ Test the api_acl_reassign function. """
        login_func.return_value = None

        output = self.app.post('/api/package/acl/reassign')
        self.assertEqual(output.status_code, 301)

        user = FakeFasUser()
        with user_set(APP, user):
            output = self.app.post('/api/package/acl/reassign/')
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(data, {
                "output": "notok",
                "error": "Invalid input submitted",
            })

        create_package_acl(self.session)

        data = {
            'packages': 'guake,geany',
            'branches': 'devel',
            'user_target': 'toshio',
        }

        # Fails is user is not a packager.
        user = FakeFasUser()
        with user_set(APP, user):
            exp = {
                "error": "The point of contact of this package is not in "
                         "the packager group",
                "output": "notok"
            }
            output = self.app.post('/api/package/acl/reassign/', data=data)
            json_out = json.loads(output.data)
            self.assertEqual(output.status_code, 500)
            self.assertEqual(json_out, exp)

        mock_func.get_packagers.return_value = ['pingou', 'ralph', 'toshio']
        mock_func.log.return_value = ''

        # Fails is user is a packager but not in the group that is the
        # current poc
        with user_set(APP, user):
            exp = {
                "error": "You are not part of the group \"gtk-sig\", you "
                         "are not allowed to change the point of contact.",
                "output": "notok"
            }
            output = self.app.post('/api/package/acl/reassign/', data=data)
            json_out = json.loads(output.data)
            self.assertEqual(output.status_code, 500)
            self.assertEqual(json_out, exp)

        # Works
        user.groups.append('gtk-sig')

        with user_set(APP, user):
            exp = {"messages": ['', ''], "output": "ok"}
            output = self.app.post('/api/package/acl/reassign/', data=data)
            json_out = json.loads(output.data)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(json_out, exp)

        # Check if it fails normally
        user.username = 'Ralph'

        with user_set(APP, user):
            exp = {
                "error": "You are not allowed to change the point of contact.",
                "output": "notok"
            }
            output = self.app.post('/api/package/acl/reassign/', data=data)
            json_out = json.loads(output.data)
            self.assertEqual(output.status_code, 500)
            self.assertEqual(json_out, exp)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskApiAclsTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
