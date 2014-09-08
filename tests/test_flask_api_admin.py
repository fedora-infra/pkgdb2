# -*- coding: utf-8 -*-
#
# Copyright © 2014  Red Hat, Inc.
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
pkgdb tests for the admin section of the Flask API.
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


class FlaskApiAdminTest(Modeltests):
    """ Flask API admin tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskApiAdminTest, self).setUp()

        pkgdb2.APP.config['TESTING'] = True
        pkgdb2.SESSION = self.session
        pkgdb2.api.admin.SESSION = self.session
        pkgdb2.ui.packages.SESSION = self.session
        self.app = pkgdb2.APP.test_client()

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_api_admin_actions(self, login_func, mock_func):
        """ Test the api_admin_actions function.  """

        output = self.app.get('/api/admin/actions/')
        data = json.loads(output.data)
        self.assertEqual(data['actions'], [])
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['page_total'], 1)
        self.assertEqual(data['output'], 'notok')
        self.assertEqual(
            data['error'], 'No actions found for these parameters')

        output = self.app.get('/api/admin/actions/?page=abc&limit=abcd')
        data = json.loads(output.data)
        self.assertEqual(data['actions'], [])
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['page_total'], 1)
        self.assertEqual(data['output'], 'notok')
        self.assertEqual(
            data['error'], 'No actions found for these parameters')

        # Unretire the package
        from test_flask_ui_packages import FlaskUiPackagesTest
        test = FlaskUiPackagesTest('test_package_unretire')
        test.session = self.session
        test.app = self.app
        test.test_package_unretire()

        output = self.app.get('/api/admin/actions/?page=2&limit=1')
        data = json.loads(output.data)
        self.assertEqual(data['actions'], [])
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['page_total'], 1)
        self.assertEqual(data['output'], 'notok')
        self.assertEqual(
            data['error'], 'No actions found for these parameters')

        output = self.app.get('/api/admin/actions/?package=guake')
        data = json.loads(output.data)
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['page_total'], 1)
        self.assertEqual(len(data['actions']), 1)
        self.assertEqual(data['actions'][0]['action'], 'request.unretire')
        self.assertEqual(
            data['actions'][0]['collection']['branchname'], 'f18')
        self.assertEqual(data['actions'][0]['package']['name'], 'guake')
        self.assertEqual(data['actions'][0]['package']['acls'], [])
        self.assertEqual(data['output'], 'ok')
        self.assertFalse('error' in data)

        output = self.app.get('/api/admin/actions/?status=Awaiting Review')
        data = json.loads(output.data)
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['page_total'], 1)
        self.assertEqual(len(data['actions']), 1)
        self.assertEqual(data['actions'][0]['action'], 'request.unretire')
        self.assertEqual(
            data['actions'][0]['collection']['branchname'], 'f18')
        self.assertEqual(data['actions'][0]['package']['name'], 'guake')
        self.assertEqual(data['actions'][0]['package']['acls'], [])
        self.assertEqual(data['output'], 'ok')
        self.assertFalse('error' in data)

        output = self.app.get('/api/admin/actions/?action=request.unretire')
        data = json.loads(output.data)
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['page_total'], 1)
        self.assertEqual(len(data['actions']), 1)
        self.assertEqual(data['actions'][0]['action'], 'request.unretire')
        self.assertEqual(
            data['actions'][0]['collection']['branchname'], 'f18')
        self.assertEqual(data['actions'][0]['package']['name'], 'guake')
        self.assertEqual(data['actions'][0]['package']['acls'], [])
        self.assertEqual(data['output'], 'ok')
        self.assertFalse('error' in data)

        output = self.app.get('/api/admin/actions/?packager=pingou')
        data = json.loads(output.data)
        self.assertEqual(data['actions'], [])
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['page_total'], 1)
        self.assertEqual(data['output'], 'notok')
        self.assertEqual(
            data['error'], 'No actions found for these parameters')


    @patch('pkgdb2.is_admin')
    def test_api_admin_action_edit_status(self, login_func):
        """ Test the api_admin_action_edit_status function.  """
        login_func.return_value = None

        # Redirect as you are not admin
        user = FakeFasUser()

        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/admin/action/status')
            self.assertEqual(output.status_code, 302)

        user = FakeFasUserAdmin()

        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/admin/action/status')
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
                    'id: This field is required.',
                    'status: Not a valid choice',
                ]
            )

        data = {
            'id': 'foo',
            'status': 'Approved',
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/admin/action/status', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "Invalid input submitted",
                    "error_detail": [
                        "id: Field must contain a number",
                    ],
                    "output": "notok"
                }

            )

        # Have another test create a pending Admin Action
        from test_flask_ui_packages import FlaskUiPackagesTest
        uitest = FlaskUiPackagesTest('test_package_request_branch')
        uitest.session = self.session
        uitest.app = self.app
        uitest.test_package_request_branch()

        # Before edit:
        output = self.app.get('/api/admin/actions/')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(len(data['actions']), 1)
        action = data['actions'][0]
        self.assertEqual(action['action'], "request.branch")
        self.assertEqual(action['id'], 1)
        self.assertEqual(action['from_collection']['branchname'], 'master')
        self.assertEqual(action['collection']['branchname'], 'el6')
        self.assertEqual(action['package']['name'], 'guake')
        self.assertEqual(action['user'], 'pingou')

        data = {
            'id': 1,
            'status': 'Approved',
        }

        # User is not an admin
        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/admin/action/status', data=data)
            self.assertEqual(output.status_code, 302)

        # User is an admin
        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):

            data = {
                'id': 10,
                'status': 'Approved',
            }

            # Wrong identifier
            output = self.app.post('/api/admin/action/status', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "No Admin action with this identifier found",
                    "output": "notok"
                }
            )

            data = {
                'id': 1,
                'status': 'Approved',
            }

            # All good
            output = self.app.post('/api/admin/action/status', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "messages": [
                        "user: admin updated action: 1 from Awaiting "
                        "Review to Approved"
                    ],
                    "output": "ok"
                }
            )

        # After edit:
        output = self.app.get('/api/admin/actions')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(len(data['actions']), 1)
        action = data['actions'][0]
        self.assertEqual(action['action'], "request.branch")
        self.assertEqual(action['id'], 1)
        self.assertEqual(action['from_collection']['branchname'], 'master')
        self.assertEqual(action['collection']['branchname'], 'el6')
        self.assertEqual(action['package']['name'], 'guake')
        self.assertEqual(action['user'], 'pingou')



if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskApiAdminTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
