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
from tests import (Modeltests, FakeFasUser, create_collection)


class FlaskApiCollectionTest(Modeltests):
    """ Flask API Collection tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskApiCollectionTest, self).setUp()

        pkgdb.APP.config['TESTING'] = True
        pkgdb.SESSION = self.session
        pkgdb.api.collections.SESSION = self.session
        self.app = pkgdb.APP.test_client()

    def test_collection_status(self):
        """ Test the api_collection_status function.  """

        output = self.app.post('/api/collection/F-18/status/')
        self.assertEqual(output.status_code, 500)
        self.assertEqual(output.data,
                         '{\n  "output": "notok",\n  '
                         '"error_detail": [\n    '
                         '"collection_status: Not a valid choice",\n    '
                         '"collection_branchname: This field is required."'
                         '\n  ],\n  "error": "Invalid input submitted"\n}')

        data = {'collection_branchname': 'F-18',
                'collection_status' : 'EOL'}
        output = self.app.post('/api/collection/F-19/status/', data=data)
        self.assertEqual(output.status_code, 500)
        self.assertEqual(output.data,
                         '{\n  "output": "notok",\n  '
                         '"error": "You\'re trying to update the wrong '
                         'collection"\n}')
        data = {'collection_branchname': 'F-18',
                'collection_status' : 'EOL'}
        output = self.app.post('/api/collection/F-18/status', data=data)
        self.assertEqual(output.status_code, 500)
        self.assertEqual(output.data,
                         '{\n  "output": "notok",\n  '
                         '"error": "You are now allowed to edit collections"\n}')

        create_collection(self.session)

        #data = {'collection_branchname': 'F-18',
                #'collection_status' : 'EOL'}
        #output = self.app.post('/api/collection/F-18/status', data=data)
        #self.assertEqual(output.status_code, 200)
        #output = json.loads(output.data)
        #self.assertEqual(output.keys(),
                         #['output', 'messages'])
        #self.assertEqual(output['output'], 'ok')
        #self.assertEqual(len(output['messages']), 1)
        #self.assertEqual(output['messages'][0],
                         #'Collection updated to "EOL"')


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
        self.assertEqual(output['collections'][0].keys(),
                         ['pendingurltemplate', 'publishurltemplate',
                          'version', 'name'])

        output = self.app.get('/api/collections/F-*/')
        self.assertEqual(output.status_code, 200)
        output = json.loads(output.data)
        self.assertEqual(output.keys(),
                         ['collections'])
        self.assertEqual(output['collections'][0].keys(),
                         ['pendingurltemplate', 'publishurltemplate',
                          'version', 'name'])
        self.assertEqual(len(output['collections']), 2)
        self.assertEqual(output['collections'][0]['name'], 'Fedora')
        self.assertEqual(output['collections'][0]['version'], '17')

    def test_collection_new(self):
        """ Test the api_collection_new function.  """

        output = self.app.post('/api/collection/new/')
        self.assertEqual(output.status_code, 500)
        self.assertEqual(output.data,
                         '{\n  "output": "notok",\n  '
                         '"error_detail": [\n    '
                         '"collection_status: Not a valid choice",\n    '
                         '"collection_name: This field is required.",\n    '
                         '"collection_branchname: This field is required.",\n    '
                         '"collection_distTag: This field is required.",\n    '
                         '"collection_version: This field is required."\n  ],\n  '
                         '"error": "Invalid input submitted"\n}')

        data = {
            'collection_name':'EPEL',
            'collection_version':'6',
            'collection_branchname':'EL-6',
            'collection_status':'ACTIVE',
            'collection_distTag':'.el6',
        }
        output = self.app.post('/api/collection/new/', data=data)
        self.assertEqual(output.status_code, 500)
        output = json.loads(output.data)
        self.assertEqual(output.keys(),
                         ['output', 'error_detail', 'error'])
        self.assertEqual(output['output'], 'notok')
        self.assertEqual(output['error'], 'Invalid input submitted')
        self.assertEqual(output['error_detail'],
                         ['collection_status: Not a valid choice'])

        ## Need to find out how to set flask.g.fas_user
        #data = {
            #'collection_name':'EPEL',
            #'collection_version':'6',
            #'collection_branchname':'EL-6',
            #'collection_status':'Active',
            #'collection_distTag':'.el6',
        #}
        #output = self.app.post('/api/collection/new/', data=data)
        #print output.data
        #self.assertEqual(output.status_code, 500)
        #output = json.loads(output.data)
        #self.assertEqual(output.keys(),
                         #['error', 'error_detail', 'output'])


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskApiCollectionTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
