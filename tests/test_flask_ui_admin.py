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


class FlaskUiAdminTest(Modeltests):
    """ Flask tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskUiAdminTest, self).setUp()

        pkgdb2.APP.config['TESTING'] = True
        pkgdb2.SESSION = self.session
        pkgdb2.ui.SESSION = self.session
        pkgdb2.ui.acls.SESSION = self.session
        pkgdb2.ui.admin.SESSION = self.session
        pkgdb2.ui.collections.SESSION = self.session
        pkgdb2.ui.packagers.SESSION = self.session
        pkgdb2.ui.packages.SESSION = self.session
        self.app = pkgdb2.APP.test_client()

    @patch('pkgdb2.is_admin')
    def test_admin(self, login_func):
        """ Test the admin function. """
        login_func.return_value = None

        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Admin interface</h1>' in output.data)

    @patch('pkgdb2.is_admin')
    def test_admin_log(self, login_func):
        """ Test the admin_log function. """
        login_func.return_value = None

        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/admin/log/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Logs</h1>' in output.data)
            self.assertTrue(
                'Restrict to package: <input type="text" name="package" />'
                in output.data)

            output = self.app.get(
                '/admin/log/?page=abc&limit=def&from_date=ghi&package=test')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Logs</h1>' in output.data)
            self.assertTrue(
                'Restrict to package: <input type="text" name="package" />'
                in output.data)
            self.assertTrue(
                'class="errors">Incorrect limit provided, using default</'
                in output.data)
            self.assertTrue(
                'class="errors">Incorrect from_date provided, using default</'
                in output.data)
            self.assertTrue(
                '<li class="errors">No package exists</li>' in output.data)

            output = self.app.get('/admin/log/?from_date=2013-10-19')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Logs</h1>' in output.data)
            self.assertTrue(
                'Restrict to package: <input type="text" name="package" />'
                in output.data)
            self.assertTrue('<table>\n\n</table>' in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskUiAdminTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
