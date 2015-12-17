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
pkgdb tests for the Collection object.
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
import pkgdb2.lib.model as model
from tests import (Modeltests, FakeFasUser,
                   FakeFasGroupValid, create_package_acl,
                   create_package_acl2, user_set)


class PkgdbGrouptests(Modeltests):
    """ PkgdbGroup tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(PkgdbGrouptests, self).setUp()

        pkgdb2.APP.config['TESTING'] = True
        pkgdb2.SESSION = self.session
        pkgdb2.api.extras.SESSION = self.session
        pkgdb2.ui.SESSION = self.session
        pkgdb2.ui.acls.SESSION = self.session
        pkgdb2.ui.admin.SESSION = self.session
        pkgdb2.ui.collections.SESSION = self.session
        pkgdb2.ui.packagers.SESSION = self.session
        pkgdb2.ui.packages.SESSION = self.session
        self.app = pkgdb2.APP.test_client()

        # Let's make sure the cache is empty for the tests
        pkgdb2.CACHE.invalidate()

    def set_group_acls(self):
        ''' Create some Group ACLs. '''
        fedocal_pkg = model.Package.by_name(self.session, 'rpms', 'fedocal')
        devel_collec = model.Collection.by_name(self.session, 'master')
        f18_collec = model.Collection.by_name(self.session, 'f18')

        pklist_fedocal_f18 = model.PackageListing.by_pkgid_collectionid(
            self.session, fedocal_pkg.id, f18_collec.id)
        pklist_fedocal_devel = model.PackageListing.by_pkgid_collectionid(
            self.session, fedocal_pkg.id, devel_collec.id)

        packager = model.PackageListingAcl(
            fas_name='group::infra-sig',
            packagelisting_id=pklist_fedocal_f18.id,
            acl='commit',
            status='Approved',
        )
        self.session.add(packager)

        packager = model.PackageListingAcl(
            fas_name='group::infra-sig',
            packagelisting_id=pklist_fedocal_devel.id,
            acl='commit',
            status='Approved',
        )
        self.session.add(packager)

        packager = model.PackageListingAcl(
            fas_name='group::infra-sig',
            packagelisting_id=pklist_fedocal_f18.id,
            acl='watchbugzilla',
            status='Approved',
        )
        self.session.add(packager)

        packager = model.PackageListingAcl(
            fas_name='group::infra-sig',
            packagelisting_id=pklist_fedocal_devel.id,
            acl='watchbugzilla',
            status='Approved',
        )
        self.session.add(packager)

        self.session.commit()

    def test_api_bugzilla_group(self):
        """ Test the api_bugzilla function. """
        create_package_acl2(self.session)
        self.set_group_acls()

        output = self.app.get('/api/bugzilla/')
        self.assertEqual(output.status_code, 200)
        expected = """# Package Database VCS Acls
# Text Format
# Collection|Package|Description|Owner|Initial QA|Initial CCList
# Backslashes (\) are escaped as \u005c Pipes (|) are escaped as \u007c

Fedora|fedocal|A web-based calendar for Fedora|pingou||group::infra-sig,pingou
Fedora|geany|A fast and lightweight IDE using GTK2|group::gtk-sig||
Fedora|guake|Top down terminal for GNOME|pingou||spot"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/bugzilla/?format=json')
        self.assertEqual(output.status_code, 200)
        expected = {
            u'bugzillaAcls': {
                'Fedora': {
                    "fedocal": {
                        "owner": "pingou",
                        "cclist": {
                            "groups": ["@infra-sig"],
                            "people": ["pingou"]
                        },
                        "qacontact": None,
                        "summary": "A web-based calendar for Fedora"
                    },
                    'geany': {
                        'owner': '@gtk-sig',
                        'cclist': {
                            'groups': [],
                            'people': []
                        },
                        'qacontact': None,
                        'summary': 'A fast and lightweight IDE using '
                        'GTK2'
                    },
                    'guake': {
                        'owner': 'pingou',
                        'cclist': {
                            'groups': [],
                            'people': ['spot']
                        },
                        'qacontact': None,
                        'summary': 'Top down terminal for GNOME'
                    }
                }
            },
            'title': 'Fedora Package Database -- Bugzilla ACLs'
        }
        data = json.loads(output.data)
        self.assertEqual(data, expected)

    @patch('pkgdb2.lib.utils')
    @patch('pkgdb2.packager_login_required')
    def test_package_give_group(self, login_func, mock_func):
        """ Test the package_give function to a group. """
        login_func.return_value = None
        create_package_acl(self.session)

        mock_func.get_packagers.return_value = ['spot']
        group = FakeFasGroupValid()
        group.name = 'gtk-sig'
        mock_func.get_fas_group.return_value = group
        mock_func.log.return_value = ''
        user = FakeFasUser()

        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/rpms/guake/give')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Give Point of Contact of package: guake</h1>'
                in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'branches': 'master',
                'poc': 'spot',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/package/rpms/guake/give', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                'rpms/<span property="doap:name">guake</span>'
                in output.data)
            self.assertEqual(
                output.data.count('<a href="/packager/spot/">'), 2)

        user.username = 'spot'
        user.groups.append('gtk-sig')
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/package/rpms/guake/give')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Give Point of Contact of package: guake</h1>'
                in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'branches': 'master',
                'poc': 'group::gtk-sig',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/package/rpms/guake/give', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(
                output.data.count('<a href="/packager/spot/">'), 2)
            self.assertEqual(
                output.data.count('<a href="/packager/group::gtk-sig/">'),
                1)

            output = self.app.get('/package/rpms/guake/give')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Give Point of Contact of package: guake</h1>'
                in output.data)
            self.assertTrue(
                '<td><select id="branches" multiple name="branches">'
                '</select></td>'
                in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(PkgdbGrouptests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
