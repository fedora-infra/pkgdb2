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

from pkgdb2.lib import model
from tests import (Modeltests, create_package_listing, create_package_acl,
                   create_package_critpath)


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
        self.assertEqual("PackageListing(id:1, u'pingou', "
                         "u'Approved', packageid=1, collectionid=2)",
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
        self.assertEqual("PackageListing(id:1, u'pingou', "
                         "u'Approved', packageid=1, collectionid=2)",
                         packages[0].__repr__())

        packages = model.PackageListing.search(self.session,
                                               pkg_name='g%',
                                               clt_id=collection.id,
                                               pkg_owner='pingou',
                                               pkg_status=None)
        self.assertEqual(2, len(packages))
        self.assertEqual("PackageListing(id:1, u'pingou', "
                         "u'Approved', packageid=1, collectionid=2)",
                         packages[0].__repr__())
        self.assertEqual("PackageListing(id:6, u'pingou', "
                         "u'Approved', packageid=3, collectionid=2)",
                         packages[1].__repr__())

        packages = model.PackageListing.search(self.session,
                                               pkg_name='g%',
                                               clt_id=collection.id,
                                               pkg_owner='pingou',
                                               pkg_status='Approved')
        self.assertEqual(2, len(packages))
        self.assertEqual("PackageListing(id:1, u'pingou', "
                         "u'Approved', packageid=1, collectionid=2)",
                         packages[0].__repr__())
        self.assertEqual("PackageListing(id:6, u'pingou', "
                         "u'Approved', packageid=3, collectionid=2)",
                         packages[1].__repr__())

        packages = model.PackageListing.search(self.session,
                                               pkg_name='g%',
                                               clt_id=collection.id,
                                               pkg_owner='pingou',
                                               pkg_status='Approved',
                                               count=True)
        self.assertEqual(2, packages)

        packages = model.PackageListing.search(self.session,
                                               pkg_name='g%',
                                               clt_id=collection.id,
                                               pkg_owner='pingou',
                                               pkg_status='Approved',
                                               limit=1)
        self.assertEqual("PackageListing(id:1, u'pingou', "
                         "u'Approved', packageid=1, collectionid=2)",
                         packages[0].__repr__())

        packages = model.PackageListing.search(self.session,
                                               pkg_name='g%',
                                               clt_id=collection.id,
                                               pkg_owner='pingou',
                                               pkg_status='Approved',
                                               critpath=False,
                                               offset=1)
        self.assertEqual(len(packages), 1)
        self.assertEqual("PackageListing(id:6, u'pingou', "
                         "u'Approved', packageid=3, collectionid=2)",
                         packages[0].__repr__())

        packages = model.PackageListing.search(self.session,
                                               pkg_name='g%',
                                               clt_id=collection.id,
                                               pkg_owner='pingou',
                                               pkg_status='Approved',
                                               critpath=True,
                                               offset=1)
        self.assertEqual(len(packages), 0)


    def test_to_json(self):
        """ Test the to_json function of PackageListing. """
        create_package_listing(self.session)
        pkg = model.Package.by_name(self.session, 'guake')
        package = model.PackageListing.by_package_id(self.session,
                                                     pkg.id)[0]
        package = package.to_json()
        self.assertEqual(
            package.keys(),
            ['status', 'point_of_contact', 'status_change','collection',
             'package'])

    def test_search_packagers(self):
        """ Test the search_packagers function of PackageListing. """
        pkg = model.PackageListing.search_packagers(
            self.session, 'pin%')
        self.assertEqual(pkg, [])

        create_package_acl(self.session)

        pkg = model.PackageListing.search_packagers(
            self.session, 'pi%')
        self.assertEqual(len(pkg), 1)
        self.assertEqual(pkg[0][0], 'pingou')

        pkg = model.PackageListing.search_packagers(
            self.session, 'pi%', count=True)
        self.assertEqual(pkg, 1)

        pkg = model.PackageListing.search_packagers(
            self.session, 'pi%', offset=1)
        self.assertEqual(pkg, [])

        pkg = model.PackageListing.search_packagers(
            self.session, 'pi%', limit=1)
        self.assertEqual(len(pkg), 1)

    def test_by_collectionid(self):
        """ Test the by_collectionid method of PackageListing. """
        create_package_acl(self.session)

        # Collection 2 == F-18
        pkg_list = model.PackageListing.by_collectionid(self.session, 2)
        self.assertEqual(len(pkg_list), 3)
        self.assertEqual(pkg_list[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_list[1].collection.branchname, 'F-18')
        self.assertEqual(pkg_list[2].collection.branchname, 'F-18')

        # Collection 3 == devel
        pkg_list = model.PackageListing.by_collectionid(self.session, 3)
        self.assertEqual(len(pkg_list), 3)
        self.assertEqual(pkg_list[0].collection.branchname, 'devel')
        self.assertEqual(pkg_list[1].collection.branchname, 'devel')


    def test_branch(self):
        """ Test the branch method of PackageListing. """
        create_package_acl(self.session)

        pkg = model.Package.by_name(self.session, 'guake')
        pkg_list = model.PackageListing.by_package_id(self.session,
                                                     pkg.id)
        self.assertEqual(len(pkg_list), 2)
        self.assertEqual(pkg_list[0].collection.branchname, 'F-18')
        self.assertEqual(len(pkg_list[0].acls), 2)
        self.assertEqual(pkg_list[1].collection.branchname, 'devel')
        self.assertEqual(len(pkg_list[1].acls), 4)

        # Create a new collection
        new_collection = model.Collection(
                                  name='Fedora',
                                  version='19',
                                  status='Active',
                                  owner='toshio',
                                  branchname='F-19',
                                  distTag='.fc19',
                                  git_branch_name='f19',
                                  )
        self.session.add(new_collection)
        self.session.commit()

        # Branch guake from devel to F-19
        pkg_list[1].branch(self.session, new_collection)

        pkg_list = model.PackageListing.by_package_id(self.session,
                                                     pkg.id)
        self.assertEqual(len(pkg_list), 3)
        self.assertEqual(pkg_list[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_list[1].collection.branchname, 'devel')
        self.assertEqual(len(pkg_list[1].acls), 4)
        self.assertEqual(pkg_list[2].collection.branchname, 'F-19')
        self.assertEqual(len(pkg_list[2].acls), 4)

    def test_get_critpath_packages(self):
        """ Test the get_critpath_packages method of PackageListing. """
        create_package_acl(self.session)

        pkg_list = model.PackageListing.get_critpath_packages(self.session)
        self.assertEqual(pkg_list, [])

        pkg_list = model.PackageListing.get_critpath_packages(
            self.session, branch='devel')
        self.assertEqual(pkg_list, [])

        create_package_critpath(self.session)

        pkg_list = model.PackageListing.get_critpath_packages(self.session)
        self.assertEqual(len(pkg_list), 2)
        self.assertEqual(
            pkg_list[0].point_of_contact, "kernel-maint")
        self.assertEqual(
            pkg_list[0].collection.branchname, "F-18")
        self.assertEqual(
            pkg_list[1].point_of_contact, "group::kernel-maint")
        self.assertEqual(
            pkg_list[1].collection.branchname, "devel")

        pkg_list = model.PackageListing.get_critpath_packages(
            self.session, branch='devel')
        self.assertEqual(len(pkg_list), 1)
        self.assertEqual(
            pkg_list[0].point_of_contact, "group::kernel-maint")
        self.assertEqual(
            pkg_list[0].collection.branchname, "devel")



if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(PackageListingtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
