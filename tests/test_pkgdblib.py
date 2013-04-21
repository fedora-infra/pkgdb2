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
                   create_package, create_package_listing,
                   create_person_package)


class PkgdbLibtests(Modeltests):
    """ PkgdbLib tests. """

    def test_add_package(self):
        """ Test the add_package function. """
        create_collection(self.session)
        msg = pkgdblib.add_package(self.session,
                                    pkg_name='guake',
                                    pkg_summary='Drop down terminal',
                                    pkg_status='Approved',
                                    pkg_collection='F-18',
                                    pkg_owner='pingou',
                                    pkg_reviewURL=None,
                                    pkg_shouldopen=None,
                                    pkg_upstreamURL='http://guake.org',
                                    user=FakeFasUser())
        self.assertEqual(msg, 'Package created')
        self.session.commit()
        packages = model.Package.all(self.session)
        self.assertEqual(1, len(packages))
        self.assertEqual('guake', packages[0].name)

        pkgdblib.add_package(self.session,
                             pkg_name='geany,fedocal',
                             pkg_summary='Drop down terminal',
                             pkg_status='Approved',
                             pkg_collection='devel, F-18',
                             pkg_owner='pingou',
                             pkg_reviewURL=None,
                             pkg_shouldopen=None,
                             pkg_upstreamURL=None,
                             user=FakeFasUser())
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
        self.assertEqual(pkg_acl[0].people[0].user, 'pingou')

    def test_set_acl_package(self):
        """ Test the set_acl_package function. """
        self.test_add_package()

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

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.set_acl_package,
                          self.session,
                          pkg_name='guake',
                          clt_name='F-17',
                          pkg_user='pingou',
                          acl='nothing',
                          status='Appr',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        self.assertRaises(IntegrityError,
                          pkgdblib.set_acl_package,
                          self.session,
                          pkg_name='guake',
                          clt_name='F-18',
                          acl='nothing',
                          pkg_user='pingou',
                          status='Appro',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        self.assertRaises(IntegrityError,
                          pkgdblib.set_acl_package,
                          self.session,
                          pkg_name='guake',
                          clt_name='F-18',
                          pkg_user='pingou',
                          acl='nothing',
                          status='Approved',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        pkgdblib.set_acl_package(self.session,
                                 pkg_name='guake',
                                 clt_name='F-18',
                                 pkg_user='pingou',
                                 acl='commit',
                                 status='Approved',
                                 user=FakeFasUser(),
                                 )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(len(pkg_acl[0].people), 1)

    def test_pkg_change_owner(self):
        """ Test the pkg_change_owner function. """
        self.test_add_package()

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.pkg_change_owner,
                          self.session,
                          pkg_name='test',
                          clt_name='F-17',
                          user=FakeFasUser(),
                          pkg_owner='toshio',
                          )
        self.session.rollback()

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.pkg_change_owner,
                          self.session,
                          pkg_name='guake',
                          clt_name='F-17',
                          user=FakeFasUser(),
                          pkg_owner='toshio',
                          )
        self.session.rollback()

        fake_user = FakeFasUser()
        fake_user.username = 'test'
        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.pkg_change_owner,
                          self.session,
                          pkg_name='guake',
                          clt_name='F-18',
                          user=fake_user,
                          pkg_owner='toshio',
                          )
        self.session.rollback()

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].owner, 'pingou')

        pkgdblib.pkg_change_owner(self.session,
                                 pkg_name='guake',
                                 clt_name='F-18',
                                 user=FakeFasUser(),
                                 pkg_owner='toshio',
                                 )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].owner, 'toshio')

        user = FakeFasUser()
        user.username = 'toshio'
        pkgdblib.pkg_change_owner(self.session,
                                 pkg_name='guake',
                                 clt_name='F-18',
                                 user=user,
                                 pkg_owner='orphan',
                                 )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].owner, 'orphan')
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
                                       pkg_owner=None,
                                       orphaned=None,
                                       deprecated=None,
                                       )
        self.assertEqual(len(pkgs), 1)
        self.assertEqual(pkgs[0].name, 'guake')
        self.assertEqual(pkgs[0].upstream_url, 'http://guake.org')

        pkgs = pkgdblib.search_package(self.session,
                                       pkg_name='gu*',
                                       clt_name='F-18',
                                       pkg_owner=None,
                                       orphaned=True,
                                       deprecated=None,
                                       )
        self.assertEqual(len(pkgs), 0)

        pkgs = pkgdblib.search_package(self.session,
                                       pkg_name='gu*',
                                       clt_name='F-18',
                                       pkg_owner=None,
                                       orphaned=None,
                                       deprecated=True,
                                       )
        self.assertEqual(len(pkgs), 0)

    def test_pkg_deprecate(self):
        """ Test the pkg_deprecate function. """
        self.test_add_package()

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.pkg_deprecate,
                          self.session,
                          pkg_name='test',
                          clt_name='F-17',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        self.assertRaises(pkgdblib.PkgdbException,
                          pkgdblib.pkg_deprecate,
                          self.session,
                          pkg_name='guake',
                          clt_name='F-17',
                          user=FakeFasUser(),
                          )
        self.session.rollback()

        pkgdblib.pkg_deprecate(self.session,
                               pkg_name='guake',
                               clt_name='F-18',
                               user=FakeFasUser()
                               )

        pkg_acl = pkgdblib.get_acl_package(self.session, 'guake')
        self.assertEqual(pkg_acl[0].collection.branchname, 'F-18')
        self.assertEqual(pkg_acl[0].package.name, 'guake')
        self.assertEqual(pkg_acl[0].owner, 'pingou')
        self.assertEqual(pkg_acl[0].status, 'Deprecated')

    def test_search_collection(self):
        """ Test the search_collection function. """
        create_collection(self.session)

        collections = pkgdblib.search_collection(self.session, 'EPEL*')
        self.assertEqual(len(collections), 0)

        collections = pkgdblib.search_collection(self.session, 'F-*', True)
        self.assertEqual(len(collections), 0)

        collections = pkgdblib.search_collection(self.session, 'F-*', False)
        self.assertEqual("Collection(u'Fedora', u'18', u'Active', u'toshio', "
                         "publishurltemplate=None, pendingurltemplate=None,"
                         " summary=u'Fedora 18 release', description=None)",
                         collections[0].__repr__())

    def test_add_collection(self):
        """ Test the add_collection function. """
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
                                user=FakeFasUser(),
                                )
        self.session.commit()
        collection = model.Collection.by_name(self.session, 'F-19')
        self.assertEqual("Collection(u'Fedora', u'19', u'Active', u'pingou', "
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

        create_person_package(self.session)

        acls = pkgdblib.get_acl_packager(self.session, 'pingou')
        self.assertEqual(len(acls), 2)
        self.assertEqual(acls[0].packagelist.package.name, 'guake')
        self.assertEqual(acls[0].packagelist.collection.branchname, 'F-18')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(PkgdbLibtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
