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

from pkgdb.lib import model
from tests import Modeltests, create_person_package_acl


class PersonPackageListingAcltests(Modeltests):
    """ PersonPackageListingAcl tests. """

    def test_init_package_listing_acl(self):
        """ Test the __init__ function of PersonPackageListingAcl. """
        create_person_package_acl(self.session)
        self.assertEqual(2,
                         len(model.PersonPackageListingAcl.all(self.session))
                         )

    def test_repr_package_listing_acl(self):
        """ Test the __repr__ function of PersonPackageListingAcl. """
        create_person_package_acl(self.session)
        person = model.PersonPackageListingAcl.all(self.session)
        self.assertEqual("PersonPackageListingAcl(u'commit', u'Approved',"
                         " personpackagelistingid=1)",
                         person[0].__repr__())

    def test_get_pending_acl(self):
        """ Test the get_pending_acl function of PersonPackageListingAcl.
        """
        create_person_package_acl(self.session)

        persopkglisting = model.PersonPackageListingAcl.get_pending_acl(
            self.session, 'pingou')
        self.assertEqual(1, len(persopkglisting))

        self.assertEqual(
            'pingou',
            persopkglisting[0].personpackagelist.user)

        self.assertEqual(
            'guake',
            persopkglisting[0].personpackagelist.packagelist.package.name)

        self.assertEqual(
            'F-18',
            persopkglisting[0].personpackagelist.packagelist.collection.branchname)
        self.assertEqual('Awaiting Review', persopkglisting[0].status)
        self.assertEqual('approveacls', persopkglisting[0].acl)

    def test_get_acl_package(self):
        """ Test the get_acl_package of PersonPackageListingAcl.
        """
        create_person_package_acl(self.session)

        persopkglisting = model.PersonPackageListingAcl.get_acl_package(
            self.session, 'pingou', 'geany')
        self.assertEqual(0, len(persopkglisting))

        persopkglisting = model.PersonPackageListingAcl.get_acl_package(
            self.session, 'pingou', 'guake', status=None)
        self.assertEqual(2, len(persopkglisting))
        self.assertEqual(
            'pingou',
            persopkglisting[0].personpackagelist.user)
        self.assertEqual(
            'guake',
            persopkglisting[0].personpackagelist.packagelist.package.name)
        self.assertEqual(
            'F-18',
            persopkglisting[0].personpackagelist.packagelist.collection.branchname)
        self.assertEqual('Awaiting Review', persopkglisting[0].status)
        self.assertEqual('approveacls', persopkglisting[0].acl)

        persopkglisting = model.PersonPackageListingAcl.get_acl_package(
            self.session, 'pingou', 'guake')
        self.assertEqual(1, len(persopkglisting))
        self.assertEqual(
            'pingou',
            persopkglisting[0].personpackagelist.user)
        self.assertEqual(
            'guake',
            persopkglisting[0].personpackagelist.packagelist.package.name)
        self.assertEqual(
            'F-18',
            persopkglisting[0].personpackagelist.packagelist.collection.branchname)
        self.assertEqual('Awaiting Review', persopkglisting[0].status)
        self.assertEqual('approveacls', persopkglisting[0].acl)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(PersonPackageListingAcltests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
