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
pkgdb tests for the PersonPackageListing object.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

from pkgdb2.lib import model
from tests import Modeltests, create_package_acl


class PackageListingAcltests(Modeltests):
    """ PackageListingAcl tests. """

    def test_init_package(self):
        """ Test the __init__ function of PackageListingAcl. """
        create_package_acl(self.session)
        self.assertEqual(7,
                         len(model.PackageListingAcl.all(self.session))
                         )

    def test_to_json(self):
        """ Test the to_json function of PackageListingAcl. """
        packager = model.PackageListingAcl.get_acl_packager(
            self.session, 'pingou')
        self.assertEqual(0, len(packager))

        create_package_acl(self.session)

        packager = model.PackageListingAcl.get_acl_packager(
            self.session, 'pingou')
        self.assertEqual(5, len(packager))
        output = packager[0].to_json()

        # Because matching times in tests is hard.
        del output['packagelist']['package']['creation_date']
        del output['packagelist']['status_change']

        target = {
            'status': u'Approved',
            'acl': 'commit',
            'fas_name': u'pingou',
            'packagelist': {
                'status': u'Approved',
                'point_of_contact': u'pingou',
                'collection': {
                    'branchname': u'F-18',
                    'version': u'18',
                    'name': u'Fedora',
                    'status': u'Active',
                },
                'package': {
                    'upstream_url': u'http://guake.org',
                    'name': u'guake',
                    'status': u'Approved',
                    'review_url': u'https://bugzilla.redhat.com/450189',
                    'summary': u'Top down terminal for GNOME',
                    'description': u'Top down terminal...',
                }
            }
        }
        self.assertEqual(output, target)

    def test___repr__(self):
        """ Test the __repr__ function of PackageListingAcl. """
        create_package_acl(self.session)

        packager = model.PackageListingAcl.get_acl_packager(
            self.session, 'pingou')
        self.assertEqual(5, len(packager))
        output = packager[0].__repr__()
        self.assertEqual(
            output,
            "PackageListingAcl(id:1, u'pingou', "
            "PackageListing:1, Acl:commit, Approved)")

    def test_get_acl_packager(self):
        """ Test the get_acl_packager function of PackageListingAcl.
        """

        acls = model.PackageListingAcl.get_acl_packager(
            self.session, 'pingou')
        self.assertEqual(0, len(acls))

        create_package_acl(self.session)

        acls = model.PackageListingAcl.get_acl_packager(
            self.session, 'pingou')
        self.assertEqual(5, len(acls))
        self.assertEqual(acls[0].packagelist.package.name, 'guake')
        self.assertEqual(acls[0].packagelist.collection.branchname, 'F-18')
        self.assertEqual(acls[1].packagelist.collection.branchname, 'F-18')
        self.assertEqual(acls[2].packagelist.collection.branchname, 'devel')
        self.assertEqual(acls[3].packagelist.collection.branchname, 'devel')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(
        PackageListingAcltests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
