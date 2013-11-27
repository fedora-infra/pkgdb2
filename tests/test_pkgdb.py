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

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import pkgdb2
from tests import Modeltests, FakeFasUser, FakeFasUserAdmin


class Pkgdbtests(Modeltests):
    """ pkgdb tests. """

    def test_is_pkgdb_admin(self):
        """ Test the is_pkgdb_admin function of pkgdb2. """
        user = FakeFasUser()
        out = pkgdb2.is_pkgdb_admin(user)
        self.assertEqual(out, False)

        user.groups = []
        out = pkgdb2.is_pkgdb_admin(user)
        self.assertEqual(out, False)

        user = FakeFasUser()
        out = pkgdb2.is_pkgdb_admin(None)
        self.assertEqual(out, False)

        user = FakeFasUserAdmin()
        out = pkgdb2.is_pkgdb_admin(user)
        self.assertEqual(out, True)

        pkgdb2.APP.config['ADMIN_GROUP'] = 'sysadmin-main'

        out = pkgdb2.is_pkgdb_admin(user)
        self.assertEqual(out, False)

        # Reset the ADMIN_GROUP for the other tests
        pkgdb2.APP.config['ADMIN_GROUP'] = ('sysadmin-main', 'sysadmin-cvs')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Pkgdbtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
