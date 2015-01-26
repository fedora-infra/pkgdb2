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

import unittest
import sys
import os

from mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import pkgdb2
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

    @patch('pkgdb2.lib.utils.get_packagers')
    @patch('pkgdb2.fas_login_required')
    def test_request_acl(self, login_func, mock_func):
        """ Test the request_acl function. """
        login_func.return_value = None

        create_package_acl(self.session)

        user = FakeFasUser()
        mock_func.return_value = ['pingou', 'ralph', 'kevin']

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
                'branches': 'master',
                'acl': 'watchbugzilla',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/acl/guake/request/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="message">ACLs updated</li>' in
                            output.data)

        user.username = 'Toshio'
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
                'branches': 'master',
                'acl': 'watchbugzilla',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/acl/guake/request/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="message">ACLs updated</li>' in
                            output.data)

            data = {
                'branches': 'master',
                'acl': 'commit',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/acl/guake/request/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                'class="error">User &#34;Toshio&#34; is not in the packager'
                ' group</' in output.data)

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
                'branches': 'master',
                'acl': 'commit',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/acl/guake/request/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">ACLs updated</li>' in output.data)
            self.assertTrue(
                '<li class="errors">You must be a packager to apply to the '
                'ACL: commit on master</li>' in output.data)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/acl/test/request/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">No package of this name found.</li>'
                in output.data)

            data = {
                'branches': 'master',
                'acl': 'commit',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/acl/test/request/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">No package of this name found.</li>'
                in output.data)

    @patch('pkgdb2.lib.utils.get_packagers')
    @patch('pkgdb2.fas_login_required')
    def test_request_acl_all_branch(self, login_func, mock_func):
        """ Test the request_acl_all_branch function. """
        login_func.return_value = None

        create_package_acl(self.session)

        user = FakeFasUser()
        mock_func.return_value = ['pingou', 'ralph', 'kevin']

        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/acl/guake/request/approveacls/', follow_redirects=True)
            self.assertEqual(output.status_code, 405)

        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/guake/')
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]
            data = {'csrf_token': csrf_token}

            output = self.app.post(
                '/acl/guake/request/approveacls/',
                data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                'class="message">ACL approveacls requested on branch f18</li>'
                in output.data)
            self.assertTrue(
                'class="message">ACL approveacls requested on branch master</l'
                in output.data)
            self.assertEqual(
                output.data.count('<a class="pending"'), 2)

            output = self.app.post(
                '/acl/guake/request/foobar/',
                data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">Invalid ACL provided foobar.</li>'
                in output.data)

            output = self.app.post(
                '/acl/barfoo/request/commit/',
                data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No package found by this name</li>'
                in output.data)

        user.username = 'toshio'
        user.groups = []
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/acl/guake/request/commit/',
                data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">You must be a packager to apply to the '
                'ACL: commit on guake</li>'
                in output.data)

            output = self.app.post(
                '/acl/guake/request/watchcommits/',
                data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">ACL watchcommits requested on branch '
                'f18</li>' in output.data)
            self.assertTrue(
                '<li class="message">ACL watchcommits requested on branch '
                'master</li>' in output.data)

    @patch('pkgdb2.lib.utils.get_packagers')
    @patch('pkgdb2.fas_login_required')
    def test_giveup_acl(self, login_func, mock_func):
        """ Test the giveup_acl function. """
        login_func.return_value = None

        create_package_acl(self.session)

        user = FakeFasUser()
        mock_func.return_value = ['pingou', 'ralph', 'kevin', 'dodji']

        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/acl/guake/giveup/approveacls/', follow_redirects=True)
            self.assertEqual(output.status_code, 405)

        user.username = 'dodji'
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/guake/')
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]
            data = {'csrf_token': csrf_token}

            output = self.app.post(
                '/acl/offlineimap/giveup/approveacls/',
                data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No active branches found for you for '
                'the ACL: approveacls</li>' in output.data)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/guake/')
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]
            data = {'csrf_token': csrf_token}

            output = self.app.post(
                '/acl/guake/giveup/approveacls/',
                data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Your ACL approveacls is obsoleted on '
                'branch f18 of package guake</li>' in output.data)
            self.assertTrue(
                '<li class="message">Your ACL approveacls is obsoleted on '
                'branch master of package guake</li>' in output.data)
            self.assertEqual(
                output.data.count('<a class="pending"'), 1)

            output = self.app.post(
                '/acl/guake/giveup/foobar/',
                data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">Invalid ACL provided foobar.</li>'
                in output.data)

            output = self.app.post(
                '/acl/barfoo/giveup/commit/',
                data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No package found by this name</li>'
                in output.data)

        user.username = 'toshio'
        user.groups = []
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/acl/guake/giveup/commit/',
                data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertFalse(
                '<li class="error">User &#34;toshio&#34; is not in the '
                'packager group</li>' in output.data)

    @patch('pkgdb2.lib.utils.get_packagers')
    @patch('pkgdb2.fas_login_required')
    def test_watch_package(self, login_func, mock_func):
        """ Test the watch_package function. """
        login_func.return_value = None

        create_package_acl(self.session)

        user = FakeFasUser()
        mock_func.return_value = ['pingou', 'ralph', 'kevin']

        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/acl/guake/watch/', follow_redirects=True)
            self.assertEqual(output.status_code, 405)

        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/guake/')
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]
            data = {'csrf_token': csrf_token}

            output = self.app.post(
                '/acl/guake/watch/', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">ACLs updated</li>' in output.data)

            output = self.app.post(
                '/acl/random/watch/', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No package found by this name</li>'
                in output.data)

    @patch('pkgdb2.lib.utils.get_packagers')
    @patch('pkgdb2.fas_login_required')
    def test_unwatch_package(self, login_func, mock_func):
        """ Test the unwatch_package function. """
        login_func.return_value = None

        create_package_acl(self.session)

        user = FakeFasUser()
        mock_func.return_value = ['pingou', 'ralph', 'kevin']

        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/acl/guake/unwatch/', follow_redirects=True)
            self.assertEqual(output.status_code, 405)

        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/guake/')
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]
            data = {'csrf_token': csrf_token}

            output = self.app.post(
                '/acl/guake/unwatch/', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">ACLs updated</li>' in output.data)

            output = self.app.post(
                '/acl/random/unwatch/', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No package found by this name</li>'
                in output.data)

    @patch('pkgdb2.lib.utils.get_packagers')
    @patch('pkgdb2.packager_login_required')
    def test_comaintain_package(self, login_func, mock_func):
        """ Test the comaintain_package function. """
        login_func.return_value = None

        create_package_acl(self.session)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/acl/guake/comaintain/', follow_redirects=True)
            self.assertEqual(output.status_code, 405)

        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/guake/')
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]
            data = {'csrf_token': csrf_token}

            output = self.app.post(
                '/acl/guake/comaintain/',
                data=data, follow_redirects=True)

            self.assertTrue(
                '<li class="error">You are already a co-maintainer on '
                'f18</li>' in output.data)
            self.assertFalse(
                '<li class="message">ACLs updated</li>' in output.data)

            output = self.app.post(
                '/acl/random/comaintain/',
                data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No package found by this name</li>'
                in output.data)

        user = FakeFasUser()
        mock_func.return_value = ['pingou', 'ralph', 'kevin']

        user.username = 'kevin'
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/acl/guake/comaintain/',
                data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">ACLs updated</li>' in output.data)

            # Nothing to update the second time
            output = self.app.post(
                '/acl/guake/comaintain/',
                data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Nothing to update</li>' in output.data)

            output = self.app.post(
                '/acl/random/comaintain/',
                data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No package found by this name</li>'
                in output.data)

        user = FakeFasUser()
        user.groups = ['gitr2spec']
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/acl/guake/comaintain/',
                data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">You must be a packager</li>'
                in output.data)

    @patch('pkgdb2.lib.utils.get_packagers')
    @patch('pkgdb2.fas_login_required')
    def test_dropcommit_package(self, login_func, mock_func):
        """ Test the dropcommit_package function. """
        login_func.return_value = None

        create_package_acl(self.session)

        user = FakeFasUser()
        mock_func.return_value = ['pingou', 'ralph', 'kevin']

        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/acl/guake/dropcommit/', follow_redirects=True)
            self.assertEqual(output.status_code, 405)

        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/guake/')
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]
            data = {'csrf_token': csrf_token}

            output = self.app.post(
                '/acl/guake/dropcommit/',
                data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">ACLs updated</li>' in output.data)

            output = self.app.post(
                '/acl/random/dropcommit/',
                data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No package found by this name</li>'
                in output.data)

    @patch('pkgdb2.lib.utils.get_packagers')
    @patch('pkgdb2.fas_login_required')
    def test_update_acl(self, login_func, mock_func):
        """ Test the update_acl function. """
        login_func.return_value = None

        create_package_acl(self.session)

        user = FakeFasUser()
        mock_func.return_value = ['pingou', 'ralph', 'kevin']

        user.username = 'kevin'
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/package/guake/acl/commit/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(
                output.data.count('<td class="users">'), 1)

        # Fails `toshio` is not a packager
        user = FakeFasUser()
        user.username = 'toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.get(
                '/package/guake/acl/commit/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '</a> > Edit Commit Access</h1>' in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)
            self.assertTrue(
                '<option value="Approved">Approved' in output.data)
            self.assertEqual(
                output.data.count('class="username">'), 1)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'branch': 'master',
                'acls': '',
                'user': 'toshio',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/package/guake/acl/commit/', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">User &#34;toshio&#34; is not in the '
                'packager group</li>' in output.data)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            # Invalid package name
            output = self.app.get(
                '/package/foobar/acl/commit/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">No package of this name found.</li>'
                in output.data)

            # Invalid ACL name
            output = self.app.get(
                '/package/guake/acl/foobar/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">Invalid ACL to update.</li>'
                in output.data)

            # GET works
            output = self.app.get(
                '/package/guake/acl/commit/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '</a> > Edit Commit Access</h1>' in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)
            self.assertTrue(
                '<option value="Approved">Approved' in output.data)
            self.assertEqual(
                output.data.count('class="username">'), 2)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'branches': 'master',
                'acl': 'commit',
                'acl_status': 'Approved',
                'csrf_token': csrf_token,
            }

            # No user provided, so we don't know for who to update the ACLs
            output = self.app.post(
                '/package/guake/acl/commit/', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">Invalid input submitted</li>'
                in output.data)

        mock_func.return_value = ['pingou', 'ralph', 'toshio']

        user = FakeFasUser()
        user.username = 'toshio'
        with user_set(pkgdb2.APP, user):
            # Get works
            output = self.app.get(
                '/package/guake/acl/commit/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '</a> > Edit Commit Access</h1>' in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)
            self.assertTrue(
                '<option value="Approved">Approved' in output.data)
            self.assertEqual(
                output.data.count('class="username">'), 1)

            # Only 2 approved ACLs
            output = self.app.get(
                '/package/guake/', follow_redirects=True)
            self.assertEqual(output.data.count('title="ACL Approved"'), 2)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'branch': 'master',
                'acls': '',
                'user': 'toshio',
                'csrf_token': csrf_token,
            }

            # Toshio drops his ACL request on master
            output = self.app.post(
                '/package/guake/acl/commit/', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">toshio&#39;s commit ACL updated on '
                'master</li>' in output.data)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            data = {
                'branch': 'master',
                'acls': 'foobar',
                'user': 'toshio',
                'csrf_token': csrf_token,
            }

            # Invalid ACL status provided
            output = self.app.post(
                '/package/guake/acl/commit/', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">Invalid ACL: foobar</li>' in output.data)

            data = {
                'branch': 'master',
                'acls': 'Awaiting Review',
                'user': 'toshio',
                'csrf_token': csrf_token,
            }

            # Toshio is no longer requesting, thus is not in the list of
            # users and thus makes the request invalid
            output = self.app.post(
                '/package/guake/acl/commit/', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h4 title="`approveacls` ACL">Package Administrator(s)</h4>'
                in output.data)
            self.assertTrue(
                '<li class="error">Invalid user: toshio</li>' in output.data)

        user = FakeFasUser()
        user.username = 'toshio'
        with user_set(pkgdb2.APP, user):
            # Toshio asks for commit on master
            data = {
                'branch': 'master',
                'acls': 'Awaiting Review',
                'user': 'toshio',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/package/guake/acl/commit/', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">toshio&#39;s commit ACL updated on '
                'master</li>' in output.data)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            # Invalid branch
            data = {
                'branch': 'foo',
                'acls': '',
                'user': 'toshio',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/package/guake/acl/commit/', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Nothing to update' in output.data)

            # Nothing to change
            data = {
                'branch': 'master',
                'acls': 'Awaiting Review',
                'user': 'toshio',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/package/guake/acl/commit/', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Nothing to update' in output.data)

            # Nothing to change (2)
            data = {
                'branch': 'f18',
                'acls': '',
                'user': 'toshio',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/package/guake/acl/commit/', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Nothing to update' in output.data)

            # package admin cannot remove the user's ACL
            data = {
                'branch': 'master',
                'acls': '',
                'user': 'toshio',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/package/guake/acl/commit/', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">Only the user can remove his/her '
                'ACL</li>' in output.data)

            # package admin grants commit to Toshio on master
            data = {
                'branch': 'master',
                'acls': 'Approved',
                'user': 'toshio',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/package/guake/acl/commit/', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">toshio&#39;s commit ACL updated on '
                'master</li>' in output.data)
            # One more approved ACL
            self.assertTrue(output.data.count('title="ACL Approved"'), 3)

    @patch('pkgdb2.packager_login_required')
    def test_pending_acl(self, login_func):
        """ Test the pending_acl function. """
        login_func.return_value = None

        create_package_acl(self.session)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/acl/pending/')
            self.assertTrue('<table id="pending">' in output.data)
            self.assertTrue(
                '<a href="/package/guake/acl/commit/">' in output.data)
            self.assertTrue(
                '<input type="submit" value="Update"/>' in output.data)

    @patch('pkgdb2.lib.utils.get_packagers')
    @patch('pkgdb2.packager_login_required')
    def test_pending_acl_approve(self, login_func, mock_func):
        """ Test the pending_acl_approve function. """
        login_func.return_value = None

        create_package_acl(self.session)
        mock_func.return_value = ['pingou', 'ralph', 'kevin', 'toshio']

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/acl/pending/')
            self.assertTrue('<table id="pending">' in output.data)
            self.assertTrue(
                '<a href="/package/guake/acl/commit/">' in output.data)
            self.assertTrue(
                '<input type="submit" value="Update"/>' in output.data)

            # No CSRF provided
            output = self.app.post(
                '/acl/pending/approve', follow_redirects=True)
            self.assertTrue('<table id="pending">' in output.data)
            self.assertTrue(
                '<a href="/package/guake/acl/commit/">' in output.data)
            self.assertTrue(
                '<input type="submit" value="Update"/>' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Valid request
            data = {'csrf_token': csrf_token}
            output = self.app.post(
                '/acl/pending/approve', data=data, follow_redirects=True)
            self.assertTrue(
                '<li class="message">All ACLs approved</li>' in output.data)
            self.assertFalse('<table id="pending">' in output.data)
            self.assertFalse(
                '<a href="/package/guake/acl/commit/">' in output.data)
            self.assertFalse(
                '<input type="submit" value="Update"/>' in output.data)

    @patch('pkgdb2.lib.utils.get_packagers')
    @patch('pkgdb2.packager_login_required')
    def test_pending_acl_deny(self, login_func, mock_func):
        """ Test the pending_acl_deny function. """
        login_func.return_value = None

        create_package_acl(self.session)
        mock_func.return_value = ['pingou', 'ralph', 'kevin', 'toshio']

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/acl/pending/')
            self.assertTrue('<table id="pending">' in output.data)
            self.assertTrue(
                '<a href="/package/guake/acl/commit/">' in output.data)
            self.assertTrue(
                '<input type="submit" value="Update"/>' in output.data)

            # No CSRF provided
            output = self.app.post(
                '/acl/pending/deny', follow_redirects=True)
            self.assertTrue('<table id="pending">' in output.data)
            self.assertTrue(
                '<a href="/package/guake/acl/commit/">' in output.data)
            self.assertTrue(
                '<input type="submit" value="Update"/>' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Valid request
            data = {'csrf_token': csrf_token}
            output = self.app.post(
                '/acl/pending/deny', data=data, follow_redirects=True)
            self.assertTrue(
                '<li class="message">All ACLs denied</li>' in output.data)
            self.assertFalse('<table id="pending">' in output.data)
            self.assertFalse(
                '<a href="/package/guake/acl/commit/">' in output.data)
            self.assertFalse(
                '<input type="submit" value="Update"/>' in output.data)

    @patch('pkgdb2.lib.utils.get_packagers')
    @patch('pkgdb2.fas_login_required')
    def test_package_give_acls(self, login_func, mock_func):
        """ Test the package_give_acls function. """
        login_func.return_value = None

        create_package_acl(self.session)

        user = FakeFasUser()
        mock_func.return_value = ['pingou', 'ralph', 'kevin']

        with user_set(pkgdb2.APP, user):
            output = self.app.get('/acl/guake/give/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Give ACLs on package: guake</h1>' in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)
            self.assertTrue(
                '<option value="approveacls">approveacls' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'branches': 'master',
                'acl': 'watchbugzilla',
                'user': 'kevin',
                'acl_status': 'Approved',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/acl/guake/give/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="message">ACLs updated</li>' in
                            output.data)

        user.username = 'Toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/acl/foo/give/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No package found by this name</li>'
                in output.data)
            self.assertTrue('<h1>Search packages</h1>' in output.data)

            output = self.app.get('/acl/guake/give/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Give ACLs on package: guake</h1>' in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)
            self.assertTrue(
                '<option value="approveacls">approveacls' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'branches': 'master',
                'acl': 'commit',
                'user': 'kevin',
                'acl_status': 'Approved',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/acl/guake/give/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                'class="error">You are not allowed to update ACLs of someone '
                'else.</li>' in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskUiAclsTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
