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
from tests import (FakeFasUser, FakeFasUserAdmin, Modeltests,
                   create_collection, create_package,
                   create_package_listing, create_package_acl)


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
                          pkg_status='Approved',
                          pkg_collection='F-18',
                          pkg_poc='group::tests',
                          pkg_reviewURL=None,
                          pkg_shouldopen=None,
                          pkg_upstreamURL='http://example.org',
                          user=FakeFasUserAdmin()
                          )
        self.session.rollback()

        msg = pkgdblib.add_package(self.session,
                                    pkg_name='guake',
                                    pkg_summary='Drop down terminal',
                                    pkg_status='Approved',
                                    pkg_collection='F-18',
                                    pkg_poc='ralph',
                                    pkg_reviewURL=None,
                                    pkg_shouldopen=None,
                                    pkg_upstreamURL='http://guake.org',
                                    user=FakeFasUserAdmin())
        self.assertEqual(msg, 'Package created')
        self.session.commit()
        packages = model.Package.all(self.session)
        self.assertEqual(1, len(packages))
        self.assertEqual('guake', packages[0].name)

        pkgdblib.add_package(self.session,
                             pkg_name='geany',
                             pkg_summary='GTK IDE',
                             pkg_status='Approved',
                             pkg_collection='devel, F-18',
                             pkg_poc='ralph',
                             pkg_reviewURL=None,
                             pkg_shouldopen=None,
                             pkg_upstreamURL=None,
                             user=FakeFasUserAdmin())
        self.session.commit()
        packages = model.Package.all(self.session)
        self.assertEqual(2, len(packages))
        self.assertEqual('guake', packages[0].name)
        self.assertEqual('geany', packages[1].name)

        pkgdblib.add_package(self.session,
                             pkg_name='fedocal',
                             pkg_summary='web calendar for Fedora',
                             pkg_status='Approved',
                             pkg_collection='devel, F-18',
                             pkg_poc='group::infra-sig',
                             pkg_reviewURL=None,
                             pkg_shouldopen=None,
                             pkg_upstreamURL=None,
                             user=FakeFasUserAdmin())
        self.session.commit()
        packages = model.Package.all(self.session)
        self.assertEqual(3, len(packages))
        self.assertEqual('guake', packages[0].name)
        self.assertEqual('geany', packages[1].name)
        self.assertEqual('fedocal', packages[2].name)

    def test_get_acl_package(self):
        """ Test the get_acl_package function. """
        self.test_add_package()
        self.session.commit()

        packages = model.Package.all(self.session)
        self.assertEqual(3, len(packages))
        self.assertEqual('guake', packages[0].name)

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].acls[0].fas_name, 'ralph')

    def test_set_acl_package(self):
        """ Test the set_acl_package function. """
        self.test_add_package()

        # Not allowed to set acl on non-existant package
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.set_acl_package,
                          self.session,
                          pkg_name='test',
                          clt_name='F-17',
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
                          clt_name='F-16',
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
                          clt_name='F-18',
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
                          clt_name='F-18',
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
                          clt_name='F-18',
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
                          clt_name='F-18',
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
                          clt_name='F-18',
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
                          clt_name='F-18',
                          pkg_user='group::perl',
                          acl='commit',
                          status='Approved',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        # You can ask for new ACLs
        pkgdblib.set_acl_package(self.session,
                                 pkg_name='guake',
                                 clt_name='F-18',
                                 pkg_user='pingou',
                                 acl='approveacls',
                                 status='Awaiting Review',
                                 user=FakeFasUser(),
                                 )

        # You can obsolete your own ACLs
        pkgdblib.set_acl_package(self.session,
                                 pkg_name='guake',
                                 clt_name='F-18',
                                 pkg_user='pingou',
                                 acl='approveacls',
                                 status='Obsolete',
                                 user=FakeFasUser(),
                                 )

        # You can remove your own ACLs
        pkgdblib.set_acl_package(self.session,
                                 pkg_name='guake',
                                 clt_name='F-18',
                                 pkg_user='pingou',
                                 acl='approveacls',
                                 status='Removed',
                                 user=FakeFasUser(),
                                 )

        # An admin can approve you ACLs
        pkgdblib.set_acl_package(self.session,
                                 pkg_name='guake',
                                 clt_name='F-18',
                                 pkg_user='pingou',
                                 acl='commit',
                                 status='Approved',
                                 user=FakeFasUserAdmin(),
                                 )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(len(pkg_acl[0].acls), 6)

    def test_pkg_change_poc(self):
        """ Test the pkg_change_poc function. """
        self.test_add_package()

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.pkg_change_poc,
                          self.session,
                          pkg_name='test',
                          clt_name='F-17',
                          user=FakeFasUser(),
                          pkg_poc='toshio',
                          )
        self.session.rollback()

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.pkg_change_poc,
                          self.session,
                          pkg_name='guake',
                          clt_name='F-16',
                          user=FakeFasUser(),
                          pkg_poc='toshio',
                          )
        self.session.rollback()

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.pkg_change_poc,
                          self.session,
                          pkg_name='guake',
                          clt_name='F-18',
                          user=FakeFasUser(),
                          pkg_poc='toshio',
                          )
        self.session.rollback()

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].point_of_contact, 'ralph')

        # PoC can change PoC
        user = FakeFasUser()
        user.username = 'ralph'
        pkgdblib.pkg_change_poc(self.session,
                                 pkg_name='guake',
                                 clt_name='F-18',
                                 user=user,
                                 pkg_poc='toshio',
                                 )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].point_of_contact, 'toshio')

        # Admin can change PoC
        pkgdblib.pkg_change_poc(self.session,
                                 pkg_name='guake',
                                 clt_name='F-18',
                                 user=FakeFasUserAdmin(),
                                 pkg_poc='kevin',
                                 )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].point_of_contact, 'kevin')

        user = FakeFasUser()
        user.username = 'kevin'
        pkgdblib.pkg_change_poc(self.session,
                                 pkg_name='guake',
                                 clt_name='F-18',
                                 user=user,
                                 pkg_poc='orphan',
                                 )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].point_of_contact, 'orphan')
        self.assertEqual(pkg_acl[0].status, 'Orphaned')

    def test_create_session(self):
        """ Test the create_session function. """
        session = pkgdblib.create_session('sqlite:///:memory:')
        self.assertTrue(session is not None)

    def test_search_package(self):
        """ Test the search_package function. """
        self.test_add_package()
        pkgs = pkgdblib.search_package(self.session,
                                       pkg_name='gu*',
                                       clt_name='F-18',
                                       pkg_poc=None,
                                       orphaned=None,
                                       status=None,
                                       )
        self.assertEqual(len(pkgs), 1)
        self.assertEqual(pkgs[0].name, 'guake')
        self.assertEqual(pkgs[0].upstream_url, 'http://guake.org')

        pkgs = pkgdblib.search_package(self.session,
                                       pkg_name='gu*',
                                       clt_name='F-18',
                                       pkg_poc=None,
                                       orphaned=True,
                                       status=None,
                                       )
        self.assertEqual(len(pkgs), 0)

        pkgs = pkgdblib.search_package(self.session,
                                       pkg_name='gu*',
                                       clt_name='F-18',
                                       pkg_poc=None,
                                       orphaned=None,
                                       status='Deprecated',
                                       )
        self.assertEqual(len(pkgs), 0)

    def test_update_pkg_status(self):
        """ Test the update_pkg_status function. """
        self.test_add_package()

        # Wrong package
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.update_pkg_status,
                          self.session,
                          pkg_name='test',
                          clt_name='F-17',
                          status='Deprecated',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        # Wrong collection
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.update_pkg_status,
                          self.session,
                          pkg_name='guake',
                          clt_name='F-16',
                          status='Deprecated',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        # User not allowed to deprecate the package on F-18
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.update_pkg_status,
                          self.session,
                          pkg_name='guake',
                          clt_name='F-18',
                          status='Deprecated',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        # Wrong status
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.update_pkg_status,
                          self.session,
                          pkg_name='guake',
                          clt_name='F-18',
                          status='Depreasdcated',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        # User not allowed to change status to Allowed
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.update_pkg_status,
                          self.session,
                          pkg_name='guake',
                          clt_name='F-18',
                          status='Allowed',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        # Admin can retire package
        pkgdblib.update_pkg_status(self.session,
                               pkg_name='guake',
                               clt_name='F-18',
                               status='Deprecated',
                               user=FakeFasUserAdmin()
                               )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].point_of_contact, 'orphan')
        self.assertEqual(pkg_acl[0].status, 'Deprecated')

    def test_search_collection(self):
        """ Test the search_collection function. """
        create_collection(self.session)

        collections = pkgdblib.search_collection(self.session, 'EPEL*')
        self.assertEqual(len(collections), 0)

        collections = pkgdblib.search_collection(self.session, 'F-*', True)
        self.assertEqual(len(collections), 0)

        collections = pkgdblib.search_collection(self.session, 'F-*', False)
        self.assertEqual("Collection(u'Fedora', u'17', u'Active', u'toshio', "
                         "publishurltemplate=None, pendingurltemplate=None,"
                         " summary=u'Fedora 17 release', description=None)",
                         collections[0].__repr__())

    def test_add_collection(self):
        """ Test the add_collection function. """

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.add_collection,
                          session=self.session,
                          clt_name='Fedora',
                          clt_version='19',
                          clt_status='Active',
                          clt_publishurl=None,
                          clt_pendingurl=None,
                          clt_summary='Fedora 19 release',
                          clt_description='Fedora 19 collection',
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
                                clt_publishurl=None,
                                clt_pendingurl=None,
                                clt_summary='Fedora 19 release',
                                clt_description='Fedora 19 collection',
                                clt_branchname='F-19',
                                clt_disttag='.fc19',
                                clt_gitbranch='f19',
                                user=FakeFasUserAdmin(),
                                )
        self.session.commit()
        collection = model.Collection.by_name(self.session, 'F-19')
        self.assertEqual("Collection(u'Fedora', u'19', u'Active', u'admin', "
                         "publishurltemplate=None, pendingurltemplate=None, "
                         "summary=u'Fedora 19 release', "
                         "description=u'Fedora 19 collection')",
                         collection.__repr__())

    def test_update_collection_status(self):
        """ Test the update_collection_status function. """
        create_collection(self.session)

        collection = model.Collection.by_name(self.session, 'F-18')
        self.assertEqual(collection.status, 'Active')

        pkgdblib.update_collection_status(self.session, 'F-18', 'EOL')
        self.session.commit()
        msg = pkgdblib.update_collection_status(self.session, 'F-18',
                                                'EOL')
        self.assertEqual(msg, 'Collection "F-18" already had this status')
        collection = model.Collection.by_name(self.session, 'F-18')
        self.assertEqual(collection.status, 'EOL')

    def test_search_packagers(self):
        """ Test the search_packagers function. """
        pkg = pkgdblib.search_packagers(self.session, 'pin*')
        self.assertEqual(pkg, [])

        create_package_listing(self.session)

        pkg = pkgdblib.search_packagers(self.session, 'pi*')
        self.assertEqual(len(pkg), 1)
        self.assertEqual(pkg[0][0], 'pingou')

    def test_get_acl_packager(self):
        """ Test the get_acl_packager function. """
        acls = pkgdblib.get_acl_packager(self.session, 'pingou')
        self.assertEqual(acls, [])

        create_package_acl(self.session)

        acls = pkgdblib.get_acl_packager(self.session, 'pingou')
        self.assertEqual(len(acls), 4)
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
        self.assertEqual(len(pending_acls), 4)

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

        pkg_status = ['Approved', 'Deprecated', 'Orphaned', 'Removed']
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


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(PkgdbLibtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
