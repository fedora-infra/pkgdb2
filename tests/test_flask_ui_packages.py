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
pkgdb tests for the Flask application.
'''

__requires__ = ['SQLAlchemy >= 0.8']
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
        create_package_acl(self.session)

        output = self.app.get('/packages/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Search packages</h1>' in output.data)
        self.assertTrue('<p>4 packages found</p>' in output.data)

        output = self.app.get('/packages/?limit=abc&page=def')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Search packages</h1>' in output.data)
        self.assertTrue('<p>4 packages found</p>' in output.data)
        self.assertTrue(
            '<li class="errors">Incorrect limit provided, using default</li>'
            in output.data)

        output = self.app.get('/packages/?orphaned=0')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Search packages</h1>' in output.data)
        self.assertTrue('<p>4 packages found</p>' in output.data)

    def test_package_info(self):
        """ Test the package_info function. """
        create_package_acl(self.session)

        output = self.app.get('/package/geany/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<h1 class="inline" property="doap:name">geany</h1>'
            in output.data)
        self.assertTrue('<th>Fedora 18</th>' in output.data)
        self.assertTrue('<a href="/packager/pingou/">' in output.data)
        self.assertTrue('<a href="/packager/group::gtk-sig/">' in output.data)

        output = self.app.get('/package/random/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<li class="errors">No package of this name found.</li>'
            in output.data)

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.is_admin')
    def test_package_new(self, login_func, utils_module):
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
                'pkg_collection': '',
                'pkg_poc': '',
                'pkg_upstreamURL': '',
                'pkg_critpath': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/new/package/', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(
                output.data.count(
                    '<td class="errors">This field is required.</td>'
                ), 5)

            utils_module.get_packagers.return_value = ['mclasen']
            utils_module.log.return_value = ''

            data = {
                'pkgname': 'gnome-terminal',
                'summary': 'Terminal emulator for GNOME',
                'description': 'Terminal for GNOME...',
                'review_url': 'http://bugzilla.redhat.com/1234',
                'status': 'Approved',
                'branches': 'master',
                'poc': 'mclasen',
                'upstream_url': '',
                'critpath': False,
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
    def test_package_give(self, login_func, utils_module):
        """ Test the package_give function. """
        login_func.return_value = None
        create_package_acl(self.session)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/guake/give')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title> Give package | PkgDB </title>' in output.data)

            output = self.app.get('/package/guake/give/0')
            self.assertEqual(output.status_code, 200)
            self.assertFalse(
                '<title> Give package | PkgDB </title>' in output.data)
            self.assertTrue(
                '<h1>Give Point of Contact of package: guake</h1>'
                in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'branches': '',
                'poc': '',
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
                'branches': 'master',
                'poc': 'limb',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/package/guake/give', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                'class="error">User &#34;limb&#34; is not in the packager '
                'group</' in output.data)

        utils_module.get_packagers.return_value = ['spot']
        utils_module.log.return_value = ''

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
                'branches': 'master',
                'poc': 'spot',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/package/guake/give', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1 class="inline" property="doap:name">guake</h1>'
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
                'branches': 'master',
                'poc': 'spot',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/package/guake/give', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<td><select id="branches" multiple ''name="branches">'
                '</select></td>' in output.data)

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_package_orphan(self, login_func, utils_module):
        """ Test the package_orphan function. """
        login_func.return_value = None
        create_package_acl(self.session)

        user = FakeFasUser()
        user.username = 'toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/guake/orphan')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title> Select branches | PkgDB </title>' in output.data)

            output = self.app.get('/package/guake/orphan/0')
            self.assertEqual(output.status_code, 200)
            self.assertFalse(
                '<title> Select branches | PkgDB </title>' in output.data)

            output = self.app.post(
                '/package/guake/orphan', follow_redirects=True,
                data={'branches': ['master']})
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                'class="errors">&#39;master&#39; is not a valid choice for '
                'this field</td>' in output.data)
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

        data = {
            'branches': ['master'],
            'csrf_token': csrf_token,
        }

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/guake/orphan', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">You are no longer point of contact on '
                'branch: master</li>' in output.data)

            # You cannot orphan twice the same package, the branch is no
            # longer available
            output = self.app.post(
                '/package/guake/orphan', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<td class="errors">&#39;master&#39; is not a valid choice '
                'for this field</td>' in output.data)

        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/random/orphan', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">No package of this name found.</li>'
                in output.data)

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_package_retire(self, login_func, utils_module):
        """ Test the package_retire function. """
        login_func.return_value = None
        create_package_acl(self.session)

        # Check at the very beginning
        output = self.app.get('/package/guake/')
        self.assertEqual(output.data.count('Obsolete'), 0)
        self.assertEqual(output.data.count('Awaiting Review'), 3)

        data = {
            'branches': ['foobar'],
        }

        user = FakeFasUser()
        user.username = 'toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/guake/retire', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                'class="errors">Only Admins are allowed to retire package '
                'here, you should use `fedpkg retire`.</li>' in output.data)
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

        data = {
            'branches': ['master'],
            'csrf_token': csrf_token,
        }

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/guake/orphan', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">You are no longer point of contact on '
                'branch: master</li>' in output.data)

            data['branches'] = ['f18']
            output = self.app.post(
                '/package/guake/orphan', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">You are no longer point of contact on '
                'branch: f18</li>' in output.data)

            # Check after orphaning
            # Orphaning already drops the ACLs of the person doing the action
            output = self.app.get('/package/guake/')
            self.assertEqual(output.data.count('Obsolete'), 8)
            self.assertEqual(output.data.count('Awaiting Review'), 3)

        data = {
            'branches': ['master'],
            'csrf_token': csrf_token,
        }

        user = FakeFasUser()
        user.username = 'toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/guake/retire', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                'class="errors">Only Admins are allowed to retire package '
                'here, you should use `fedpkg retire`.</li>' in output.data)

        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/guake/retire')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title> Select branches | PkgDB </title>' in output.data)

            output = self.app.get('/package/guake/retire/0')
            self.assertEqual(output.status_code, 200)
            self.assertFalse(
                '<title> Select branches | PkgDB </title>' in output.data)

            data['branches'] = ['foobar']
            output = self.app.post(
                '/package/guake/retire', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<td class="errors">&#39;foobar&#39; is not a valid choice '
                'for this field</td>' in output.data)

            # Retire F18 that has been orphaned before
            data['branches'] = ['f18']
            output = self.app.post(
                '/package/guake/retire', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">This package has been retired on '
                'branch: f18</li>' in output.data)

            # Package retired, clear all the ACLs on branch f18
            output = self.app.get('/package/guake/')
            self.assertEqual(output.data.count('Obsolete'), 8)
            self.assertEqual(output.data.count('Awaiting Review'), 3)

            # Retire branch master
            data['branches'] = ['master']
            output = self.app.post(
                '/package/guake/retire', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">This package has been retired on '
                'branch: master</li>' in output.data)

            # Package retired, clear all the ACLs on master
            output = self.app.get('/package/guake/')
            self.assertEqual(output.data.count('Obsolete'), 12)
            self.assertEqual(output.data.count('Awaiting Review'), 0)

        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/random/retire', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">No package of this name found.</li>'
                in output.data)

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_package_unretire(self, login_func, utils_module):
        """ Test the package_unretire function. """
        login_func.return_value = None
        create_package_acl(self.session)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/guake/orphan')
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

        # Oprhan and retire guake on F18
        data = {
            'branches': ['f18'],
            'csrf_token': csrf_token,
        }

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/guake/orphan', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">You are no longer point of contact on '
                'branch: f18</li>' in output.data)

        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):

            output = self.app.post(
                '/package/guake/retire', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">This package has been retired on '
                'branch: f18</li>' in output.data)

        # Start testing unretire

        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/package/random/unretire', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">No package of this name found.</li>'
                in output.data)

            output = self.app.post(
                '/package/random/unretire', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">No package of this name found.</li>'
                in output.data)

            output = self.app.post(
                '/package/guake/unretire', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">User &#34;admin&#34; is not in the '
                'packager group</li>' in output.data)

        mock_func.get_packagers.return_value = ['pingou', 'toshio']
        user.username = 'toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/package/guake/unretire', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<td><select id="branches" multiple name="branches">'
                '<option value="f18">f18</option></select></td>'
                in output.data)

            output = self.app.post(
                '/package/guake/unretire', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Admins have been asked to un-retire '
                'branch: f18</li>' in output.data)

            output = self.app.post(
                '/package/guake/unretire/0', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">Could not save the request for branch: '
                'f18, has it already been requested?</li>' in output.data)

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_package_take(self, login_func, utils_module):
        """ Test the package_take function. """
        login_func.return_value = None
        utils_module.get_packagers.return_value = ['pingou', 'toshio']

        create_package_acl(self.session)

        data = {
            'branches': ['master'],
        }

        user = FakeFasUser()
        user.username = 'toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/guake/take', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No branches orphaned found</li>'
                in output.data)
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

        data = {
            'branches': ['master'],
            'csrf_token': csrf_token,
        }

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/guake/orphan', follow_redirects=True, data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">You are no longer point of contact on '
                'branch: master</li>' in output.data)

        data = {
            'branches': ['foo'],
        }

        user = FakeFasUser()
        user.username = 'toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/guake/take', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<td class="errors">&#39;foo&#39; is not a valid choice '
                'for this field</td>' in output.data)
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

        data = {
            'branches': ['master'],
            'csrf_token': csrf_token,
        }

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/guake/take')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title> Select branches | PkgDB </title>' in output.data)

            output = self.app.get('/package/guake/take/0')
            self.assertEqual(output.status_code, 200)
            self.assertFalse(
                '<title> Select branches | PkgDB </title>' in output.data)

            output = self.app.post(
                '/package/guake/take', follow_redirects=True, data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">You have taken the package guake on '
                'branch master</li>' in output.data)

        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/random/take', follow_redirects=True, data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">No package of this name found.</li>'
                in output.data)

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_delete_package(self, login_func, utils_module):
        """ Test the delete_package function. """
        login_func.return_value = None
        utils_module.get_packagers.return_value = ['pingou', 'toshio']
        create_package_acl(self.session)

        data = {}

        # User is not an admin
        user = FakeFasUser()
        user.username = 'toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/guake/delete', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">You are not an administrator of pkgdb'
                '</li>' in output.data)

        # User is an admin but no csrf
        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/guake/delete', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">Invalid input</li>' in output.data)

            output = self.app.get('/package/guake/')
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

        data = {
            'csrf_token': csrf_token,
        }

        # User is not an admin but csrf
        user = FakeFasUser()
        user.username = 'toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/guake/delete', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">You are not an administrator of pkgdb'
                '</li>' in output.data)

            # Check before deleting
            output = self.app.get('/packages/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<p>4 packages found</p>' in output.data)

        # User is an admin with csrf
        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/guake/delete', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Package guake deleted</li>'
                in output.data)
            self.assertTrue(
                '<p>3 packages found</p>' in output.data)

            output = self.app.post(
                '/package/random/delete', follow_redirects=True, data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">No package of this name found.</li>'
                in output.data)

    def test_package_timeline(self):
        """ Test the package_timeline function. """

        output = self.app.get('/package/guake/timeline')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('</a> > Timeline' in output.data)
        self.assertTrue(
            'Restrict to packager: <input type="text" name="packager" />'
            in output.data)

        output = self.app.get(
            '/package/guake/timeline?page=abc&limit=def&from_date=ghi'
            '&package=test')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('</a> > Timeline' in output.data)
        self.assertTrue(
            'Restrict to packager: <input type="text" name="packager" />'
            in output.data)
        self.assertTrue(
            'class="errors">Incorrect limit provided, using default</'
            in output.data)
        self.assertTrue(
            'class="errors">Incorrect from_date provided, using default</'
            in output.data)
        self.assertTrue(
            '<li class="errors">No package exists</li>' in output.data)

        output = self.app.get('/package/guake/timeline?from_date=2013-10-19')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('</a> > Timeline' in output.data)
        self.assertTrue(
            'Restrict to packager: <input type="text" name="packager" />'
            in output.data)
        self.assertTrue(
            '<p class=\'error\'>No logs found in the database.</p>'
            in output.data)

        # Put some data in the database
        create_package_acl(self.session)
        guake_pkg = model.Package.by_name(self.session, 'guake')
        pkgdb2.lib.utils.log(
            self.session,
            guake_pkg,
            'acl.update',
            dict(
                agent='pingou',
                username='pingou',
                acl='commit',
                previous_status='Approved',
                status='Obsolete',
                package_name='guake',
                package_listing={
                    'collection': {'branchname': 'master'}
                },
            )
        )
        pkgdb2.lib.utils.log(
            self.session,
            guake_pkg,
            'acl.update',
            dict(
                agent='pingou',
                username='pingou',
                acl='approveacls',
                previous_status='Obsolete',
                status='Approved',
                package_name='guake',
                package_listing={
                    'collection': {'branchname': 'master'}
                },
            )
        )

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/guake/timeline')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('</a> > Timeline' in output.data)
            self.assertTrue(
                'Restrict to packager: <input type="text" name="packager" />'
                in output.data)
            self.assertTrue(
                'user: pingou set for pingou acl: commit of package: guake '
                'from: Approved to: Obsolete on branch: master'
                in output.data)
            self.assertTrue(
                'user: pingou set for pingou acl: approveacls of package: '
                'guake from: Obsolete to: Approved on branch: master'
                in output.data)

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_package_request_branch(self, login_func, mock_func):
        """ Test the package_request_branch function. """
        login_func.return_value = None
        mock_func.get_packagers.return_value = ['pingou', 'toshio']
        create_package_acl(self.session)

        data = {
            'branches': ['epel7'],
        }

        user = FakeFasUser()
        user.username = 'toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/foobar/request_branch', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">No package of this name found.</li>'
                in output.data)

            output = self.app.post(
                '/package/guake/request_branch', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<td class="errors">&#39;epel7&#39; is not a valid choice '
                'for this field</td>' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

        data = {
            'branches': ['el6'],
            'csrf_token': csrf_token,
        }

        # Missing one input
        user = FakeFasUser()
        user.username = 'kevin'
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/guake/request_branch',
                follow_redirects=True, data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<td class="errors">Not a valid choice</td>' in output.data)

        data = {
            'branches': ['el6'],
            'from_branch': 'master',
            'csrf_token': csrf_token,
        }

        # Input correct but user is not allowed
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/guake/request_branch/0',
                follow_redirects=True, data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">User &#34;kevin&#34; is not in the '
                'packager group</li>' in output.data)

        data = {
            'branches': ['el6'],
            'from_branch': 'master',
            'csrf_token': csrf_token,
        }

        # All good
        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/package/guake/request_branch',
                follow_redirects=True, data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Branch el6 requested</li>'
                in output.data)

    @patch('pkgdb2.lib.utils.get_packagers')
    @patch('pkgdb2.packager_login_required')
    def test_package_request_new(self, login_func, mock_func):
        """ Test the package_request_new function. """
        login_func.return_value = None
        mock_func.return_value = ['pingou', 'toshio']
        create_package_acl(self.session)

        data = {
            'pkgname': 'guake',
            'summary': 'Drop down terminal for GNOME',
            'description': 'desc',
            'review_url': 'https://bz.rh.c/123',
            'status': 'Approved',
            'critpath': False,
            'poc': 'pingou',
            'upstream_url': 'http://guake.org',
            'branches': 'master',
        }

        user = FakeFasUser()

        user.username = 'toshio'
        data['branches'] = 'epel7'
        with user_set(pkgdb2.APP, user):

            # Branch EPEL7 does not exist
            output = self.app.post(
                '/request/package/', follow_redirects=True,
                data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<td class="errors">&#39;epel7&#39; is not a valid choice'
                in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

        data['csrf_token'] = csrf_token
        data['branches'] = 'master'

        # All good
        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/request/package/',
                follow_redirects=True, data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">user: pingou request package: guake '
                'on branch master</li>' in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskUiPackagesTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
