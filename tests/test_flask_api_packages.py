# -*- coding: utf-8 -*-
#
# Copyright © 2013-2016  Red Hat, Inc.
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
from pkgdb2 import lib as pkgdblib
from pkgdb2.lib import model
from tests import (Modeltests, FakeFasUser, FakeFasUserAdmin,
                   create_collection, create_package_acl,
                   create_package_critpath, user_set)


class FlaskApiPackagesTest(Modeltests):
    """ Flask API Packages tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskApiPackagesTest, self).setUp()

        pkgdb2.APP.config['TESTING'] = True
        pkgdb2.SESSION = self.session
        pkgdb2.api.packages.SESSION = self.session
        pkgdb2.ui.SESSION = self.session
        self.app = pkgdb2.APP.test_client()

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.is_admin')
    def test_api_package_new(self, login_func, mock_func):
        """ Test the api_package_new function.  """
        login_func.return_value = None

        # Redirect as you are not admin
        user = FakeFasUser()

        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/new/')
            self.assertEqual(output.status_code, 302)

        user = FakeFasUserAdmin()

        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/new/')
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
                    "branches: This field is required.",
                    "pkgname: This field is required.",
                    "poc: This field is required.",
                    "review_url: This field is required.",
                    "status: Not a valid choice",
                    "summary: This field is required.",
                ]
            )

        data = {
            'pkgname': 'gnome-terminal',
            'summary': 'Terminal emulator for GNOME',
            'description': 'Terminal for GNOME...',
            'review_url': 'http://bugzilla.redhat.com/1234',
            'status': '',
            'critpath': '',
            'branches': '',
            'poc': '',
            'upstream_url': '',
            'namespace': 'foo',
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/new/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "Invalid input submitted",
                    "error_detail": [
                        "status: This field is required.",
                        "namespace: Not a valid choice",
                        "branches: '' is not a valid choice for this field",
                        "poc: This field is required.",
                    ],
                    "output": "notok"
                }
            )

        data = {
            'pkgname': 'gnome-terminal',
            'summary': 'Terminal emulator for GNOME',
            'description': 'Terminal for GNOME...',
            'review_url': 'http://bugzilla.redhat.com/1234',
            'status': 'Approved',
            'branches': 'master',
            'poc': 'mclasen',
            'upstream_url': 'http://www.gnome.org/',
            'critpath': False,
            'namespace': 'rpms',
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/new/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "Invalid input submitted",
                    "error_detail": [
                        "branches: 'master' is not a valid choice for this "
                        "field"
                    ],
                    "output": "notok"
                }

            )

        create_collection(self.session)

        data = {
            'pkgname': 'gnome-terminal',
            'summary': 'Terminal emulator for GNOME',
            'description': 'Terminal for GNOME...',
            'review_url': 'http://bugzilla.redhat.com/1234',
            'status': 'Approved',
            'branches': 'master',
            'poc': 'mclasen',
            'upstream_url': 'http://www.gnome.org/',
            'critpath': False,
            'namespace': 'rpms',
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/new/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "User \"mclasen\" is not in the packager group",
                    "output": "notok"
                }
            )

        mock_func.get_packagers.return_value = ['mclasen']
        mock_func.log.return_value = ''

        data = {
            'pkgname': 'gnome-terminal',
            'summary': 'Terminal emulator for GNOME',
            'description': 'Terminal for GNOME...',
            'review_url': 'http://bugzilla.redhat.com/1234',
            'status': 'Approved',
            'branches': 'master',
            'poc': 'mclasen',
            'upstream_url': 'http://www.gnome.org/',
            'critpath': False,
            'namespace': 'rpms',
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/new/', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "messages": [
                        "Package created"
                    ],
                    "output": "ok"
                }
            )

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_api_package_orphan(self, login_func, mock_func):
        """ Test the api_package_orphan function.  """
        login_func.return_value = None

        # Redirect as you are not a packager
        user = FakeFasUser()
        user.groups = []

        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/orphan/')
            self.assertEqual(output.status_code, 302)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/orphan/')
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "Invalid input submitted",
                    "error_detail": [
                        "pkgnames: This field is required.",
                        "branches: This field is required.",
                    ],
                    "output": "notok"
                }
            )

        data = {
            'namespace': 'rpms',
            'pkgnames': 'guake',
            'branches': ['f18', 'master'],
            'poc': 'test',
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/orphan/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "No package found by this name",
                    "output": "notok"
                }
            )

        create_package_acl(self.session)
        mock_func.log.return_value = ''

        data = {
            'namespace': 'rpms',
            'pkgnames': 'guake',
            'branches': ['el4', 'f18'],
            'poc': 'test',
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/orphan/', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    'error': 'The package rpms/guake could not be found in '
                    'the collection el4.',
                    'messages': [''],
                    'output': 'ok'
                }
            )
            pkg_acl = pkgdblib.get_acl_package(
                self.session, 'rpms', 'guake')
            self.assertEqual(pkg_acl[0].collection.branchname, 'f18')
            self.assertEqual(pkg_acl[0].package.name, 'guake')
            self.assertEqual(pkg_acl[0].point_of_contact, 'orphan')
            self.assertEqual(pkg_acl[0].status, 'Orphaned')

            self.assertEqual(pkg_acl[1].collection.branchname, 'master')
            self.assertEqual(pkg_acl[1].package.name, 'guake')
            self.assertEqual(pkg_acl[1].point_of_contact, 'pingou')

        data = {
            'namespace': 'rpms',
            'pkgnames': 'guake',
            'branches': ['f18', 'master'],
            'poc': 'test',
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/orphan/', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "messages": ["", ""],
                    "output": "ok"
                }
            )
            pkg_acl = pkgdblib.get_acl_package(
                self.session, 'rpms', 'guake')
            self.assertEqual(pkg_acl[0].collection.branchname, 'f18')
            self.assertEqual(pkg_acl[0].package.name, 'guake')
            self.assertEqual(pkg_acl[0].point_of_contact, 'orphan')
            self.assertEqual(pkg_acl[0].status, 'Orphaned')

            self.assertEqual(pkg_acl[1].collection.branchname, 'master')
            self.assertEqual(pkg_acl[1].package.name, 'guake')
            self.assertEqual(pkg_acl[1].point_of_contact, 'orphan')
            self.assertEqual(pkg_acl[1].status, 'Orphaned')

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_api_package_unorphan(self, login_func, mock_func):
        """ Test the api_package_unorphan function.  """
        login_func.return_value = None

        # Redirect as you are not a packager
        user = FakeFasUser()
        user.groups = []

        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/unorphan/')
            self.assertEqual(output.status_code, 302)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/unorphan/')
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "Invalid input submitted",
                    "error_detail": [
                        "pkgnames: This field is required.",
                        "branches: This field is required.",
                        "poc: This field is required.",
                    ],
                    "output": "notok"
                }
            )

        mock_func.get_packagers.return_value = ['test']

        data = {
            'namespace': 'rpms',
            'pkgnames': 'guake',
            'branches': ['f18', 'master'],
            'poc': 'test',
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/unorphan/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "No package found by this name",
                    "output": "notok"
                }
            )

        create_package_acl(self.session)
        mock_func.log.return_value = ''

        # Unorphan a not-orphaned package
        data = {
            'namespace': 'rpms',
            'pkgnames': 'guake',
            'branches': ['f18', 'master'],
            'poc': 'test',
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/unorphan/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": [
                        'Package "rpms/guake" is not orphaned on master',
                        'Package "rpms/guake" is not orphaned on f18',
                    ],
                    "output": "notok"
                }
            )

        # Orphan the package
        data = {
            'namespace': 'rpms',
            'pkgnames': 'guake',
            'branches': ['f18', 'master'],
            'poc': 'test',
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/orphan/', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "messages": ["", ""],
                    "output": "ok"
                }
            )
            pkg_acl = pkgdblib.get_acl_package(
                self.session, 'rpms', 'guake')
            self.assertEqual(pkg_acl[0].collection.branchname, 'f18')
            self.assertEqual(pkg_acl[0].package.name, 'guake')
            self.assertEqual(pkg_acl[0].point_of_contact, 'orphan')
            self.assertEqual(pkg_acl[0].status, 'Orphaned')

            self.assertEqual(pkg_acl[1].collection.branchname, 'master')
            self.assertEqual(pkg_acl[1].package.name, 'guake')
            self.assertEqual(pkg_acl[1].point_of_contact, 'orphan')
            self.assertEqual(pkg_acl[1].status, 'Orphaned')

        # Unorphan the package for someone else
        data = {
            'namespace': 'rpms',
            'pkgnames': 'guake',
            'branches': ['f18', 'master'],
            'poc': 'test',
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/unorphan/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "You are not allowed to update ACLs of someone "
                    "else.",
                    "output": "notok"
                }
            )

        mock_func.get_packagers.return_value = ['pingou']

        # Unorphan the package on a branch where it is not
        data = {
            'namespace': 'rpms',
            'pkgnames': 'guake',
            'branches': ['el4', 'f18'],
            'poc': 'pingou',
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/unorphan/', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    'error':
                    'Package "rpms/guake" is not in the collection el4',
                    "messages": [
                        "Package rpms/guake has been unorphaned on f18 by pingou"
                    ],
                    'output': 'ok'
                }
            )

            pkg_acl = pkgdblib.get_acl_package(
                self.session, 'rpms', 'guake')
            self.assertEqual(pkg_acl[0].collection.branchname, 'f18')
            self.assertEqual(pkg_acl[0].package.name, 'guake')
            self.assertEqual(pkg_acl[0].point_of_contact, 'pingou')
            self.assertEqual(pkg_acl[0].status, 'Approved')

            self.assertEqual(pkg_acl[1].collection.branchname, 'master')
            self.assertEqual(pkg_acl[1].package.name, 'guake')
            self.assertEqual(pkg_acl[1].point_of_contact, 'orphan')
            self.assertEqual(pkg_acl[1].status, 'Orphaned')

        # Unorphan the package
        data = {
            'namespace': 'rpms',
            'pkgnames': 'guake',
            'branches': ['f18', 'master'],
            'poc': 'pingou',
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/unorphan/', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": 'Package "rpms/guake" is not orphaned on f18',
                    "messages": [
                        "Package rpms/guake has been unorphaned on master by pingou"
                    ],
                    "output": "ok"
                }
            )

            pkg_acl = pkgdblib.get_acl_package(
                self.session, 'rpms', 'guake')
            self.assertEqual(pkg_acl[0].collection.branchname, 'f18')
            self.assertEqual(pkg_acl[0].package.name, 'guake')
            self.assertEqual(pkg_acl[0].point_of_contact, 'pingou')
            self.assertEqual(pkg_acl[0].status, 'Approved')

            self.assertEqual(pkg_acl[1].collection.branchname, 'master')
            self.assertEqual(pkg_acl[1].package.name, 'guake')
            self.assertEqual(pkg_acl[1].point_of_contact, 'pingou')
            self.assertEqual(pkg_acl[1].status, 'Approved')

    @patch('pkgdb2.lib.utils.set_bugzilla_owner')
    @patch('pkgdb2.packager_login_required')
    def test_api_package_retire(self, login_func, mock_func):
        """ Test the api_package_retire function.  """
        login_func.return_value = None

        # Redirect as you are not a packager
        user = FakeFasUser()
        user.groups = []

        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/retire/')
            self.assertEqual(output.status_code, 302)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/retire/')
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "Invalid input submitted",
                    "error_detail": [
                        "pkgnames: This field is required.",
                        "branches: This field is required.",
                    ],
                    "output": "notok"
                }
            )

        data = {
            'pkgnames': 'guake',
            'branches': ['f18', 'master'],
            'poc': 'test',
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/retire/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "No package found by this name",
                    "output": "notok"
                }
            )

        create_package_acl(self.session)
        mock_func.log.return_value = ''

        data = {
            'pkgnames': 'guake',
            'branches': ['f18', 'master'],
            'poc': 'test',
        }
        # User is not an admin
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/retire/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "You are not allowed to retire the package: "
                    "rpms/guake on branch f18.",
                    "output": "notok"
                }
            )

        data = {
            'pkgnames': 'guake',
            'branches': ['master'],
            'poc': 'test',
        }
        # User is not the poc
        user.username = 'toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/retire/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "You are not allowed to retire this package.",
                    "output": "notok"
                }
            )

        # Retire the package on a non-existant branch
        user = FakeFasUser()
        data = {
            'pkgnames': 'guake',
            'branches': ['el6'],
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/retire/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "No package rpms/guake found in collection el6",
                    "output": "notok"
                }
            )

        # Check before
        output = self.app.get('/api/package/guake/')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(data.keys(), ['output', 'packages'])
        self.assertEqual(len(data['packages']), 2)
        self.assertEqual(data['output'], 'ok')
        self.assertEqual(data['packages'][0]['collection']['branchname'],
                         'f18')
        self.assertEqual(data['packages'][0]['point_of_contact'],
                         'pingou')
        self.assertEqual(data['packages'][1]['collection']['branchname'],
                         'master')
        self.assertEqual(data['packages'][1]['point_of_contact'],
                         'pingou')
        for acl in data['packages'][0]['acls']:
            self.assertEqual(acl['status'], 'Approved')

        # Retire the package
        user = FakeFasUserAdmin()
        data = {
            'pkgnames': 'guake',
            'branches': ['f18', 'master'],
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/retire/', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "messages": [
                        "user: admin updated package: guake status from: "
                        "Approved to Retired on branch: f18",
                        "user: admin updated package: guake status from: "
                        "Approved to Retired on branch: master",
                    ],
                    "output": "ok"
                }
            )

        # Check after retiring
        output = self.app.get('/api/package/guake/')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(data.keys(), ['output', 'packages'])
        self.assertEqual(len(data['packages']), 2)
        self.assertEqual(data['output'], 'ok')
        self.assertEqual(data['packages'][0]['collection']['branchname'],
                         'f18')
        self.assertEqual(data['packages'][0]['point_of_contact'],
                         'orphan')
        self.assertEqual(data['packages'][1]['collection']['branchname'],
                         'master')
        self.assertEqual(data['packages'][1]['point_of_contact'],
                         'orphan')
        for acl in data['packages'][0]['acls']:
            if acl['fas_name'] == 'group::provenpackager':
                continue
            self.assertEqual(acl['status'], 'Obsolete')

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_api_package_retire2(self, login_func, mock_func):
        """ Test a second time the api_package_retire function.  """
        login_func.return_value = None
        create_package_acl(self.session)
        mock_func.log.return_value = ''

        # Redirect as you are not a packager
        user = FakeFasUser()
        user.groups = []

        # Add the EPEL 7 collection
        collection = model.Collection(
            name='Fedora EPEL',
            version='7',
            status='Active',
            owner='kevin',
            branchname='epel7',
            dist_tag='.el7',
            allow_retire=True,
        )
        self.session.add(collection)
        self.session.commit()

        # Add guake to epel7
        guake_pkg = model.Package.by_name(self.session, 'rpms', 'guake')
        el7_collec = model.Collection.by_name(self.session, 'epel7')

        pkgltg = model.PackageListing(
            point_of_contact='pingou',
            status='Approved',
            package_id=guake_pkg.id,
            collection_id=el7_collec.id,
        )
        self.session.add(pkgltg)
        self.session.commit()

        # Check before
        output = self.app.get('/api/package/guake/')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(data.keys(), ['output', 'packages'])
        self.assertEqual(len(data['packages']), 3)
        self.assertEqual(data['output'], 'ok')
        self.assertEqual(data['packages'][0]['collection']['branchname'],
                         'f18')
        self.assertEqual(data['packages'][0]['point_of_contact'],
                         'pingou')
        self.assertEqual(data['packages'][1]['collection']['branchname'],
                         'master')
        self.assertEqual(data['packages'][1]['point_of_contact'],
                         'pingou')
        self.assertEqual(data['packages'][2]['collection']['branchname'],
                         'epel7')
        self.assertEqual(data['packages'][2]['point_of_contact'],
                         'pingou')
        for acl in data['packages'][1]['acls']:
            self.assertTrue(acl['status'] in ['Awaiting Review','Approved'])
        self.assertFalse('acls' in data['packages'][2])

        # Retire the package on an EPEL branch
        user = FakeFasUser()
        data = {
            'pkgnames': 'guake',
            'branches': ['master', 'epel7'],
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/retire/', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "messages": ["", ""],
                    "output": "ok"
                }
            )

        # Check after retiring
        output = self.app.get('/api/package/guake/')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(data.keys(), ['output', 'packages'])
        self.assertEqual(len(data['packages']), 3)
        self.assertEqual(data['output'], 'ok')
        self.assertEqual(data['packages'][0]['collection']['branchname'],
                         'f18')
        self.assertEqual(data['packages'][0]['point_of_contact'],
                         'pingou')
        self.assertEqual(data['packages'][1]['collection']['branchname'],
                         'master')
        self.assertEqual(data['packages'][1]['point_of_contact'],
                         'orphan')
        self.assertEqual(data['packages'][2]['collection']['branchname'],
                         'epel7')
        self.assertEqual(data['packages'][2]['point_of_contact'],
                         'orphan')

        for acl in data['packages'][1]['acls']:
            if acl['fas_name'] == 'group::provenpackager':
                continue
            self.assertEqual(acl['status'], 'Obsolete')
        self.assertFalse('acls' in data['packages'][2])

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_api_package_retire3(self, login_func, mock_func):
        """ Test a third time the api_package_retire function.  """
        login_func.return_value = None
        create_package_acl(self.session)
        mock_func.log.return_value = ''

        # Redirect as you are not a packager
        user = FakeFasUser()
        user.groups = []

        # Add the EPEL 7 collection
        collection = model.Collection(
            name='Fedora EPEL',
            version='7',
            status='Active',
            owner='kevin',
            branchname='epel7',
            dist_tag='.el7',
            allow_retire=True,
        )
        self.session.add(collection)
        self.session.commit()

        # Add guake to epel7
        guake_pkg = model.Package.by_name(self.session, 'rpms', 'guake')
        el7_collec = model.Collection.by_name(self.session, 'epel7')

        pkgltg = model.PackageListing(
            point_of_contact='orphan',
            status='Orphaned',
            package_id=guake_pkg.id,
            collection_id=el7_collec.id,
        )
        self.session.add(pkgltg)
        self.session.commit()

        # Retire an orphaned package on an EPEL branch
        user = FakeFasUser()
        data = {
            'pkgnames': 'guake',
            'branches': ['epel7'],
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/retire/', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "messages": [""],
                    "output": "ok"
                }
            )

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_api_package_retire4(self, login_func, mock_func):
        """ Test a fourth time the api_package_retire function.  """
        login_func.return_value = None
        create_package_acl(self.session)
        mock_func.log.return_value = ''

        # Redirect as you are not a packager
        user = FakeFasUser()
        user.groups = []

        # Add the EPEL 7 collection
        collection = model.Collection(
            name='Fedora EPEL',
            version='7',
            status='Active',
            owner='kevin',
            branchname='epel7',
            dist_tag='.el7',
            allow_retire=True,
        )
        self.session.add(collection)
        self.session.commit()

        # Add guake to epel7
        guake_pkg = model.Package.by_name(self.session, 'rpms', 'guake')
        el7_collec = model.Collection.by_name(self.session, 'epel7')

        pkgltg = model.PackageListing(
            point_of_contact='kevin',
            status='Approved',
            package_id=guake_pkg.id,
            collection_id=el7_collec.id,
        )
        self.session.add(pkgltg)
        self.session.commit()
        # No idea but access pkgltg.id later on fails with:
        # DetachedInstanceError: Instance <PackageListing at ...> is not
        # bound to a Session; attribute refresh operation cannot proceed
        pkgltg_id = pkgltg.id

        user = FakeFasUser()
        data = {
            'namespace': 'rpms',
            'pkgnames': 'guake',
            'branches': ['epel7'],
        }
        # User does not have approveacls and is not PoC on that branch
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/retire/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "You are not allowed to retire this package.",
                    "output": "notok"
                }
            )

        # Give approveacls to pingou on guake branch epel7:
        packager = model.PackageListingAcl(
            fas_name='pingou',
            packagelisting_id=pkgltg_id,
            acl='approveacls',
            status='Approved',
        )
        self.session.add(packager)
        self.session.commit()

        data = {
            'namespace': 'rpms',
            'pkgnames': 'guake',
            'branches': ['epel7'],
        }

        # Retire a package where user has `approveacls` but is not PoC
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/retire/', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "messages": [""],
                    "output": "ok"
                }
            )

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_api_package_retire5(self, login_func, mock_func):
        """ Test a fifth time the api_package_retire function.  """
        login_func.return_value = None
        create_package_acl(self.session)
        mock_func.log.return_value = ''

        # Redirect as you are not a packager
        user = FakeFasUser()
        user.groups = []

        # Add the EPEL 7 collection where we block retiring packages
        collection = model.Collection(
            name='Fedora EPEL',
            version='7',
            status='Active',
            owner='kevin',
            branchname='epel7',
            dist_tag='.el7',
            allow_retire=False,
        )
        self.session.add(collection)
        self.session.commit()

        # Add guake to epel7
        guake_pkg = model.Package.by_name(self.session, 'rpms', 'guake')
        el7_collec = model.Collection.by_name(self.session, 'epel7')

        pkgltg = model.PackageListing(
            point_of_contact='kevin',
            status='Approved',
            package_id=guake_pkg.id,
            collection_id=el7_collec.id,
        )
        self.session.add(pkgltg)
        self.session.commit()
        # No idea but access pkgltg.id later on fails with:
        # DetachedInstanceError: Instance <PackageListing at ...> is not
        # bound to a Session; attribute refresh operation cannot proceed
        pkgltg_id = pkgltg.id

        # Give approveacls to pingou on guake branch epel7:
        packager = model.PackageListingAcl(
            fas_name='pingou',
            packagelisting_id=pkgltg_id,
            acl='approveacls',
            status='Approved',
        )
        self.session.add(packager)
        self.session.commit()

        user = FakeFasUser()
        data = {
            'pkgnames': 'guake',
            'branches': ['epel7'],
        }
        # Collection does not support retiring a package
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/retire/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "You are not allowed to retire the package: "
                    "rpms/guake on branch epel7.",
                    "output": "notok"
                }
            )

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_api_package_unretire(self, login_func, mock_func):
        """ Test the api_package_unretire function.  """
        login_func.return_value = None

        # Redirect as you are not a packager
        user = FakeFasUser()
        user.groups = []

        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/unretire/')
            self.assertEqual(output.status_code, 302)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/unretire/')
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "Invalid input submitted",
                    "error_detail": [
                        "pkgnames: This field is required.",
                        "branches: This field is required.",
                    ],
                    "output": "notok"
                }
            )

        data = {
            'pkgnames': 'guake',
            'branches': ['f18', 'master'],
            'poc': 'test',
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/unretire/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "No package found by this name",
                    "output": "notok"
                }
            )

        create_package_acl(self.session)
        mock_func.log.return_value = ''

        # User is not an admin
        data = {
            'pkgnames': 'guake',
            'branches': ['f18', 'master'],
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/unretire/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "You are not allowed to update the status of "
                             "the package: rpms/guake on branch f18 to "
                             "Approved.",
                    "output": "notok"
                }
            )

        # Unretire the package
        user = FakeFasUserAdmin()
        data = {
            'pkgnames': 'guake',
            'branches': ['f18', 'master'],
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/unretire/', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "messages": ["", ""],
                    "output": "ok"
                }
            )

    def test_api_package_info(self):
        """ Test the api_package_info function.  """

        output = self.app.get('/api/package/guake/')
        self.assertEqual(output.status_code, 404)
        data = json.loads(output.data)
        self.assertEqual(
            data,
            {
                "error": "Package: rpms/guake not found",
                "output": "notok"
            }
        )

        create_package_acl(self.session)

        output = self.app.get('/api/package/guake/')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(data.keys(), ['output', 'packages'])
        self.assertEqual(len(data['packages']), 2)
        self.assertEqual(data['output'], 'ok')
        self.assertEqual(data['packages'][0]['collection']['branchname'],
                         'f18')
        self.assertEqual(data['packages'][0]['point_of_contact'],
                         'pingou')
        self.assertEqual(data['packages'][0]['package']['name'],
                         'guake')
        self.assertEqual(data['packages'][1]['collection']['branchname'],
                         'master')
        self.assertEqual(data['packages'][1]['point_of_contact'],
                         'pingou')
        self.assertEqual(data['packages'][1]['package']['name'],
                         'guake')

        output = self.app.get('/api/package/?pkgname=guake&branches=master')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(data.keys(), ['output', 'packages'])
        self.assertEqual(len(data['packages']), 1)
        self.assertEqual(data['output'], 'ok')
        self.assertEqual(
            set(data['packages'][0].keys()),
            set(['status', 'point_of_contact', 'package', 'collection',
                 'acls', 'status_change', 'critpath']))
        self.assertEqual(
            [acl['fas_name'] for acl in data['packages'][0]['acls']],
            ['pingou', 'pingou', 'pingou', 'toshio', 'ralph',
             'group::provenpackager'])
        self.assertEqual(data['packages'][0]['collection']['branchname'],
                         'master')
        self.assertEqual(data['packages'][0]['point_of_contact'],
                         'pingou')
        self.assertEqual(data['packages'][0]['package']['name'],
                         'guake')

        output = self.app.get(
            '/api/package/?pkgname=guake&branches=master&acls=0')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(data.keys(), ['output', 'packages'])
        self.assertEqual(len(data['packages']), 1)
        self.assertEqual(data['output'], 'ok')
        self.assertEqual(
            set(data['packages'][0].keys()),
            set(['status', 'point_of_contact', 'package', 'collection',
                 'status_change', 'critpath']))
        self.assertEqual(data['packages'][0]['collection']['branchname'],
                         'master')
        self.assertEqual(data['packages'][0]['point_of_contact'],
                         'pingou')
        self.assertEqual(data['packages'][0]['package']['name'],
                         'guake')

        output = self.app.get('/api/package/?pkgname=guake&branches=f19')
        self.assertEqual(output.status_code, 404)
        data = json.loads(output.data)
        self.assertEqual(
            data,
            {
                "error": "No package found on these branches: f19",
                "output": "notok"
            }
        )

    def test_api_package_list(self):
        """ Test the api_package_list function.  """

        output = self.app.get('/api/packages/guake/')
        self.assertEqual(output.status_code, 404)
        data = json.loads(output.data)
        self.assertEqual(
            data,
            {
                "error": "No packages found for these parameters",
                "packages": [],
                "output": "notok",
                "page_total": 1,
                "page": 1,
            }
        )

        create_package_acl(self.session)
        create_package_critpath(self.session)

        output = self.app.get('/api/packages/guake/')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(
            sorted(data.keys()),
            ['output', 'packages', 'page', 'page_total'])
        self.assertEqual(len(data['packages']), 1)
        self.assertEqual(data['output'], 'ok')
        self.assertEqual(
            data['packages'][0]['name'], 'guake')
        self.assertEqual(
            data['packages'][0]['status'], 'Approved')
        self.assertEqual(
            data['packages'][0]['summary'], 'Top down terminal for GNOME')

        output = self.app.get('/api/packages/g*/')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(len(data['packages']), 2)
        self.assertEqual(data['packages'][0]['acls'], [])
        self.assertEqual(data['packages'][1]['acls'], [])

        output = self.app.get('/api/packages/g*/?count=True')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(
            data,
            {
                "output": "ok",
                "packages": 2,
                "page": 1,
                "page_total": 1,
            }
        )

        # Check that we do return the ACLs when we ask them
        output = self.app.get('/api/packages/g*/?acls=True')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(
            sorted(data.keys()),
            ['output', 'packages', 'page', 'page_total'])
        self.assertEqual(len(data['packages']), 2)
        self.assertEqual(data['output'], 'ok')
        self.assertEqual(
            data['packages'][0]['name'], 'geany')
        self.assertEqual(
            data['packages'][1]['name'], 'guake')
        self.assertNotEqual(data['packages'][0]['acls'], [])
        self.assertNotEqual(data['packages'][1]['acls'], [])
        self.assertEqual(
            data['packages'][0]['acls'][0]['collection']['branchname'],
            'f18'
        )
        self.assertEqual(
            data['packages'][1]['acls'][1]['collection']['branchname'],
            'master'
        )
        self.assertEqual(
            data['packages'][1]['acls'][0].keys(),
            [
                'status', 'point_of_contact', 'collection', 'acls',
                'critpath', 'status_change',
            ]
        )

        output = self.app.get('/api/packages/g*/?limit=abc')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(
            sorted(data.keys()),
            ['output', 'packages', 'page', 'page_total'])
        self.assertEqual(len(data['packages']), 2)
        self.assertEqual(data['output'], 'ok')
        self.assertEqual(
            data['packages'][0]['name'], 'geany')
        self.assertEqual(
            data['packages'][0]['status'], 'Approved')
        self.assertEqual(
            data['packages'][1]['name'], 'guake')
        self.assertEqual(
            data['packages'][1]['status'], 'Approved')

        output = self.app.get('/api/packages/g*/?limit=5000')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(
            sorted(data.keys()),
            ['output', 'packages', 'page', 'page_total'])
        self.assertEqual(len(data['packages']), 2)
        self.assertEqual(data['output'], 'ok')
        self.assertEqual(
            data['packages'][0]['name'], 'geany')
        self.assertEqual(
            data['packages'][0]['status'], 'Approved')
        self.assertEqual(
            data['packages'][1]['name'], 'guake')
        self.assertEqual(
            data['packages'][1]['status'], 'Approved')

        output = self.app.get('/api/packages/g*/?critpath=1')
        self.assertEqual(output.status_code, 404)
        data = json.loads(output.data)
        self.assertEqual(
            sorted(data.keys()),
            ['error', 'output', 'packages', 'page', 'page_total'])
        self.assertEqual(len(data['packages']), 0)
        self.assertEqual(data['output'], 'notok')

        output = self.app.get('/api/packages/k*/?critpath=1')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(
            sorted(data.keys()),
            ['output', 'packages', 'page', 'page_total'])
        self.assertEqual(len(data['packages']), 1)
        self.assertEqual(data['packages'][0]['name'], 'kernel')
        self.assertEqual(data['output'], 'ok')

        output = self.app.get('/api/packages/g*/?critpath=0')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(
            sorted(data.keys()),
            ['output', 'packages', 'page', 'page_total'])
        self.assertEqual(len(data['packages']), 2)
        self.assertEqual(data['output'], 'ok')

        output = self.app.get('/api/packages/g*/?page=abc')
        self.assertEqual(output.status_code, 500)
        data = json.loads(output.data)
        self.assertEqual(
            sorted(data.keys()),
            ['error', 'output', 'page', 'page_total'])
        self.assertEqual(data['error'], 'Wrong page provided')
        self.assertEqual(data['output'], 'notok')

        output = self.app.get('/api/packages/g*/?orphaned=False')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(
            sorted(data.keys()),
            ['output', 'packages', 'page', 'page_total'])
        self.assertEqual(data['output'], 'ok')
        self.assertEqual(len(data['packages']), 2)
        self.assertEqual(data['packages'][0]['name'], 'geany')
        self.assertEqual(data['packages'][1]['name'], 'guake')

        output = self.app.get('/api/packages/g*/?orphaned=True')
        self.assertEqual(output.status_code, 404)
        data = json.loads(output.data)
        self.assertEqual(
            sorted(data.keys()),
            ['error', 'output', 'packages', 'page', 'page_total'])
        self.assertEqual(
            data['error'], 'No packages found for these parameters')
        self.assertEqual(data['output'], 'notok')
        self.assertEqual(data['packages'], [])

        output = self.app.get('/api/packages/?pattern=guake&pattern=geany')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(
            sorted(data.keys()),
            ['output', 'packages', 'page', 'page_total'])
        self.assertEqual(data['output'], 'ok')
        self.assertEqual(len(data['packages']), 2)
        self.assertEqual(data['packages'][0]['name'], 'geany')
        self.assertEqual(data['packages'][1]['name'], 'guake')

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.is_admin')
    def test_api_package_edit(self, login_func, mock_func):
        """ Test the api_package_edit function.  """
        login_func.return_value = None

        # Redirect as you are not admin
        user = FakeFasUser()

        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/edit/')
            self.assertEqual(output.status_code, 302)

        user = FakeFasUserAdmin()

        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/edit/')
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
                    "pkgname: This field is required.",
                ]
            )

        data = {
            'namespace': 'rpms',
            'pkgname': 'gnome-terminal',
            'summary': 'Terminal emulator for GNOME',
            'description': 'Terminal for GNOME...',
            'review_url': 'http://bugzilla.redhat.com/1234',
            'status': 'Approved',
            'upstream_url': 'http://www.gnome.org/',
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/edit/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "No package of this name found",
                    "output": "notok"
                }
            )

        create_package_acl(self.session)
        create_package_critpath(self.session)

        # Before edit:
        output = self.app.get('/api/package/guake/', data=data)
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(
            data['packages'][0]['package']['upstream_url'],
            'http://guake.org'
        )

        data = {
            'namespace': 'rpms',
            'pkgname': 'guake',
            'upstream_url': 'http://www.guake.org',
        }

        # User is not an admin
        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/edit/', data=data)
            self.assertEqual(output.status_code, 302)

        # User is an admin
        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/edit/', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "messages": ['Package "guake" edited'],
                    "output": "ok"
                }
            )

        # After edit:
        output = self.app.get('/api/package/guake/', data=data)
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(
            data['packages'][0]['package']['upstream_url'],
            'http://www.guake.org'
        )

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.is_admin')
    def test_api_package_critpath(self, login_func, mock_func):
        """ Test the api_package_critpath function.  """
        login_func.return_value = None

        # Redirect as you are not admin
        user = FakeFasUser()

        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/critpath/')
            self.assertEqual(output.status_code, 302)

        user = FakeFasUserAdmin()

        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/critpath/')
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
                    'branches: This field is required.',
                    'pkgnames: This field is required.'
                ]
            )

        data = {
            'namespace': 'rpms',
            'pkgnames': 'gnome-terminal',
            'branches': 'master'
        }
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/critpath/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "No package found by this name: "
                    "rpms/gnome-terminal",
                    "output": "notok"
                }
            )

        create_package_acl(self.session)
        create_package_critpath(self.session)

        # Before edit:
        output = self.app.get('/api/package/guake/', data=data)
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        for pkg in data['packages']:
            self.assertFalse(pkg['critpath'])
            self.assertFalse(pkg['critpath'])

        data = {
            'namespace': 'rpms',
            'pkgnames': 'guake',
            'branches': ['master', 'f18'],
        }

        # User is an admin - But not updating the critpath
        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/critpath/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "Nothing to update",
                    "output": "notok"
                }
            )

            # Still no update
            data = {
                'namespace': 'rpms',
                'pkgnames': 'guake',
                'branches': ['master', 'f18'],
                'critpath': False,
            }

            output = self.app.post('/api/package/critpath/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "Nothing to update",
                    "output": "notok"
                }
            )

        data = {
            'namespace': 'rpms',
            'pkgnames': 'guake',
            'branches': ['foobar'],
        }

        # User is an admin - But not invalid collection the critpath
        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/critpath/', data=data)
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    "error": "No collection found by the name of foobar",
                    "output": "notok"
                }
            )

        data = {
            'namespace': 'rpms',
            'pkgnames': 'guake',
            'branches': ['master', 'f18'],
            'critpath': True,
        }

        # User is an admin and updating the critpath
        user = FakeFasUserAdmin()
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/critpath/', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                    'messages': [
                        'rpms/guake: critpath updated on master to True',
                        'rpms/guake: critpath updated on f18 to True'
                    ],
                    'output': 'ok'
                }
            )

        # After edit:
        output = self.app.get('/api/package/rpms/guake/', data=data)
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        for pkg in data['packages']:
            self.assertTrue(pkg['critpath'])

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.is_admin')
    def test_api_monitor_package(self, login_func, mock_func):
        """ Test the api_monitor_package function.  """
        login_func.return_value = None

        user = FakeFasUser()

        # No package
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/rpms/guake/monitor/1')
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                sorted(data),
                ['error', 'output']
            )
            self.assertEqual(
                data['error'], "No package found by this name")

            self.assertEqual(
                data['output'], "notok")

        create_package_acl(self.session)
        create_package_critpath(self.session)

        # User is not a packager
        user.username = 'Toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/rpms/guake/monitor/1')
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                sorted(data),
                ['error', 'output']
            )
            self.assertEqual(
                data['error'],
                "You are not allowed to update the monitor flag on this "
                "package")

            self.assertEqual(
                data['output'], "notok")

        # Works
        user.username = 'pingou'
        with user_set(pkgdb2.APP, user):
            # Ensure that GETs show that it is *not* monitored
            output = self.app.get('/api/package/rpms/guake/')
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(data['packages'][0]['package']['monitor'], False)

            output = self.app.post('/api/package/rpms/guake/monitor/1')
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                sorted(data),
                ['messages', 'output']
            )
            self.assertEqual(
                data['messages'],
                "Monitoring status of rpms/guake set to True")

            self.assertEqual(
                data['output'], "ok")

            output = self.app.post('/api/package/rpms/guake/monitor/1')
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                sorted(data),
                ['messages', 'output']
            )
            self.assertEqual(
                data['messages'], "Monitoring status un-changed")

            self.assertEqual(
                data['output'], "ok")

            # Ensure that subsequent GETs show that it is monitored
            output = self.app.get('/api/package/rpms/guake/')
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(data['packages'][0]['package']['monitor'], True)

        # User is not a packager but is admin
        user = FakeFasUserAdmin()
        user.username = 'Toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/rpms/guake/monitor/False')
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                sorted(data),
                ['messages', 'output']
            )
            self.assertEqual(
                data['messages'],
                "Monitoring status of rpms/guake set to False")

            self.assertEqual(
                data['output'], "ok")

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.is_admin')
    def test_api_koschei_package(self, login_func, mock_func):
        """ Test the api_koschei_package function.  """
        login_func.return_value = None

        user = FakeFasUser()

        # No package
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/rpms/guake/koschei/1')
            self.assertEqual(output.status_code, 500)
            data = json.loads(output.data)
            self.assertEqual(
                sorted(data),
                ['error', 'output']
            )
            self.assertEqual(
                data['error'], "No package found by this name")

            self.assertEqual(
                data['output'], "notok")

        create_package_acl(self.session)
        create_package_critpath(self.session)

        # User is not a packager
        user.username = 'Toshio'
        user.groups = ['sysadmin']
        with user_set(pkgdb2.APP, user):
            output = self.app.post(
                '/api/package/rpms/guake/koschei/1', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertIn(
                '<li class="errors">You must be a packager</li>', output.data)

        # Works
        user.username = 'pingou'
        user.groups = ['packager']
        with user_set(pkgdb2.APP, user):
            # Ensure that GETs show that it is *not* monitored
            output = self.app.get('/api/package/guake/')
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data['packages'][0]['package']['koschei_monitor'], False)

            output = self.app.post('/api/package/rpms/guake/koschei/1')
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                sorted(data),
                ['messages', 'output']
            )
            self.assertEqual(
                data['messages'],
                "Koschei monitoring status of rpms/guake set to True")

            self.assertEqual(
                data['output'], "ok")

            output = self.app.post('/api/package/rpms/guake/koschei/1')
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                sorted(data),
                ['messages', 'output']
            )
            self.assertEqual(
                data['messages'], "Koschei monitoring status un-changed")

            self.assertEqual(
                data['output'], "ok")

            # Ensure that subsequent GETs show that it is monitored
            output = self.app.get('/api/package/rpms/guake/')
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data['packages'][0]['package']['koschei_monitor'], True)

        # User is not a packager but is admin
        user = FakeFasUserAdmin()
        user.username = 'Toshio'
        with user_set(pkgdb2.APP, user):
            output = self.app.post('/api/package/rpms/guake/koschei/False')
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                sorted(data),
                ['messages', 'output']
            )
            self.assertEqual(
                data['messages'],
                "Koschei monitoring status of rpms/guake set to False")

            self.assertEqual(
                data['output'], "ok")

    @patch('pkgdb2.lib.utils')
    def test_api_package_request(self, utils_mock):
        """ Test the api_package_request function.  """
        # Ensure there are no actions before
        actions = pkgdblib.search_actions(self.session)
        self.assertEqual(len(actions), 0)

        create_collection(self.session)
        user = FakeFasUser()

        with user_set(pkgdb2.APP, user):
            # Incomplete request
            data = {
                'pkgname': 'guake',
                'summary': 'Drop-down terminal for GNOME',
                'branches': ['foobar'],
            }
            output = self.app.post('/api/request/package', data=data)
            self.assertEqual(output.status_code, 400)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                  "error": "Invalid input submitted",
                  "error_detail": [
                    "branches: 'foobar' is not a valid choice for this field",
                    "review_url: This field is required."
                  ],
                  "output": "notok"
                }
            )

            # User not a packager
            data = {
                'pkgname': 'guake',
                'summary': 'Drop-down terminal for GNOME',
                'review_url': 'https://bugzilla.redhat.com/450189',
                'branches': ['master', 'f18'],
                'namespace': 'rpms',
            }
            output = self.app.post('/api/request/package', data=data)
            self.assertEqual(output.status_code, 400)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                  'error': 'User "pingou" is not in the packager group',
                  'output': 'notok'
                }
            )

            # Working - Asking for 1 branch only but getting `master` as well
            utils_mock.get_packagers.return_value = ['pingou', 'ralph']
            utils_mock.log.return_value = \
                'user: pingou request package: guake on branch <branch>'
            data = {
                'pkgname': 'guake',
                'summary': 'Drop-down terminal for GNOME',
                'review_url': 'https://bugzilla.redhat.com/450189',
                'branches': ['f18'],
                'namespace': 'rpms',
            }
            output = self.app.post('/api/request/package', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                  'messages': [
                    'user: pingou request package: guake on branch <branch>',
                    'user: pingou request package: guake on branch <branch>',
                  ],
                  'output': 'ok'
                }
            )

        actions = pkgdblib.search_actions(self.session)
        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[0].action, 'request.package')
        self.assertEqual(actions[1].action, 'request.package')
        self.assertEqual(actions[0].collection.branchname, 'f18')
        self.assertEqual(actions[1].collection.branchname, 'master')
        self.assertEqual(actions[0].package, None)
        self.assertEqual(actions[1].package, None)
        self.assertEqual(actions[0].info_data['pkg_name'], 'guake')
        self.assertEqual(actions[1].info_data['pkg_name'], 'guake')

        # Check with providing a bug number instead of the full URL
        with user_set(pkgdb2.APP, user):
            utils_mock.log.return_value = \
                'user: pingou request package: terminator on branch master'
            data = {
                'pkgname': 'terminator',
                'summary': 'Terminal for GNOME',
                'review_url': '123',
                'branches': ['master'],
                'namespace': 'rpms',
            }
            output = self.app.post('/api/request/package', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                  'messages': [
                    'user: pingou request package: terminator on branch master',
                  ],
                  'output': 'ok'
                }
            )

        actions = pkgdblib.search_actions(self.session)
        self.assertEqual(len(actions), 3)
        action = pkgdblib.get_admin_action(self.session, 3)
        self.assertEqual(action.action, 'request.package')
        self.assertEqual(action.collection.branchname, 'master')
        self.assertEqual(action.package, None)
        self.assertEqual(action.info_data['pkg_name'], 'terminator')
        self.assertEqual(
            action.info_data['pkg_review_url'],
            'https://bugzilla.redhat.com/123'
        )

        # Check with an URL not matching expectations
        with user_set(pkgdb2.APP, user):
            utils_mock.log.return_value = \
                'user: pingou request package: foo on branch master'
            data = {
                'pkgname': 'foo',
                'summary': 'bar',
                'review_url': 'http://bz.rh.c/123',
                'branches': ['master'],
                'namespace': 'rpms',
            }
            output = self.app.post('/api/request/package', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                  'messages': [
                    'user: pingou request package: foo on branch master',
                  ],
                  'output': 'ok'
                }
            )

        actions = pkgdblib.search_actions(self.session)
        self.assertEqual(len(actions), 4)
        action = pkgdblib.get_admin_action(self.session, 4)
        self.assertEqual(action.action, 'request.package')
        self.assertEqual(action.collection.branchname, 'master')
        self.assertEqual(action.package, None)
        self.assertEqual(action.info_data['pkg_name'], 'foo')
        self.assertEqual(
            action.info_data['pkg_review_url'], 'http://bz.rh.c/123')

    @patch('pkgdb2.lib.utils')
    def test_api_branch_request(self, utils_mock):
        """ Test the api_branch_request function.  """
        # Ensure there are no actions before
        actions = pkgdblib.search_actions(self.session)
        self.assertEqual(len(actions), 0)

        create_package_acl(self.session)
        user = FakeFasUser()

        with user_set(pkgdb2.APP, user):
            # Invalid package
            data = {
                'branches': ['foobar'],
            }
            output = self.app.post('/api/request/branch/rpms/foo', data=data)
            self.assertEqual(output.status_code, 404)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                  "error": "No package found: rpms/foo",
                  "output": "notok"
                }
            )

            # Invalid request
            data = {
                'branches': ['foobar'],
            }
            output = self.app.post('/api/request/branch/rpms/guake', data=data)
            self.assertEqual(output.status_code, 400)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                  "error": "Invalid input submitted",
                  "error_detail": [
                    "branches: 'foobar' is not a valid choice for this field"
                  ],
                  "output": "notok"
                }
            )

            # User not a packager
            data = {
                'branches': ['f17'],
            }
            output = self.app.post('/api/request/branch/rpms/guake', data=data)
            self.assertEqual(output.status_code, 400)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                  'error': 'User "pingou" is not in the packager group',
                  'output': 'notok'
                }
            )

            # Working - Fedora branches are directly created
            utils_mock.get_packagers.return_value = ['pingou', 'ralph']
            utils_mock.log.return_value = \
                'user: pingou request package: guake on branch <branch>'
            data = {
                'branches': ['f17'],
            }
            output = self.app.post('/api/request/branch/rpms/guake', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                  'messages': [
                    'Branch f17 created for user pingou',
                  ],
                  'output': 'ok'
                }
            )

            actions = pkgdblib.search_actions(self.session)
            self.assertEqual(len(actions), 0)

            # Working - EPEL branches go through validation
            data = {
                'branches': ['el6'],
            }
            output = self.app.post('/api/request/branch/rpms/guake', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(
                data,
                {
                  "messages": [
                    "Branch el6 requested for user pingou"
                  ],
                  "output": "ok"
                }
            )

            actions = pkgdblib.search_actions(self.session)
            self.assertEqual(len(actions), 1)
            self.assertEqual(actions[0].action, 'request.branch')
            self.assertEqual(actions[0].collection.branchname, 'el6')
            self.assertEqual(actions[0].package.name, 'guake')
            self.assertEqual(actions[0].info_data, {})


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskApiPackagesTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
