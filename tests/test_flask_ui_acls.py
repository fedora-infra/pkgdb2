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
pkgdb tests for the Flask application.
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
from pkgdb2.lib import model
from tests import (Modeltests, FakeFasUser, create_package_acl, user_set)


class FlaskUiAclsTest(Modeltests):
    """ Flask tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskUiAclsTest, self).setUp()

        pkgdb2.APP.config['TESTING'] = True
        pkgdb2.SESSION = self.session
        pkgdb2.ui.SESSION = self.session
        pkgdb2.ui.acls.SESSION = self.session
        pkgdb2.ui.admin.SESSION = self.session
        pkgdb2.ui.collections.SESSION = self.session
        pkgdb2.ui.packagers.SESSION = self.session
        pkgdb2.ui.packages.SESSION = self.session
        self.app = pkgdb2.APP.test_client()

    @patch('pkgdb2.fas_login_required')
    def test_request_acl(self, login_func):
        """ Test the request_acl function. """
        login_func.return_value=None

        create_package_acl(self.session)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/acl/guake/request/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Request ACLs on package: guake</h1>' in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)
            self.assertTrue(
                '<option value="approveacls">approveacls' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'pkg_branch': 'devel',
                'pkg_acl': 'watchbugzilla',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/acl/guake/request/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="message">ACLs updated</li>' in
                            output.data)

        user = FakeFasUser()
        user.groups = ['gitr2spec']
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/acl/guake/request/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Request ACLs on package: guake</h1>' in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)
            self.assertTrue(
                '<option value="approveacls">approveacls' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'pkg_branch': 'devel',
                'pkg_acl': 'commit',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/acl/guake/request/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">ACLs updated</li>' in output.data)
            self.assertTrue(
                '<li class="errors">You must be a packager to apply to the '
                'ACL: commit on devel</li>' in output.data)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/acl/test/request/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Request ACLs on package: test</h1>' in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)
            self.assertTrue(
                '<option value="approveacls">approveacls' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'pkg_branch': 'devel',
                'pkg_acl': 'commit',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/acl/test/request/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No package found by this name</li>'
                in output.data)

    @patch('pkgdb2.fas_login_required')
    def test_watch_package(self, login_func):
        """ Test the watch_package function. """
        login_func.return_value=None

        create_package_acl(self.session)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/acl/guake/watch/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">ACLs updated</li>' in output.data)

            output = self.app.get(
                '/acl/random/watch/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No package found by this name</li>'
                in output.data)

    @patch('pkgdb2.packager_login_required')
    def test_comaintain_package(self, login_func):
        """ Test the comaintain_package function. """
        login_func.return_value=None

        create_package_acl(self.session)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/acl/guake/comaintain/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">You are already a co-maintainer on '
                'F-18</li>' in output.data)
            self.assertFalse(
                '<li class="message">ACLs updated</li>' in output.data)

            output = self.app.get(
                '/acl/random/comaintain/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No package found by this name</li>'
                in output.data)

        user = FakeFasUser()
        user.username = 'kevin'
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/acl/guake/comaintain/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">ACLs updated</li>' in output.data)

            output = self.app.get(
                '/acl/random/comaintain/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No package found by this name</li>'
                in output.data)

        user = FakeFasUser()
        user.groups = ['gitr2spec']
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/acl/guake/comaintain/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">You must be a packager</li>'
                in output.data)

    @patch('pkgdb2.fas_login_required')
    def test_update_acl(self, login_func):
        """ Test the update_acl function. """
        login_func.return_value=None

        create_package_acl(self.session)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/acl/guake/update/pingou/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Update ACLs on package: guake</h1>' in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)
            self.assertTrue(
                '<option value="approveacls">approveacls' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'pkg_branch': 'devel',
                'pkg_acl': 'commit',
                'acl_status': 'Approved',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/acl/guake/update/pingou/', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">ACLs updated</li>' in output.data)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/acl/guake/update/test/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Update ACLs on package: guake</h1>' in output.data)
            self.assertTrue(
                'No pending ACLs for this user on this package.' in output.data)

        user = FakeFasUser()
        user.groups = ['gitr2spec']
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/acl/guake/update/toshio/devel', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Update ACLs on package: guake</h1>' in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)
            self.assertTrue(
                '<option value="approveacls">approveacls' in output.data)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/acl/guake/update/pingou/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Update ACLs on package: guake</h1>' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'pkg_branch': 'devel',
                'pkg_acl': 'watchbugzilla',
                'acl_status': 'Awaiting Review',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/acl/guake/update/pingou/', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">ACLs updated</li>' in output.data)

    @patch('pkgdb2.packager_login_required')
    def test_pending_acl(self, login_func):
        """ Test the pending_acl function. """
        login_func.return_value=None

        create_package_acl(self.session)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/acl/pending/')
            self.assertTrue('<table id="pending">' in output.data)
            self.assertTrue(
                '<a href="/acl/guake/update/toshio/">' in output.data)
            self.assertTrue(
                '<input type="submit" value="Update"/>' in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskUiAclsTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
