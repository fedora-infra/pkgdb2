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
from tests import Modeltests, create_package, create_package_acl


class Packagetests(Modeltests):
    """ Package tests. """

    def test_init_package(self):
        """ Test the __init__ function of Package. """
        create_package(self.session)
        self.assertEqual(3, len(model.Package.all(self.session)))

    def test_repr_package(self):
        """ Test the __repr__ function of Package. """
        create_package(self.session)
        packages = model.Package.all(self.session)
        self.assertEqual("Package(u'guake', u'Top down terminal for GNOME', "
                         "u'Approved', "
                         "upstreamurl=u'http://guake.org', "
                         "reviewurl=u'https://bugzilla.redhat.com/450189', "
                         "shouldopen=True)",
                         packages[0].__repr__())

    def test_to_json(self):
        """ Test the to_json function of Package. """
        create_package(self.session)
        package = model.Package.by_name(self.session, 'guake')
        package = package.to_json()
        self.assertEqual(set(package.keys()), set(['status', 'upstream_url',
                         'name', 'summary', 'acls', 'creation_date',
                         'review_url', 'description']))

    def test_search(self):
        """ Test the search function of Package. """
        create_package(self.session)

        packages = model.Package.search(
            session=self.session,
            pkg_name='g%')
        self.assertEqual(len(packages), 2)
        self.assertEqual(packages[0].name, 'geany')
        self.assertEqual(packages[1].name, 'guake')

        packages = model.Package.search(
            session=self.session,
            pkg_name='g%',
            limit=1)
        self.assertEqual(len(packages), 1)
        self.assertEqual(packages[0].name, 'geany')

        packages = model.Package.search(
            session=self.session,
            pkg_name='g%',
            offset=1)
        self.assertEqual(len(packages), 1)
        self.assertEqual(packages[0].name, 'guake')

        packages = model.Package.search(
            session=self.session,
            pkg_name='g%',
            count=True)
        self.assertEqual(packages, 2)

    def test_get_package_of_user(self):
        """ Test the get_package_of_user function of Package. """
        create_package_acl(self.session)

        packages = model.Package.get_package_of_user(
            self.session, user='pingou', poc=True
        )
        self.assertEqual(len(packages), 2)
        self.assertEqual(packages[0][0].name, 'guake')

        expected = set(['devel', 'F-18'])
        branches = set([packages[0][1].branchname,
                        packages[1][1].branchname])
        self.assertEqual(branches.symmetric_difference(expected), set())

        packages = model.Package.get_package_of_user(
            self.session, user='pingou', poc=False
        )
        self.assertEqual(packages, [])

        packages = model.Package.get_package_of_user(
            self.session,
            user='pingou',
            pkg_status='Awaiting Review',
        )
        self.assertEqual(len(packages), 0)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Packagetests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
