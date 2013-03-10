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
pkgdb tests for the Collection object.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import sys
import os

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import pkgdb.lib as pkgdblib
from pkgdb.lib import model
from tests import (FakeFasUser, Modeltests, create_collection,
                   create_package)


class PkgdbLibtests(Modeltests):
    """ PkgdbLib tests. """

    def test_add_package(self):
        """ Test the add_package function. """
        create_collection(self.session)
        pkgdblib.add_package(self.session,
                             pkg_name='guake',
                             pkg_summary='Drop down terminal',
                             pkg_status='Approved',
                             pkg_collection='F-18',
                             pkg_owner='pingou',
                             pkg_reviewURL=None,
                             pkg_shouldopen=None,
                             pkg_upstreamURL=None)
        self.session.commit()
        packages = model.Package.all(self.session)
        self.assertEqual(1, len(packages))
        self.assertEqual('guake', packages[0].name)

    def test_get_acl_package(self):
        """ Test the get_acl_package function. """
        self.test_add_package()
        self.session.commit()

        packages = model.Package.all(self.session)
        self.assertEqual(1, len(packages))
        self.assertEqual('guake', packages[0].name)

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].people, [])

    def test_set_acl_package(self):
        """ Test the get_acl_package function. """
        self.test_add_package()

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.set_acl_package,
                          self.session,
                          pkg_name='test',
                          clt_name='F-17',
                          user=FakeFasUser(),
                          acl='nothing',
                          status='Appr'
                          )
        self.session.rollback()

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.set_acl_package,
                          self.session,
                          pkg_name='guake',
                          clt_name='F-17',
                          user=FakeFasUser(),
                          acl='nothing',
                          status='Appr'
                          )
        self.session.rollback()

        self.assertRaises(IntegrityError,
                          pkgdblib.set_acl_package,
                          self.session,
                          pkg_name='guake',
                          clt_name='F-18',
                          user=FakeFasUser(),
                          acl='nothing',
                          status='Appro'
                          )
        self.session.rollback()

        self.assertRaises(IntegrityError,
                          pkgdblib.set_acl_package,
                          self.session,
                          pkg_name='guake',
                          clt_name='F-18',
                          user=FakeFasUser(),
                          acl='nothing',
                          status='Approved'
                          )
        self.session.rollback()

        pkgdblib.set_acl_package(self.session,
                                 pkg_name='guake',
                                 clt_name='F-18',
                                 user=FakeFasUser(),
                                 acl='commit',
                                 status='Approved'
                                 )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(len(pkg_acl[0].people), 1)
        


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(PkgdbLibtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
