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
from pkgdb2.lib import model
from tests import (Modeltests, FakeFasUser, FakeFasUserAdmin,
                   create_collection, user_set)


class FlaskApiCollectionTest(Modeltests):
    """ Flask API Collection tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskApiCollectionTest, self).setUp()

        pkgdb2.APP.config['TESTING'] = True
        pkgdb2.SESSION = self.session
        pkgdb2.api.collections.SESSION = self.session
        self.app = pkgdb2.APP.test_client()

    @patch('pkgdb2.packager_login_required')
    def test_collection_status(self, login_func):
        """ Test the api_collection_status function.  """
        login_func.return_value = None

        # Redirect as you are not admin
        user = FakeFasUser()

        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/collection/F-18/status/')
            self.assertEqual(output.status_code, 302)

        user = FakeFasUserAdmin()

        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/collection/F-18/status/')
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "output": "notok",
                    "error_detail": [
                        "collection_status: Not a valid choice",
                        "collection_branchname: This field is required.",
                    ],
                    "error": "Invalid input submitted",
                }
            )

        data = {'collection_branchname': 'F-18',
                'collection_status': 'EOL'}
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/collection/F-19/status/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "output": "notok",
                    "error": "You're trying to update the wrong collection",
                }
            )

        data = {'collection_branchname': 'F-18',
                'collection_status': 'EOL'}
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/collection/F-18/status', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "output": "notok",
                    "error": 'Could not find collection "F-18"',
                }
            )

        create_collection(self.session)

        data = {'collection_branchname': 'F-18',
                'collection_status': 'EOL'}
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/collection/F-18/status', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "output": "ok",
                    "messages": [
                        'Collection updated from "Active" to \"EOL\"'
                    ],
                }
            )

    def test_collection_list(self):
        """ Test the api_collection_list function.  """
        output = self.app.get('/api/collections/F-*')
        self.assertEqual(output.status_code, 200)

        output = self.app.get('/api/collections/F-*/')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data,
                         '{\n  "collections": []\n}')

        output = self.app.get('/api/collections/F-*/')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data,
                         '{\n  "collections": []\n}')

        create_collection(self.session)

        output = self.app.get('/api/collections/')
        self.assertEqual(output.status_code, 200)
        output = json.loads(output.data)
        self.assertEqual(output.keys(),
                         ['collections'])
        self.assertEqual(len(output['collections']), 4)
        self.assertEqual(set(output['collections'][0].keys()),
                         set(['branchname', 'version', 'name', 'status']))

        output = self.app.get('/api/collections/F-*/')
        self.assertEqual(output.status_code, 200)
        output = json.loads(output.data)
        self.assertEqual(output.keys(),
                         ['collections'])
        self.assertEqual(set(output['collections'][0].keys()),
                         set(['branchname', 'version', 'name', 'status']))
        self.assertEqual(len(output['collections']), 2)
        self.assertEqual(output['collections'][0]['name'], 'Fedora')
        self.assertEqual(output['collections'][0]['version'], '17')

    @patch('pkgdb2.packager_login_required')
    def test_collection_new(self, login_func):
        """ Test the api_collection_new function.  """
        login_func.return_value = None

        # Redirect as you are not admin
        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/collection/new/')
            self.assertEqual(output.status_code, 302)

        user = FakeFasUserAdmin()

        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/collection/new/')
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            print output.data
            self.assertEqual(
                data,
                {
                    "error": "Invalid input submitted",
                    "error_detail": [
                        "collection_distTag: This field is required.",
                        "collection_status: Not a valid choice",
                        "collection_name: This field is required.",
                        "collection_branchname: This field is required.",
                        "collection_kojiname: This field is required.",
                        "collection_version: This field is required.",
                    ],
                    "output": "notok",
                }
            )

        data = {
            'collection_name': 'EPEL',
            'collection_version': '6',
            'collection_branchname': 'EL-6',
            'collection_status': 'ACTIVE',
            'collection_distTag': '.el6',
            'collection_kojiname': 'epel6'
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/collection/new/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "Invalid input submitted",
                    "error_detail": [
                        "collection_status: Not a valid choice"
                    ],
                    "output": "notok"
                }
            )

        # Need to find out how to set flask.g.fas_user
        data = {
            'collection_name': 'EPEL',
            'collection_version': '6',
            'collection_branchname': 'EL-6',
            'collection_status': 'Active',
            'collection_distTag': '.el6',
            'collection_kojiname': 'epel6'
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/collection/new/', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "messages": [
                        "Collection \"EL-6\" created"
                    ],
                    "output": "ok"
                }
            )


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskApiCollectionTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
