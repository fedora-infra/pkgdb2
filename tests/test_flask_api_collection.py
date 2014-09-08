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
pkgdb tests for the Flask API regarding collections.
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
            output = self.app.post('/api/collection/f18/status/')
            self.assertEqual(output.status_code, 302)

        user = FakeFasUserAdmin()

        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/collection/f18/status/')
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                sorted(data),
                ['error', 'error_detail', 'output']
            )
            self.assertEqual(
                data['error'], "Invalid input submitted")

            self.assertEqual(
                data['output'], "notok")

            self.assertEqual(
                sorted(data['error_detail']),
                [
                    "branch: This field is required.",
                    "clt_status: Not a valid choice",
                ]
            )

        data = {'branch': 'f18',
                'clt_status': 'EOL'}
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/collection/f19/status/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "output": "notok",
                    "error": "You're trying to update the wrong collection",
                }
            )

        data = {'branch': 'f18',
                'clt_status': 'EOL'}
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/collection/f18/status', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "output": "notok",
                    "error": 'Could not find collection "f18"',
                }
            )

        create_collection(self.session)

        data = {'branch': 'f18',
                'clt_status': 'EOL'}
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/collection/f18/status', data=data)
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
        output = self.app.get('/api/collections/f*')
        self.assertEqual(output.status_code, 200)

        output = self.app.get('/api/collections/f*/')
        self.assertEqual(output.status_code, 200)
        output = json.loads(output.data)
        self.assertEqual(output,
                         {"collections": [], "output": "ok"})

        output = self.app.get('/api/collections/f*/')
        self.assertEqual(output.status_code, 200)
        output = json.loads(output.data)
        self.assertEqual(output,
                         {"collections": [], "output": "ok"})

        create_collection(self.session)

        output = self.app.get('/api/collections/')
        self.assertEqual(output.status_code, 200)
        output = json.loads(output.data)
        self.assertEqual(sorted(output.keys()),
                         ['collections', 'output'])
        self.assertEqual(len(output['collections']), 5)
        self.assertEqual(set(output['collections'][0].keys()),
                         set(['branchname', 'version', 'name', 'status',
                              'dist_tag', 'koji_name']))

        output = self.app.get('/api/collections/f*/')
        self.assertEqual(output.status_code, 200)
        output = json.loads(output.data)
        self.assertEqual(sorted(output.keys()),
                         ['collections', 'output'])
        self.assertEqual(set(output['collections'][0].keys()),
                         set(['branchname', 'version', 'name', 'status',
                              'dist_tag', 'koji_name']))
        self.assertEqual(len(output['collections']), 2)
        self.assertEqual(output['collections'][0]['name'], 'Fedora')
        self.assertEqual(output['collections'][0]['version'], '17')

        output = self.app.get('/api/collections/f*/?clt_status=EOL')
        self.assertEqual(output.status_code, 200)
        output = json.loads(output.data)
        self.assertEqual(sorted(output.keys()),
                         ['collections', 'output'])
        self.assertEqual(output['collections'], [])

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
            self.assertEqual(
                data,
                {
                    "error": "Invalid input submitted",
                    "error_detail": [
                        "dist_tag: This field is required.",
                        "version: This field is required.",
                        "clt_status: Not a valid choice",
                        "kojiname: This field is required.",
                        "clt_name: This field is required.",
                        "branchname: This field is required.",
                    ],
                    "output": "notok",
                }
            )

        data = {
            'clt_name': 'Fedora EPEL',
            'version': '6',
            'branchname': 'EL-6',
            'clt_status': 'ACTIVE',
            'dist_tag': '.el6',
            'kojiname': 'epel6'
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
                        "clt_status: Not a valid choice"
                    ],
                    "output": "notok"
                }
            )

        # Need to find out how to set flask.g.fas_user
        data = {
            'clt_name': 'Fedora EPEL',
            'version': '6',
            'branchname': 'EL-6',
            'clt_status': 'Active',
            'dist_tag': '.el6',
            'kojiname': 'epel6'
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
