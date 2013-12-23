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

import mock
import unittest
import sys
import os

from datetime import date

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import pkgdb2
import pkgdb2.lib as pkgdblib
from tests import (FakeFasUser, FakeFasUserAdmin, Modeltests,
                   FakeFasGroupValid, FakeFasGroupInvalid,
                   create_collection, create_package,
                   create_package_listing, create_package_acl,
                   create_package_critpath)


class PkgdbLibtests(Modeltests):
    """ PkgdbLib tests. """

    def test_add_package(self):
        """ Test the add_package function. """
        create_collection(self.session)

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.add_package,
                          self.session,
                          pkg_name='test',
                          pkg_summary='test package',
                          pkg_description='test description',
                          pkg_status='Approved',
                          pkg_collection='F-18',
                          pkg_poc='ralph',
                          pkg_reviewURL=None,
                          pkg_shouldopen=None,
                          pkg_upstreamURL='http://example.org',
                          user=FakeFasUser()
                          )
        self.session.rollback()

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.add_package,
                          self.session,
                          pkg_name='test',
                          pkg_summary='test package',
                          pkg_description='test description',
                          pkg_status='Approved',
                          pkg_collection='F-18',
                          pkg_poc='group::tests',
                          pkg_reviewURL=None,
                          pkg_shouldopen=None,
                          pkg_upstreamURL='http://example.org',
                          user=FakeFasUserAdmin()
                          )
        self.session.rollback()

        pkgdb2.lib.utils.get_packagers = mock.MagicMock()
        pkgdb2.lib.utils.get_packagers.reset_mock()

        # Configuration to query FAS isn't set
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.add_package,
                          self.session,
                          pkg_name='guake',
                          pkg_summary='Drop down terminal',
                          pkg_description='Drop down terminal desc',
                          pkg_status='Approved',
                          pkg_collection='F-18',
                          pkg_poc='ralph',
                          pkg_reviewURL=None,
                          pkg_shouldopen=None,
                          pkg_upstreamURL='http://guake.org',
                          user=FakeFasUserAdmin())

        pkgdb2.lib.utils.get_packagers = mock.MagicMock()
        pkgdb2.lib.utils.get_packagers.return_value = ['pingou']

        # 'Ralph' is not in the packager group
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.add_package,
                          self.session,
                          pkg_name='guake',
                          pkg_summary='Drop down terminal',
                          pkg_description='Drop down terminal desc',
                          pkg_status='Approved',
                          pkg_collection='F-18',
                          pkg_poc='ralph',
                          pkg_reviewURL=None,
                          pkg_shouldopen=None,
                          pkg_upstreamURL='http://guake.org',
                          user=FakeFasUserAdmin())

        pkgdb2.lib.utils.get_fas_group = mock.MagicMock()
        pkgdb2.lib.utils.get_fas_group.return_value = FakeFasGroupInvalid

        # Invalid FAS group returned
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.add_package,
                          self.session,
                          pkg_name='fedocal',
                          pkg_summary='web calendar for Fedora',
                          pkg_description='Web-based calendar system',
                          pkg_status='Approved',
                          pkg_collection='devel, F-18',
                          pkg_poc='group::infra-sig',
                          pkg_reviewURL=None,
                          pkg_shouldopen=None,
                          pkg_upstreamURL=None,
                          user=FakeFasUserAdmin())

        pkgdb2.lib.utils.get_packagers = mock.MagicMock()
        pkgdb2.lib.utils.get_packagers.return_value = ['ralph', 'pingou']

        msg = pkgdblib.add_package(self.session,
                                    pkg_name='guake',
                                    pkg_summary='Drop down terminal',
                                    pkg_description='Drop down terminal desc',
                                    pkg_status='Approved',
                                    pkg_collection='F-18',
                                    pkg_poc='ralph',
                                    pkg_reviewURL=None,
                                    pkg_shouldopen=None,
                                    pkg_upstreamURL='http://guake.org',
                                    user=FakeFasUserAdmin())
        self.assertEqual(msg, 'Package created')
        self.session.commit()
        packages = pkgdblib.model.Package.all(self.session)
        self.assertEqual(1, len(packages))
        self.assertEqual('guake', packages[0].name)

        pkgdblib.add_package(self.session,
                             pkg_name='geany',
                             pkg_summary='GTK IDE',
                             pkg_description='Lightweight IDE for GNOME',
                             pkg_status='Approved',
                             pkg_collection='devel, F-18',
                             pkg_poc='ralph',
                             pkg_reviewURL=None,
                             pkg_shouldopen=None,
                             pkg_upstreamURL=None,
                             user=FakeFasUserAdmin())
        self.session.commit()
        packages = pkgdblib.model.Package.all(self.session)
        self.assertEqual(2, len(packages))
        self.assertEqual('guake', packages[0].name)
        self.assertEqual('geany', packages[1].name)

        pkgdb2.lib.utils.get_fas_group = mock.MagicMock()
        pkgdb2.lib.utils.get_fas_group.return_value = FakeFasGroupValid

        pkgdblib.add_package(self.session,
                             pkg_name='fedocal',
                             pkg_summary='web calendar for Fedora',
                             pkg_description='Web-based calendar system',
                             pkg_status='Approved',
                             pkg_collection='devel, F-18',
                             pkg_poc='group::infra-sig',
                             pkg_reviewURL=None,
                             pkg_shouldopen=None,
                             pkg_upstreamURL=None,
                             user=FakeFasUserAdmin())
        self.session.commit()
        packages = pkgdblib.model.Package.all(self.session)
        self.assertEqual(3, len(packages))
        self.assertEqual('guake', packages[0].name)
        self.assertEqual('geany', packages[1].name)
        self.assertEqual('fedocal', packages[2].name)

    def test_get_acl_package(self):
        """ Test the get_acl_package function. """
        create_package_acl(self.session)

        packages = pkgdblib.model.Package.all(self.session)
        self.assertEqual(3, len(packages))
        self.assertEqual('guake', packages[0].name)

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(len(pkg_acl), 2)
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].acls[0].fas_name, 'pingou')

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake', 'devel')[0]
        self.assertEqual(pkg_acl.collection.branchname, 'devel')
        self.assertEqual(pkg_acl.package.name, 'guake')
        self.assertEqual(pkg_acl.acls[0].fas_name, 'pingou')

        # Package does not exist
        self.assertRaises(NoResultFound,
                          pkgdblib.get_acl_package,
                          self.session,
                          'test',
                          'devel')

        # Collection does not exist
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.get_acl_package,
                          self.session,
                          'guake',
                          'unknown')


    def test_set_acl_package(self):
        """ Test the set_acl_package function. """
        self.test_add_package()

        # Not allowed to set acl on non-existant package
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.set_acl_package,
                          self.session,
                          pkg_name='test',
                          pkg_branch='F-17',
                          pkg_user='pingou',
                          acl='nothing',
                          status='Appr',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        # Not allowed to set non-existant collection
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.set_acl_package,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='F-16',
                          pkg_user='pingou',
                          acl='nothing',
                          status='Appr',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        # Not allowed to set non-existant status
        self.assertRaises(IntegrityError,
                          pkgdblib.set_acl_package,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='F-18',
                          acl='commit',
                          pkg_user='pingou',
                          status='Appro',
                          user=FakeFasUserAdmin(),
                          )
        self.session.rollback()

        # Not allowed to set non-existant acl
        self.assertRaises(IntegrityError,
                          pkgdblib.set_acl_package,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='F-18',
                          pkg_user='pingou',
                          acl='nothing',
                          status='Approved',
                          user=FakeFasUserAdmin(),
                          )
        self.session.rollback()

        # Not allowed to set acl for yourself
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.set_acl_package,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='F-18',
                          pkg_user='pingou',
                          acl='approveacls',
                          status='Approved',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        # Not allowed to set acl for someone else
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.set_acl_package,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='F-18',
                          pkg_user='ralph',
                          acl='commit',
                          status='Approved',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        # Not allowed to set acl approveacl to a group
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.set_acl_package,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='F-18',
                          pkg_user='group::perl',
                          acl='approveacls',
                          status='Approved',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        # Group must ends with -sig
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.set_acl_package,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='F-18',
                          pkg_user='group::perl',
                          acl='commit',
                          status='Approved',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        # You can ask for new ACLs
        pkgdblib.set_acl_package(self.session,
                                 pkg_name='guake',
                                 pkg_branch='F-18',
                                 pkg_user='pingou',
                                 acl='approveacls',
                                 status='Awaiting Review',
                                 user=FakeFasUser(),
                                 )
        self.session.commit()

        # You can obsolete your own ACLs
        pkgdblib.set_acl_package(self.session,
                                 pkg_name='guake',
                                 pkg_branch='F-18',
                                 pkg_user='pingou',
                                 acl='approveacls',
                                 status='Obsolete',
                                 user=FakeFasUser(),
                                 )
        self.session.commit()

        # You can remove your own ACLs
        pkgdblib.set_acl_package(self.session,
                                 pkg_name='guake',
                                 pkg_branch='F-18',
                                 pkg_user='pingou',
                                 acl='approveacls',
                                 status='Removed',
                                 user=FakeFasUser(),
                                 )
        self.session.commit()

        # An admin can approve you ACLs
        pkgdblib.set_acl_package(self.session,
                                 pkg_name='guake',
                                 pkg_branch='F-18',
                                 pkg_user='pingou',
                                 acl='commit',
                                 status='Approved',
                                 user=FakeFasUserAdmin(),
                                 )
        self.session.commit()

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(len(pkg_acl[0].acls), 6)

    def test_update_pkg_poc(self):
        """ Test the update_pkg_poc function. """
        self.test_add_package()

        # Package must exists
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.update_pkg_poc,
                          self.session,
                          pkg_name='test',
                          pkg_branch='F-17',
                          user=FakeFasUser(),
                          pkg_poc='toshio',
                          )
        self.session.rollback()

        # Collection must exists
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.update_pkg_poc,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='F-16',
                          user=FakeFasUser(),
                          pkg_poc='toshio',
                          )
        self.session.rollback()

        pkgdb2.lib.utils.get_packagers = mock.MagicMock()
        pkgdb2.lib.utils.get_packagers.return_value = [
            'pingou', 'toshio', 'ralph']

        # User must be the actual Point of Contact (or an admin of course,
        # or part of the group)
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.update_pkg_poc,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='F-18',
                          user=FakeFasUser(),
                          pkg_poc='toshio',
                          )
        self.session.rollback()

        # Groups must end with -sig
        user = FakeFasUser()
        user.username = 'ralph'
        # Change PoC to a group
        pkgdblib.update_pkg_poc(
                          self.session,
                          pkg_name='guake',
                          pkg_branch='F-18',
                          user=user,
                          pkg_poc='group::perl-sig',
                          )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].point_of_contact, 'group::perl-sig')

        # User must be in the group it takes the PoC from
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.update_pkg_poc,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='F-18',
                          user=user,
                          pkg_poc='ralph',
                          )
        self.session.rollback()

        user.groups.append('perl-sig')
        pkgdblib.update_pkg_poc(
                          self.session,
                          pkg_name='guake',
                          pkg_branch='F-18',
                          user=user,
                          pkg_poc='ralph',
                          )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].point_of_contact, 'ralph')

        pkgdb2.lib.utils.get_packagers = mock.MagicMock()
        pkgdb2.lib.utils.get_packagers.return_value = ['pingou', 'toshio']

        # PoC can change PoC
        user = FakeFasUser()
        user.username = 'ralph'
        pkgdblib.update_pkg_poc(self.session,
                                 pkg_name='guake',
                                 pkg_branch='F-18',
                                 user=user,
                                 pkg_poc='toshio',
                                 )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].point_of_contact, 'toshio')

        # PoC must be a packager, even for admin
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.update_pkg_poc,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='F-18',
                          user=FakeFasUserAdmin,
                          pkg_poc='kevin',
                          )
        self.session.rollback()

        pkgdb2.lib.utils.get_packagers = mock.MagicMock()
        pkgdb2.lib.utils.get_packagers.return_value = ['pingou', 'kevin']

        # Admin can change PoC
        pkgdblib.update_pkg_poc(self.session,
                                 pkg_name='guake',
                                 pkg_branch='F-18',
                                 user=FakeFasUserAdmin(),
                                 pkg_poc='kevin',
                                 )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].point_of_contact, 'kevin')

        # Orphan -> status changed to Orphaned
        user = FakeFasUser()
        user.username = 'kevin'
        pkgdblib.update_pkg_poc(self.session,
                                 pkg_name='guake',
                                 pkg_branch='F-18',
                                 user=user,
                                 pkg_poc='orphan',
                                 )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].point_of_contact, 'orphan')
        self.assertEqual(pkg_acl[0].status, 'Orphaned')

        # Take orphaned package -> status changed to Approved
        pkgdblib.update_pkg_poc(self.session,
                                 pkg_name='guake',
                                 pkg_branch='F-18',
                                 user=FakeFasUser(),
                                 pkg_poc=FakeFasUser().username,
                                 )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].point_of_contact, 'pingou')
        self.assertEqual(pkg_acl[0].status, 'Approved')


    def test_create_session(self):
        """ Test the create_session function. """
        session = pkgdblib.create_session('sqlite:///:memory:')
        self.assertTrue(session is not None)

    def test_search_package(self):
        """ Test the search_package function. """
        self.test_add_package()
        pkgs = pkgdblib.search_package(self.session,
                                       pkg_name='gu*',
                                       pkg_branch='F-18',
                                       pkg_poc=None,
                                       orphaned=None,
                                       status=None,
                                       )
        self.assertEqual(len(pkgs), 1)
        self.assertEqual(pkgs[0].name, 'guake')
        self.assertEqual(pkgs[0].upstream_url, 'http://guake.org')

        pkgs = pkgdblib.search_package(self.session,
                                       pkg_name='g*',
                                       pkg_branch='F-18',
                                       pkg_poc=None,
                                       orphaned=None,
                                       status=None,
                                       )
        self.assertEqual(len(pkgs), 2)
        self.assertEqual(pkgs[0].name, 'geany')
        self.assertEqual(pkgs[1].name, 'guake')

        pkgs = pkgdblib.search_package(self.session,
                                       pkg_name='g*',
                                       pkg_branch='F-18',
                                       pkg_poc=None,
                                       orphaned=None,
                                       status=None,
                                       limit=1
                                       )
        self.assertEqual(len(pkgs), 1)
        self.assertEqual(pkgs[0].name, 'geany')

        pkgs = pkgdblib.search_package(self.session,
                                       pkg_name='g*',
                                       pkg_branch='F-18',
                                       pkg_poc=None,
                                       orphaned=None,
                                       status=None,
                                       limit=1,
                                       page=2
                                       )
        self.assertEqual(len(pkgs), 1)
        self.assertEqual(pkgs[0].name, 'guake')

        pkgs = pkgdblib.search_package(self.session,
                                       pkg_name='g*',
                                       pkg_branch='F-18',
                                       pkg_poc=None,
                                       orphaned=None,
                                       status=None,
                                       page=2
                                       )
        self.assertEqual(len(pkgs), 0)

        pkgs = pkgdblib.search_package(self.session,
                                       pkg_name='gu*',
                                       pkg_branch='F-18',
                                       pkg_poc=None,
                                       orphaned=True,
                                       status=None,
                                       )
        self.assertEqual(len(pkgs), 0)

        pkgs = pkgdblib.search_package(self.session,
                                       pkg_name='gu*',
                                       pkg_branch='F-18',
                                       pkg_poc=None,
                                       orphaned=None,
                                       status='Retired',
                                       )
        self.assertEqual(len(pkgs), 0)

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.search_package,
                          self.session,
                          pkg_name='g*',
                          pkg_branch='F-18',
                          pkg_poc=None,
                          orphaned=None,
                          status=None,
                          limit='a'
                          )

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.search_package,
                          self.session,
                          pkg_name='g*',
                          pkg_branch='F-18',
                          pkg_poc=None,
                          orphaned=None,
                          status=None,
                          page='a'
                          )

    def test_update_pkg_status(self):
        """ Test the update_pkg_status function. """
        create_package_acl(self.session)

        # Wrong package
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.update_pkg_status,
                          self.session,
                          pkg_name='test',
                          pkg_branch='F-17',
                          status='Retired',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        # Wrong collection
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.update_pkg_status,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='F-16',
                          status='Orphaned',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        # User not allowed to retire the package on F-18
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.update_pkg_status,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='F-18',
                          status='Retired',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        # Wrong status
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.update_pkg_status,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='F-18',
                          status='Depreasdcated',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        # User not allowed to change status to Allowed
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.update_pkg_status,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='F-18',
                          status='Allowed',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        # Admin can retire package
        pkgdblib.update_pkg_status(self.session,
                                   pkg_name='guake',
                                   pkg_branch='F-18',
                                   status='Retired',
                                   user=FakeFasUserAdmin()
                                   )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].point_of_contact, 'orphan')
        self.assertEqual(pkg_acl[0].status, 'Retired')

        # User can orphan package
        pkgdblib.update_pkg_status(self.session,
                                   pkg_name='guake',
                                   pkg_branch='devel',
                                   status='Orphaned',
                                   user=FakeFasUser()
                                   )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].point_of_contact, 'orphan')
        self.assertEqual(pkg_acl[0].status, 'Retired')
        self.assertEqual(pkg_acl[1].collection.branchname, 'devel')
        self.assertEqual(pkg_acl[1].package.name, 'guake')
        self.assertEqual(pkg_acl[1].point_of_contact, 'orphan')
        self.assertEqual(pkg_acl[1].status, 'Orphaned')

        # Admin must give a poc when un-orphan/un-retire a package
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.update_pkg_status,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='devel',
                          status='Approved',
                          user=FakeFasUserAdmin()
                          )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].point_of_contact, 'orphan')
        self.assertEqual(pkg_acl[0].status, 'Retired')
        self.assertEqual(pkg_acl[1].collection.branchname, 'devel')
        self.assertEqual(pkg_acl[1].package.name, 'guake')
        self.assertEqual(pkg_acl[1].point_of_contact, 'orphan')
        self.assertEqual(pkg_acl[1].status, 'Orphaned')


        # Admin can un-orphan package
        pkgdblib.update_pkg_status(self.session,
                                   pkg_name='guake',
                                   pkg_branch='devel',
                                   status='Approved',
                                   poc="pingou",
                                   user=FakeFasUserAdmin()
                                   )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].point_of_contact, 'orphan')
        self.assertEqual(pkg_acl[0].status, 'Retired')
        self.assertEqual(pkg_acl[1].collection.branchname, 'devel')
        self.assertEqual(pkg_acl[1].package.name, 'guake')
        self.assertEqual(pkg_acl[1].point_of_contact, 'pingou')
        self.assertEqual(pkg_acl[1].status, 'Approved')

        # Admin can un-retire package
        pkgdblib.update_pkg_status(self.session,
                                   pkg_name='guake',
                                   pkg_branch='F-18',
                                   status='Approved',
                                   poc="pingou",
                                   user=FakeFasUserAdmin()
                                   )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].point_of_contact, 'pingou')
        self.assertEqual(pkg_acl[0].status, 'Approved')
        self.assertEqual(pkg_acl[1].collection.branchname, 'devel')
        self.assertEqual(pkg_acl[1].package.name, 'guake')
        self.assertEqual(pkg_acl[1].point_of_contact, 'pingou')
        self.assertEqual(pkg_acl[1].status, 'Approved')

        # Not Admin and status is not Orphaned nor Retired
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.update_pkg_status,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='devel',
                          status='Removed',
                          user=FakeFasUser()
                          )

    def test_search_collection(self):
        """ Test the search_collection function. """
        create_collection(self.session)

        collections = pkgdblib.search_collection(self.session, 'EPEL*')
        self.assertEqual(len(collections), 0)

        collections = pkgdblib.search_collection(self.session, 'F-*',
                                                 status='EOL')
        self.assertEqual(len(collections), 0)

        collections = pkgdblib.search_collection(self.session, 'F-*')
        self.assertEqual(len(collections), 2)
        self.assertEqual(
            "Collection(u'Fedora', u'17', u'Active', owner:u'toshio')",
            collections[0].__repr__())

        collections = pkgdblib.search_collection(
            self.session,
            'F-*',
            limit=1)
        self.assertEqual(len(collections), 1)

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.search_collection,
                          self.session,
                          'F-*',
                          limit='a'
                          )

        collections = pkgdblib.search_collection(
            self.session,
            'F-*',
            limit=1,
            page=2)
        self.assertEqual(len(collections), 1)

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.search_collection,
                          self.session,
                          'F-*',
                          page='a'
                          )

    def test_add_collection(self):
        """ Test the add_collection function. """

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.add_collection,
                          session=self.session,
                          clt_name='Fedora',
                          clt_version='19',
                          clt_status='Active',
                          clt_branchname='F-19',
                          clt_disttag='.fc19',
                          clt_gitbranch='f19',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        pkgdblib.add_collection(self.session,
                                clt_name='Fedora',
                                clt_version='19',
                                clt_status='Active',
                                clt_branchname='F-19',
                                clt_disttag='.fc19',
                                clt_gitbranch='f19',
                                user=FakeFasUserAdmin(),
                                )
        self.session.commit()
        collection = pkgdblib.model.Collection.by_name(self.session, 'F-19')
        self.assertEqual(
            "Collection(u'Fedora', u'19', u'Active', owner:u'admin')",
            collection.__repr__())

    def test_update_collection_status(self):
        """ Test the update_collection_status function. """
        create_collection(self.session)

        collection = pkgdblib.model.Collection.by_name(self.session, 'F-18')
        self.assertEqual(collection.status, 'Active')

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.update_collection_status,
                          self.session,
                          'F-18',
                          'EOL',
                          user=FakeFasUser(),
                          )

        pkgdblib.update_collection_status(
            self.session, 'F-18', 'EOL', user=FakeFasUserAdmin())
        self.session.commit()

        msg = pkgdblib.update_collection_status(
            self.session, 'F-18', 'EOL', user=FakeFasUserAdmin())
        self.assertEqual(msg, 'Collection "F-18" already had this status')

        collection = pkgdblib.model.Collection.by_name(self.session, 'F-18')
        self.assertEqual(collection.status, 'EOL')

    def test_search_packagers(self):
        """ Test the search_packagers function. """
        pkg = pkgdblib.search_packagers(self.session, 'pin*')
        self.assertEqual(pkg, [])

        create_package_acl(self.session)

        pkg = pkgdblib.search_packagers(self.session, 'pi*')
        self.assertEqual(len(pkg), 1)
        self.assertEqual(pkg[0][0], 'pingou')

        pkg = pkgdblib.search_packagers(self.session, 'pi*', page=0)
        self.assertEqual(len(pkg), 1)
        self.assertEqual(pkg[0][0], 'pingou')

        pkg = pkgdblib.search_packagers(self.session, 'pi*', limit=1, page=1)
        self.assertEqual(len(pkg), 1)
        self.assertEqual(pkg[0][0], 'pingou')

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.search_packagers,
                          self.session,
                          'p*',
                          limit='a'
                          )

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.search_packagers,
                          self.session,
                          'p*',
                          page='a'
                          )

    def test_get_acl_packager(self):
        """ Test the get_acl_packager function. """
        acls = pkgdblib.get_acl_packager(self.session, 'pingou')
        self.assertEqual(acls, [])

        create_package_acl(self.session)

        acls = pkgdblib.get_acl_packager(self.session, 'pingou')
        self.assertEqual(len(acls), 5)
        self.assertEqual(acls[0].packagelist.package.name, 'guake')
        self.assertEqual(acls[0].packagelist.collection.branchname, 'F-18')
        self.assertEqual(acls[1].packagelist.collection.branchname, 'F-18')
        self.assertEqual(acls[2].packagelist.collection.branchname, 'devel')
        self.assertEqual(acls[3].packagelist.collection.branchname, 'devel')

    def test_get_pending_acl_user(self):
        """ Test the get_pending_acl_user function. """
        pending_acls = pkgdblib.get_pending_acl_user(
            self.session, 'pingou')
        self.assertEqual(pending_acls, [])

        create_package_acl(self.session)

        pending_acls = pkgdblib.get_pending_acl_user(
            self.session, 'pingou')
        self.assertEqual(len(pending_acls), 1)
        self.assertEqual(pending_acls[0]['package'], 'guake')
        self.assertEqual(pending_acls[0]['collection'], 'devel')
        self.assertEqual(pending_acls[0]['acl'], 'commit')
        self.assertEqual(pending_acls[0]['status'], 'Awaiting Review')

    def test_get_acl_user_package(self):
        """ Test the get_acl_user_package function. """
        pending_acls = pkgdblib.get_acl_user_package(
            self.session, 'pingou', 'guake')
        self.assertEqual(pending_acls, [])

        create_package_acl(self.session)

        pending_acls = pkgdblib.get_acl_user_package(
            self.session, 'pingou', 'geany')
        self.assertEqual(len(pending_acls), 0)

        pending_acls = pkgdblib.get_acl_user_package(
            self.session, 'pingou', 'guake')
        self.assertEqual(len(pending_acls), 5)

        pending_acls = pkgdblib.get_acl_user_package(
            self.session, 'toshio', 'guake', status='Awaiting Review')
        self.assertEqual(len(pending_acls), 1)
        self.assertEqual(pending_acls[0]['package'], 'guake')
        self.assertEqual(pending_acls[0]['collection'], 'devel')
        self.assertEqual(pending_acls[0]['acl'], 'commit')
        self.assertEqual(pending_acls[0]['status'], 'Awaiting Review')

    def test_has_acls(self):
        """ Test the has_acls function. """
        self.assertFalse(pkgdblib.has_acls(self.session, 'pingou',
            'guake', 'devel', 'approveacl'))

        create_package_acl(self.session)

        self.assertTrue(pkgdblib.has_acls(self.session, 'pingou',
            'guake', 'devel', 'commit'))

    def test_get_status(self):
        """ Test the get_status function. """
        obs = pkgdblib.get_status(self.session)

        acl_status = ['Approved', 'Awaiting Review', 'Denied', 'Obsolete',
                      'Removed']
        self.assertEqual(obs['acl_status'], acl_status)

        pkg_status = ['Approved', 'Orphaned', 'Removed', 'Retired']
        self.assertEqual(obs['pkg_status'], pkg_status)

        clt_status = ['Active', 'EOL', 'Under Development']
        self.assertEqual(obs['clt_status'], clt_status)

        pkg_acl = ['approveacls', 'commit', 'watchbugzilla', 'watchcommits']
        self.assertEqual(obs['pkg_acl'], pkg_acl)

        obs = pkgdblib.get_status(self.session, 'acl_status')
        self.assertEqual(obs.keys(), ['acl_status'])
        self.assertEqual(obs['acl_status'], acl_status)

        obs = pkgdblib.get_status(self.session, ['acl_status', 'pkg_acl'])
        self.assertEqual(obs.keys(), ['pkg_acl', 'acl_status'])
        self.assertEqual(obs['pkg_acl'], pkg_acl)
        self.assertEqual(obs['acl_status'], acl_status)

    def test_get_package_maintained(self):
        """ Test the get_package_maintained function. """
        create_package_acl(self.session)

        pkg = pkgdblib.get_package_maintained(self.session, 'pingou',
            poc=True)
        self.assertEqual(len(pkg), 1)
        self.assertEqual(pkg[0][0].name, 'guake')
        expected = set(['devel', 'F-18'])
        branches = set([pkg[0][1][0].branchname, pkg[0][1][1].branchname])
        self.assertEqual(branches.symmetric_difference(expected), set())
        self.assertEqual(len(pkg[0][1]), 2)

        pkg = pkgdblib.get_package_maintained(self.session, 'pingou',
            poc=False)
        self.assertEqual(pkg, [])

        pkg = pkgdblib.get_package_maintained(self.session, 'ralph')
        self.assertEqual(pkg, [])

    def test_edit_collection(self):
        """ Test the edit_collection function. """
        create_collection(self.session)

        collection = pkgdblib.search_collection(self.session, 'F-18')[0]

        out = pkgdblib.edit_collection(self.session, collection,
                                       user=FakeFasUserAdmin())
        self.assertEqual(out, None)

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.edit_collection,
                          self.session,
                          collection)

        out = pkgdblib.edit_collection(
            self.session,
            collection,
            clt_name='Fedora youhou!',
            clt_version='Awesome 18',
            clt_status='EOL',
            clt_branchname='f18_b',
            clt_disttag='fc18',
            clt_gitbranch='F-18',
            user=FakeFasUserAdmin(),
            )

        self.assertEqual(out, 'Collection "f18_b" edited')

        collections = pkgdblib.search_collection(self.session, 'F-18')
        self.assertEqual(collections, [])

        collection = pkgdblib.search_collection(self.session, 'f18_b')[0]
        self.assertEqual(collection.name, 'Fedora youhou!')
        self.assertEqual(collection.status, 'EOL')

    def test_edit_package(self):
        """ Test the edit_package function. """
        create_collection(self.session)
        create_package(self.session)

        package = pkgdblib.search_package(self.session, 'guake')[0]

        out = pkgdblib.edit_package(self.session, package,
                                       user=FakeFasUserAdmin())
        self.assertEqual(out, None)

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.edit_package,
                          self.session,
                          package)

        out = pkgdblib.edit_package(
            self.session,
            package,
            pkg_name='Fedora youhou!',
            pkg_summary='Youhou Fedora is awesome!',
            pkg_status='Orphaned',
            pkg_description='this package says how awesome fedora is',
            pkg_review_url='http://bugzilla.rh.com/42',
            pkg_upstream_url='https://fedoraproject.org',
            user=FakeFasUserAdmin(),
            )

        self.assertEqual(out, 'Package "Fedora youhou!" edited')

        collections = pkgdblib.search_package(self.session, 'guake')
        self.assertEqual(collections, [])

        package = pkgdblib.search_package(self.session, 'Fedora youhou!')[0]
        self.assertEqual(package.name, 'Fedora youhou!')
        self.assertEqual(package.review_url, 'http://bugzilla.rh.com/42')
        self.assertEqual(package.summary, 'Youhou Fedora is awesome!')
        self.assertEqual(package.status, 'Orphaned')

    def test_get_top_maintainers(self):
        """ Test the get_top_maintainers funtion. """
        create_package_acl(self.session)

        top = pkgdblib.get_top_maintainers(self.session)
        self.assertEqual(top, [(u'group::gtk-sig', 1), (u'pingou', 1)])


    def test_get_top_poc(self):
        """ Test the get_top_poc function. """
        create_package_acl(self.session)

        top = pkgdblib.get_top_poc(self.session)
        self.assertEqual(top, [(u'pingou', 3), (u'group::gtk-sig', 1)])

    def test_search_logs(self):
        """ Test the search_logs function. """
        self.test_add_package()

        # Wrong limit
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.search_logs,
                          self.session,
                          limit='a'
                          )

        # Wrong offset
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.search_logs,
                          self.session,
                          page='a'
                          )

        # Wrong package name
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.search_logs,
                          self.session,
                          package='asdads'
                          )

        logs = pkgdblib.search_logs(self.session)

        self.assertEqual(len(logs), 23)
        self.assertEqual(logs[22].description, "user: admin created "
                         "package: guake on branch: F-18 for poc: ralph")
        self.assertEqual(logs[22].user, "admin")
        self.assertEqual(logs[19].description, "user: admin set acl: "
                         "watchcommits of package: guake from: Approved to:"
                         " Approved on branch: F-18")

        logs = pkgdblib.search_logs(self.session, limit=3, page=2)

        self.assertEqual(len(logs), 3)
        self.assertEqual(logs[0].description, "user: admin set acl: "
                         "watchcommits of package: fedocal from: Approved "
                         "to: Approved on branch: devel")
        self.assertEqual(logs[0].user, "admin")

        exp = "Log(user=u'admin', description=u'user: admin set acl: " \
              "watchcommits of package: fedocal from: Approved to:" \
              " Approved on branch: devel"
        self.assertTrue(logs[0].__repr__().startswith(exp))

        logs = pkgdblib.search_logs(self.session, count=True)
        self.assertEqual(logs, 23)

        logs = pkgdblib.search_logs(self.session, from_date=date.today())
        self.assertEqual(len(logs), 23)

        logs = pkgdblib.search_logs(
            self.session, from_date=date.today(), package='guake')
        self.assertEqual(len(logs), 5)

    def test_unorphan_package(self):
        """ Test the unorphan_package function. """
        create_package_acl(self.session)

        # Wrong package name
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.unorphan_package,
                          self.session,
                          pkg_name='asd',
                          pkg_branch='devel',
                          pkg_user='pingou',
                          user=FakeFasUser()
                          )
        self.session.rollback()

        # Wrong collection
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.unorphan_package,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='asd',
                          pkg_user='pingou',
                          user=FakeFasUser()
                          )
        self.session.rollback()

        # Package is not orphaned
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.unorphan_package,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='devel',
                          pkg_user='pingou',
                          user=FakeFasUser()
                          )
        self.session.rollback()

        # PKGDB2_BUGZILLA_* configuration not set
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.unorphan_package,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='devel',
                          pkg_user='pingou',
                          user=FakeFasUser()
                          )
        self.session.rollback()

        if pkgdb2.APP.config['PKGDB2_BUGZILLA_IN_TESTS']:
            pkgdb2.lib.utils.get_bz_email_user = mock.MagicMock()
            pkgdb2.lib.utils.get_bz_email_user.return_value = FakeFasUser
        else:
            pkgdb2.lib.utils.set_bugzilla_owner = mock.MagicMock()
        self.session.commit()

        # Orphan package
        pkgdblib.update_pkg_poc(self.session,
                                pkg_name='guake',
                                pkg_branch='devel',
                                user=FakeFasUserAdmin(),
                                pkg_poc='orphan',
                                )
        self.session.commit()

        # User cannot unorphan for someone else
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.unorphan_package,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='devel',
                          pkg_user='ralph',
                          user=FakeFasUser()
                          )
        self.session.rollback()

        # User must be a packager
        user = FakeFasUser()
        user.groups = ['cla_done']
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.unorphan_package,
                          self.session,
                          pkg_name='guake',
                          pkg_branch='devel',
                          pkg_user='pingou',
                          user=user
                          )
        self.session.rollback()

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[1].collection.branchname, 'devel')
        self.assertEqual(pkg_acl[1].package.name, 'guake')
        self.assertEqual(pkg_acl[1].point_of_contact, 'orphan')
        self.assertEqual(pkg_acl[1].status, 'Orphaned')

        pkgdblib.unorphan_package(
                          self.session,
                          pkg_name='guake',
                          pkg_branch='devel',
                          pkg_user='pingou',
                          user=FakeFasUser()
                          )
        self.session.commit()

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[1].collection.branchname, 'devel')
        self.assertEqual(pkg_acl[1].package.name, 'guake')
        self.assertEqual(pkg_acl[1].point_of_contact, 'pingou')
        self.assertEqual(pkg_acl[1].status, 'Approved')

    def test_add_branch(self):
        """ Test the add_branch function. """
        create_package_acl(self.session)

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(len(pkg_acl), 2)
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].acls[0].fas_name, 'pingou')
        self.assertEqual(pkg_acl[1].collection.branchname, 'devel')

        # Create a new collection
        new_collection = pkgdblib.model.Collection(
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

        # User cannot branch, admins are required
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.add_branch,
                          session=self.session,
                          clt_from='devel',
                          clt_to='F-19',
                          user=FakeFasUser()
                          )

        # Inexistant collection to branch from
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.add_branch,
                          session=self.session,
                          clt_from='blah',
                          clt_to='F-19',
                          user=FakeFasUserAdmin()
                          )

        # Inexistant collection to branch to
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.add_branch,
                          session=self.session,
                          clt_from='devel',
                          clt_to='blah',
                          user=FakeFasUserAdmin()
                          )

        pkgdblib.add_branch(
            session=self.session,
            clt_from='devel',
            clt_to='F-19',
            user=FakeFasUserAdmin()
        )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(len(pkg_acl), 3)
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].acls[0].fas_name, 'pingou')
        self.assertEqual(len(pkg_acl[0].acls), 2)
        self.assertEqual(pkg_acl[1].collection.branchname, 'devel')
        self.assertEqual(len(pkg_acl[1].acls), 4)
        self.assertEqual(pkg_acl[2].collection.branchname, 'F-19')
        self.assertEqual(len(pkg_acl[2].acls), 4)

    def test_get_critpath_packages(self):
        """ Test the get_critpath_packages method of pkgdblib. """
        create_package_acl(self.session)

        pkg_list = pkgdblib.get_critpath_packages(self.session)
        self.assertEqual(pkg_list, [])

        pkg_list = pkgdblib.get_critpath_packages(
            self.session, branch='devel')
        self.assertEqual(pkg_list, [])

        create_package_critpath(self.session)

        pkg_list = pkgdblib.get_critpath_packages(self.session)
        self.assertEqual(len(pkg_list), 2)
        self.assertEqual(
            pkg_list[0].point_of_contact, "kernel-maint")
        self.assertEqual(
            pkg_list[0].collection.branchname, "F-18")
        self.assertEqual(
            pkg_list[1].point_of_contact, "group::kernel-maint")
        self.assertEqual(
            pkg_list[1].collection.branchname, "devel")

        pkg_list = pkgdblib.get_critpath_packages(
            self.session, branch='devel')
        self.assertEqual(len(pkg_list), 1)
        self.assertEqual(
            pkg_list[0].point_of_contact, "group::kernel-maint")
        self.assertEqual(
            pkg_list[0].collection.branchname, "devel")


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(PkgdbLibtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
