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
from tests import (Modeltests, FakeFasUser, FakeFasUserAdmin,
                   create_package_acl, user_set)


class FlaskUiPackagesTest(Modeltests):
    """ Flask tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskUiPackagesTest, self).setUp()

        pkgdb2.APP.config['TESTING'] = True
        pkgdb2.SESSION = self.session
        pkgdb2.ui.SESSION = self.session
        pkgdb2.ui.acls.SESSION = self.session
        pkgdb2.ui.admin.SESSION = self.session
        pkgdb2.ui.collections.SESSION = self.session
        pkgdb2.ui.packagers.SESSION = self.session
        pkgdb2.ui.packages.SESSION = self.session
        self.app = pkgdb2.APP.test_client()

    def test_list_packages(self):
        """ Test the list_packages function. """

        output = self.app.get('/packages/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Search packages</h1>' in output.data)

        output = self.app.get('/packages/?limit=abc&page=def')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Search packages</h1>' in output.data)

    def test_package_info(self):
        """ Test the package_info function. """
        create_package_acl(self.session)

        output = self.app.get('/package/geany/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1 property="doap:name">geany</h1>' in output.data)
        self.assertTrue('<h3>Fedora 18</h3>' in output.data)
        self.assertTrue('<a href="/packager/pingou/">' in output.data)
        self.assertTrue('<a href="/packager/group::gtk-sig/">' in output.data)

        output = self.app.get('/package/random/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<li class="errors">No package of this name found.</li>'
            in output.data)

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.is_admin')
    def test_package_new(self, login_func, mock_func):
        """ Test the package_new function. """
        login_func.return_value = None
        create_package_acl(self.session)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/new/package/')
            self.assertEqual(output.status_code, 302)

        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/new/package/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Create a new package</h1>' in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'pkg_name': '',
                'pkg_summary': '',
                'pkg_description': '',
                'pkg_reviewURL': '',
                'pkg_status': '',
                'pkg_shouldopen': '',
                'pkg_collection': '',
                'pkg_poc': '',
                'pkg_upstreamURL': '',
                'pkg_critpath': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/new/package/', data=data)
            self.assertEqual(output.status_code, 200)
            ## FIXME: this is the same problem as in test_api_package_new
            ## we need to look into this.
            self.assertTrue(
                output.data.count(
                    '<td class="errors">This field is required.</td>'
                ) in (5, 7))

            mock_func.get_packagers.return_value = ['mclasen']
            mock_func.log.return_value = ''

            data = {
                'pkg_name': 'gnome-terminal',
                'pkg_summary': 'Terminal emulator for GNOME',
                'pkg_description': 'Terminal for GNOME...',
                'pkg_reviewURL': 'http://bugzilla.redhat.com/1234',
                'pkg_status': 'Approved',
                'pkg_shouldopen': True,
                'pkg_collection': 'devel',
                'pkg_poc': 'mclasen',
                'pkg_upstreamURL': '',
                'pkg_critpath': False,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/new/package/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Package created</li>' in output.data)
            self.assertTrue(
                '<h1>Search packages</h1>' in output.data)
            self.assertTrue(
                '<a href="/package/gnome-terminal/">' in output.data)

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_package_give(self, login_func, mock_func):
        """ Test the package_give function. """
        login_func.return_value = None
        create_package_acl(self.session)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/guake/give')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Give Point of Contact of package: guake</h1>'
                in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'pkg_branch': '',
                'pkg_poc': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/package/guake/give', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(
                output.data.count(
                    '<td class="errors">This field is required.</td>'
                ), 1)

        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/guake/give')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Give Point of Contact of package: guake</h1>'
                in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'pkg_branch': 'devel',
                'pkg_poc': 'limb',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/package/guake/give', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">The point of contact of this package '
                'is not in the packager group</li>'
                in output.data)

        mock_func.get_packagers.return_value = ['spot']
        mock_func.log.return_value = ''

        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/guake/give')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Give Point of Contact of package: guake</h1>'
                in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'pkg_branch': 'devel',
                'pkg_poc': 'spot',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/package/guake/give', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1 property="doap:name">guake</h1>'
                            in output.data)
            self.assertTrue('<a href="/packager/spot/">' in output.data)

        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/random/give')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">No package of this name found.</li>'
                in output.data)

        user.username = 'ralph'
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/guake/give')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Give Point of Contact of package: guake</h1>'
                in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'pkg_branch': 'devel',
                'pkg_poc': 'spot',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/package/guake/give', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<td><select id="pkg_branch" multiple ''name="pkg_branch">'
                '</select></td>' in output.data)

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_package_orphan(self, login_func, mock_func):
        """ Test the package_orphan function. """
        login_func.return_value = None
        create_package_acl(self.session)

        user = FakeFasUser()
        user.username = 'toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/package/guake/devel/orphan', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">You are not allowed to change the point '
                'of contact.</li>' in output.data)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/package/guake/devel/orphan', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">You are no longer point of contact on '
                'branch: devel</li>' in output.data)

        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/package/guake/devel/orphan', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">You are no longer point of contact on '
                'branch: devel</li>' in output.data)

        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/package/random/devel/orphan', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">No package of this name found.</li>'
                in output.data)

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_package_retire(self, login_func, mock_func):
        """ Test the package_retire function. """
        login_func.return_value = None
        create_package_acl(self.session)

        user = FakeFasUser()
        user.username = 'toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/package/guake/devel/retire', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">This package has not been orphaned on '
                'branch: devel</li>' in output.data)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/package/guake/devel/orphan', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">You are no longer point of contact on '
                'branch: devel</li>' in output.data)
            output = self.app.get(
                '/package/guake/F-18/orphan', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">You are no longer point of contact on '
                'branch: F-18</li>' in output.data)

        user = FakeFasUser()
        user.username = 'toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/package/guake/devel/retire', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">This package has been retired on '
                'branch: devel</li>' in output.data)

            output = self.app.get(
                '/package/guake/F-18/retire', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">You are not allowed to retire the '
                'package: guake on branch F-18.</li>' in output.data)

        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/package/guake/F-18/retire', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">This package has been retired on '
                'branch: F-18</li>' in output.data)

        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/package/random/devel/retire', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">No package of this name found.</li>'
                in output.data)

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_package_take(self, login_func, mock_func):
        """ Test the package_take function. """
        login_func.return_value = None
        create_package_acl(self.session)

        user = FakeFasUser()
        user.username = 'toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/package/guake/devel/take', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">Package is not orphaned on devel</li>'
                in output.data)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/package/guake/devel/orphan', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">You are no longer point of contact on '
                'branch: devel</li>' in output.data)

            output = self.app.get(
                '/package/guake/devel/take', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">You have taken the package guake on '
                'branch devel</li>' in output.data)

        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/package/random/devel/take', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">No package of this name found.</li>'
                in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskUiPackagesTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
