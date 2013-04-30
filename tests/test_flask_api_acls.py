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

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import pkgdb
from pkgdb.lib import model
from tests import (Modeltests, FakeFasUser, create_package_acl)


class FlaskApiAclsTest(Modeltests):
    """ Flask API ACLs tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskApiAclsTest, self).setUp()

        pkgdb.APP.config['TESTING'] = True
        pkgdb.SESSION = self.session
        pkgdb.api.acls.SESSION = self.session
        self.app = pkgdb.APP.test_client()

    def test_acl_get(self):
        """ Test the api_acl_get function.  """
        output = self.app.get('/api/package/acl/get/guake')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/api/package/acl/get/guake/')
        self.assertEqual(output.status_code, 500)
        self.assertEqual(output.data,
                         '{\n  "output": "notok",\n  '
                         '"error": "No package found with name '
                         '\\"guake\\""\n}')

        output = self.app.get('/api/package/acl/get/')
        self.assertEqual(output.status_code, 500)
        self.assertEqual(output.data,
                         '{\n  "output": "notok",\n  '
                         '"error": "No package provided"\n}')

        create_package_acl(self.session)

        output = self.app.get('/api/package/acl/get/guake/')
        self.assertEqual(output.status_code, 200)
        output = json.loads(output.data)
        self.assertEqual(output.keys(),
                         ['acls'])
        self.assertEqual(len(output['acls']), 2)
        self.assertEqual(output['acls'][0]['collection']['branchname'],
                         'F-18')
        self.assertEqual(output['acls'][0]['point_of_contact'],
                         'user://pingou')
        self.assertEqual(output['acls'][1]['collection']['branchname'],
                         'devel')
        self.assertEqual(output['acls'][1]['point_of_contact'],
                         'user://pingou')

    def test_acl_update(self):
        """ Test the api_acl_update function.  """
        output = self.app.post('/api/package/acl')
        self.assertEqual(output.status_code, 301)

        output = self.app.post('/api/package/acl/')
        self.assertEqual(output.status_code, 500)
        self.assertEqual(output.data,
                         '{\n  "output": "notok",\n  '
                         '"error_detail": [\n    '
                         '"pkg_acl: Not a valid choice",\n    '
                         '"pkg_status: Not a valid choice",\n    '
                         '"pkg_name: This field is required.",\n    '
                         '"pkg_user: This field is required.",\n    '
                         '"pkg_branch: This field is required."\n  ],\n  '
                         '"error": "Invalid input submitted"\n}')

    def test_acl_reassign(self):
        """ Test the api_acl_reassign function. """
        output = self.app.post('/api/package/acl/reassign')
        self.assertEqual(output.status_code, 301)

        output = self.app.post('/api/package/acl/reassign/')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data,
                         '{}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskApiAclsTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
