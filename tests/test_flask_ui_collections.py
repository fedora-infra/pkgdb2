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


class FlaskUiCollectionsTest(Modeltests):
    """ Flask tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskUiCollectionsTest, self).setUp()

        pkgdb2.APP.config['TESTING'] = True
        pkgdb2.SESSION = self.session
        pkgdb2.ui.SESSION = self.session
        pkgdb2.ui.acls.SESSION = self.session
        pkgdb2.ui.admin.SESSION = self.session
        pkgdb2.ui.collections.SESSION = self.session
        pkgdb2.ui.packagers.SESSION = self.session
        pkgdb2.ui.packages.SESSION = self.session
        self.app = pkgdb2.APP.test_client()

    def test_list_collections(self):
        """ Test the list_collections function. """

        output = self.app.get('/collections/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Search collections</h1>' in output.data)

        output = self.app.get('/collections/?limit=abc')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Search collections</h1>' in output.data)

    def test_collection_info(self):
        """ Test the collection_info function. """
        create_package_acl(self.session)

        output = self.app.get('/collection/devel/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Fedora devel</h1>' in output.data)

        output = self.app.get('/collection/random/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<li class="errors">No collection of this name '
                        'found.</li>' in output.data)

    @patch('pkgdb2.is_admin')
    def test_collection_new(self, login_func):
        """ Test the collection_new function. """
        login_func.return_value = None
        create_package_acl(self.session)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/new/collection/')
            self.assertEqual(output.status_code, 302)

        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/new/collection/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Create a new collection</h1>' in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'collection_name': '',
                'collection_version': '',
                'collection_status': '',
                'collection_branchname': '',
                'collection_distTag': '',
                'collection_git_branch_name': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/new/collection/', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(
                output.data.count(
                    '<td class="errors">This field is required.</td>'
                ), 6)

        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/new/collection/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Create a new collection</h1>' in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'collection_name': 'Fedora',
                'collection_version': '19',
                'collection_status': 'Active',
                'collection_branchname': 'f19',
                'collection_distTag': '.fc19',
                'collection_git_branch_name': 'f19',
                'collection_kojiname': 'f19',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/new/collection/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Collection &#34;f19&#34; created</li>'
                in output.data)

    @patch('pkgdb2.is_admin')
    def test_collection_edit(self, login_func):
        """ Test the collection_edit function. """
        login_func.return_value = None
        create_package_acl(self.session)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/collection/devel/edit')
            self.assertEqual(output.status_code, 302)

        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/collection/devel/edit')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Edit collection</h1>' in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)

        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/collection/random/edit')

            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">No collection of this name found.</li>'
                in output.data)

        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/collection/F-17/edit')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Edit collection</h1>' in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            collections = model.Collection.by_name(self.session, 'F-17')
            self.assertEqual(
                "Collection(u'Fedora', u'17', u'Active', owner:u'toshio')",
                collections.__repr__())
            self.assertEqual(collections.branchname, 'F-17')

            data = {
                'collection_name': 'Fedora',
                'collection_version': '17',
                'collection_status': 'Active',
                'collection_branchname': 'F-17',
                'collection_distTag': '.fc17',
                'collection_git_branch_name': 'f17',
                'collection_kojiname': 'f17',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/collection/F-17/edit', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Collection &#34;F-17&#34; edited</li>'
                in output.data)

            collections = model.Collection.by_name(self.session, 'F-17')
            self.assertEqual(
                "Collection(u'Fedora', u'17', u'Active', owner:u'toshio')",
                collections.__repr__())
            self.assertEqual(collections.branchname, 'F-17')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskUiCollectionsTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
