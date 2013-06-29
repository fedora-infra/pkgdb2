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
pkgdb tests for the Package object.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

from pkgdb.lib import model
from tests import Modeltests, create_package_listing, create_package_acl


class PackageListingtests(Modeltests):
    """ PackageListing tests. """

    def test_init_package_listing(self):
        """ Test the __init__ function of PackageListing. """
        create_package_listing(self.session)
        pkg = model.Package.by_name(self.session, 'guake')
        self.assertEqual(2,
                         len(model.PackageListing.by_package_id(
                            self.session,
                            pkg.id))
                         )

    def test_repr_package_listing(self):
        """ Test the __repr__ function of PackageListing. """
        create_package_listing(self.session)
        pkg = model.Package.by_name(self.session, 'guake')
        packages = model.PackageListing.by_package_id(self.session,
                                                        pkg.id)
        self.assertEqual("PackageListing(id:1, u'user::pingou', "
                         "u'Approved', packageid=1, collectionid=1)",
                         packages[0].__repr__())

    def test_search_listing(self):
        """ Test the search function of PackageListing. """
        create_package_listing(self.session)
        collection = model.Collection.by_name(self.session, 'F-18')
        packages = model.PackageListing.search(self.session,
                                               pkg_name='g%',
                                               clt_id=collection.id,
                                               pkg_owner=None,
                                               pkg_status=None)
        self.assertEqual(2, len(packages))
        self.assertEqual("PackageListing(id:1, u'user::pingou', "
                         "u'Approved', packageid=1, collectionid=1)",
                         packages[0].__repr__())

        packages = model.PackageListing.search(self.session,
                                               pkg_name='g%',
                                               clt_id=collection.id,
                                               pkg_owner='user::pingou',
                                               pkg_status=None)
        self.assertEqual(2, len(packages))
        self.assertEqual("PackageListing(id:1, u'user::pingou', "
                         "u'Approved', packageid=1, collectionid=1)",
                         packages[0].__repr__())
        self.assertEqual("PackageListing(id:5, u'user::pingou', "
                         "u'Approved', packageid=3, collectionid=1)",
                         packages[1].__repr__())


    def test_api_repr(self):
        """ Test the api_repr function of PackageListing. """
        create_package_listing(self.session)
        pkg = model.Package.by_name(self.session, 'guake')
        package = model.PackageListing.by_package_id(self.session,
                                                     pkg.id)[0]
        package = package.api_repr(1)
        self.assertEqual(package.keys(), ['point_of_contact',
                         'collection', 'package'])

    def test_to_json(self):
        """ Test the to_json function of PackageListing. """
        create_package_listing(self.session)
        pkg = model.Package.by_name(self.session, 'guake')
        package = model.PackageListing.by_package_id(self.session,
                                                     pkg.id)[0]
        package = package.to_json()
        self.assertEqual(package.keys(), ['point_of_contact',
                         'collection', 'package'])

    def test_search_point_of_contact(self):
        """ Test the search_point_of_contact function of PackageListing. """
        pkg = model.PackageListing.search_point_of_contact(
            self.session, 'pin%')
        self.assertEqual(pkg, [])

        create_package_acl(self.session)

        pkg = model.PackageListing.search_point_of_contact(
            self.session, 'pi%')
        self.assertEqual(len(pkg), 1)
        self.assertEqual(pkg[0][0], 'user::pingou')

    
    def test_get_acl_packager(self):
        """ Test the get_acl_packager function of PersonPackageListing.
        """

        acls = model.PackageListingAcl.get_acl_packager(
            self.session, 'pingou')
        self.assertEqual(0, len(acls))

        create_package_acl(self.session)

        acls = model.PackageListingAcl.get_acl_packager(
            self.session, 'pingou')
        self.assertEqual(4, len(acls))
        self.assertEqual(acls[0].packagelist.package.name, 'guake')
        self.assertEqual(acls[0].packagelist.collection.branchname, 'F-18')
        self.assertEqual(acls[1].packagelist.collection.branchname, 'F-18')
        self.assertEqual(acls[2].packagelist.collection.branchname, 'devel')
        self.assertEqual(acls[3].packagelist.collection.branchname, 'devel')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(PackageListingtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
