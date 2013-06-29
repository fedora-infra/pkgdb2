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
pkgdb tests for the Flask API regarding packagers.
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
from tests import Modeltests, FakeFasUser, create_package_acl


class FlaskApiPackagersTest(Modeltests):
    """ Flask API Packagers tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskApiPackagersTest, self).setUp()

        pkgdb.APP.config['TESTING'] = True
        pkgdb.SESSION = self.session
        pkgdb.api.packagers.SESSION = self.session
        self.app = pkgdb.APP.test_client()

    def test_packager_acl(self):
        """ Test the api_packager_acl function.  """
        output = self.app.get('/api/packager/acl/pingou')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/api/packager/acl/')
        self.assertEqual(output.status_code, 500)
        self.assertEqual(output.data,
                         '{\n  "output": "notok",\n  '
                         '"error": "Invalid request"\n}')

        output = self.app.get('/api/packager/acl/pingou/')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data,
                         '{\n  "output": "ok",\n  "acls": []\n}')

        create_package_acl(self.session)

        output = self.app.get('/api/packager/acl/pingou/')
        self.assertEqual(output.status_code, 200)
        output = json.loads(output.data)
        self.assertEqual(output.keys(),
                         ['output', 'acls'])
        self.assertEqual(output['output'], 'ok')
        self.assertEqual(len(output['acls']), 4)
        self.assertEqual(output['acls'][0].keys(),
                         ['status', 'fas_name', 'packagelist', 'acl'])
        self.assertEqual(output['acls'][0]['packagelist'].keys(),
                         ['package', 'collection', 'point_of_contact'])
        self.assertEqual(output['acls'][0]['packagelist']['package'].keys(),
                         ['upstreamurl', 'name', 'reviewurl', 'summary'])
        self.assertEqual(output['acls'][0]['packagelist']['collection'].keys(),
                         ['pendingurltemplate', 'publishurltemplate',
                          'branchname', 'version', 'name'])
        self.assertEqual(
            output['acls'][0]['packagelist']['package']['name'], 'guake')
        self.assertEqual(
            output['acls'][0]['packagelist']['collection']['branchname'],
            'F-18')


    def test_packager_list(self):
        """ Test the api_packager_list function.  """
        output = self.app.get('/api/packager/list/pin*')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/api/packager/list/')
        self.assertEqual(output.status_code, 500)
        self.assertEqual(output.data,
                         '{\n  "output": "notok",\n  '
                         '"error": "Invalid request"\n}')

        output = self.app.get('/api/packager/list/pin*/')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data,
                         '{\n  "output": "ok",\n  "packagers": []\n}')

        create_package_acl(self.session)

        output = self.app.get('/api/packager/list/pin*/')
        self.assertEqual(output.status_code, 200)
        output = json.loads(output.data)
        self.assertEqual(output.keys(),
                         ['output', 'packagers'])
        self.assertEqual(output['output'], 'ok')
        self.assertEqual(len(output['packagers']), 1)
        self.assertEqual(output['packagers'][0], 'user::pingou')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskApiPackagersTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
