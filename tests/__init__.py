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
pkgdb tests.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import sys
import os

from datetime import date
from datetime import timedelta

from contextlib import contextmanager
from flask import appcontext_pushed, g

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

from pkgdb2 import APP, FAS
from pkgdb2.lib import model

#DB_PATH = 'sqlite:///:memory:'
## A file database is required to check the integrity, don't ask
DB_PATH = 'sqlite:////tmp/test.sqlite'
FAITOUT_URL = 'http://209.132.184.152/faitout/'

try:
    import requests
    req = requests.get('%s/new' % FAITOUT_URL)
    if req.status_code == 200:
        DB_PATH = req.text
        print 'Using faitout at: %s' % DB_PATH
except:
    pass


class FakeFasUser(object):
    """ Fake FAS user used for the tests. """
    id = 100
    username = 'pingou'
    cla_done = True
    groups = ['packager', 'cla_done']
    bugzilla_email = 'pingou@pingoured.fr'


class FakeFasUserAdmin(object):
    """ Fake FAS user used for the tests. """
    id = 1000
    username = 'admin'
    cla_done = True
    groups = ['packager', 'cla_done', 'sysadmin-cvs']


class FakeFasGroupValid(object):
    """ Fake FAS Group used for the tests. """
    id = 10000
    name = 'perl-sig'
    group_type = 'pkgdb'


class FakeFasGroupInvalid(object):
    """ Fake FAS Group used for the tests. """
    id = 10001
    name = 'perl'
    group_type = 'tracking'


@contextmanager
def user_set(APP, user):
    """ Set the provided user as fas_user in the provided application."""

    # Hack used to remove the before_request function set by
    # flask.ext.fas_openid.FAS which otherwise kills our effort to set a
    # flask.g.fas_user.
    APP.before_request_funcs[None] = []

    def handler(sender, **kwargs):
        g.fas_user = user

    with appcontext_pushed.connected_to(handler, APP):
        yield


class Modeltests(unittest.TestCase):
    """ Model tests. """

    def __init__(self, method_name='runTest'):
        """ Constructor. """
        unittest.TestCase.__init__(self, method_name)
        self.session = None

    # pylint: disable=C0103
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        if '///' in DB_PATH:
            dbfile = DB_PATH.split('///')[1]
            if os.path.exists(dbfile):
                os.unlink(dbfile)
        self.session = model.create_tables(DB_PATH, debug=False)
        APP.before_request(FAS._check_session)

    # pylint: disable=C0103
    def tearDown(self):
        """ Remove the test.db database if there is one. """
        if '///' in DB_PATH:
            dbfile = DB_PATH.split('///')[1]
            if os.path.exists(dbfile):
                os.unlink(dbfile)

        self.session.rollback()
        self.session.close()

        if DB_PATH.startswith('postgres'):
            if 'localhost' in DB_PATH:
                model.drop_tables(DB_PATH, self.session.bind)
            else:
                db_name = DB_PATH.rsplit('/', 1)[1]
                req = requests.get(
                    '%s/clean/%s' % (FAITOUT_URL, db_name))
                print req.text


def create_collection(session):
    """ Create some basic collection for testing. """
    collection = model.Collection(
        name='Fedora',
        version='17',
        status='Active',
        owner='toshio',
        branchname='F-17',
        distTag='.fc17',
        git_branch_name='f17',
    )
    session.add(collection)

    collection = model.Collection(
        name='Fedora',
        version='18',
        status='Active',
        owner='toshio',
        branchname='F-18',
        distTag='.fc18',
        git_branch_name='f18',
    )
    session.add(collection)

    collection = model.Collection(
        name='Fedora',
        version='devel',
        status='Under Development',
        owner='kevin',
        branchname='devel',
        distTag='devel',
        git_branch_name='master',
    )
    session.add(collection)

    collection = model.Collection(
        name='EPEL',
        version='6',
        status='Active',
        owner='kevin',
        branchname='el6',
        distTag='.el6',
        git_branch_name='el6',
    )
    session.add(collection)

    session.commit()


def create_package(session):
    """ Create some basic package for testing. """
    package = model.Package(
        name='guake',
        summary='Top down terminal for GNOME',
        description='Top down terminal...',
        status='Approved',
        review_url='https://bugzilla.redhat.com/450189',
        shouldopen=None,
        upstream_url='http://guake.org',
    )
    session.add(package)

    package = model.Package(
        name='fedocal',
        summary='A web-based calendar for Fedora',
        description='Web calendar ...',
        status='Approved',
        review_url='https://bugzilla.redhat.com/915074',
        shouldopen=None,
        upstream_url='http://fedorahosted.org/fedocal',
    )
    session.add(package)

    package = model.Package(
        name='geany',
        summary='A fast and lightweight IDE using GTK2',
        description='Lightweight GNOME IDE...',
        status='Approved',
        review_url=None,
        shouldopen=None,
        upstream_url=None,
    )
    session.add(package)

    session.commit()


def create_package_listing(session):
    """ Add some package to a some collection. """
    create_collection(session)
    create_package(session)

    guake_pkg = model.Package.by_name(session, 'guake')
    fedocal_pkg = model.Package.by_name(session, 'fedocal')
    geany_pkg = model.Package.by_name(session, 'geany')

    f17_collec = model.Collection.by_name(session, 'F-17')
    f18_collec = model.Collection.by_name(session, 'F-18')
    devel_collec = model.Collection.by_name(session, 'devel')

    # Pkg: guake - Collection: F18 - Approved
    pkgltg = model.PackageListing(
        point_of_contact='pingou',
        status='Approved',
        package_id=guake_pkg.id,
        collection_id=f18_collec.id,
    )
    session.add(pkgltg)
    # Pkg: guake - Collection: devel - Approved
    pkgltg = model.PackageListing(
        point_of_contact='pingou',
        status='Approved',
        package_id=guake_pkg.id,
        collection_id=devel_collec.id,
    )
    session.add(pkgltg)
    # Pkg: fedocal - Collection: F17 - Orphaned
    pkgltg = model.PackageListing(
        point_of_contact='pingou',
        status='Approved',
        package_id=fedocal_pkg.id,
        collection_id=f17_collec.id,
    )
    session.add(pkgltg)
    # Pkg: fedocal - Collection: F18 - Orphaned
    pkgltg = model.PackageListing(
        point_of_contact='orphan',
        status='Orphaned',
        package_id=fedocal_pkg.id,
        collection_id=f18_collec.id,
    )
    session.add(pkgltg)
    # Pkg: fedocal - Collection: devel - Retired
    pkgltg = model.PackageListing(
        point_of_contact='orphan',
        status='Retired',
        package_id=fedocal_pkg.id,
        collection_id=devel_collec.id,
    )
    session.add(pkgltg)

    # Pkg: geany - Collection: F18 - Approved
    pkgltg = model.PackageListing(
        point_of_contact='pingou',
        status='Approved',
        package_id=geany_pkg.id,
        collection_id=f18_collec.id,
    )
    session.add(pkgltg)

    # Pkg: geany - Collection: devel - Approved
    pkgltg = model.PackageListing(
        point_of_contact='group::gtk-sig',
        status='Approved',
        package_id=geany_pkg.id,
        collection_id=devel_collec.id,
    )
    session.add(pkgltg)

    session.commit()


def create_package_critpath(session):
    """ Create package in critpath. """
    package = model.Package(
        name='kernel',
        summary='The Linux kernel',
        description='The kernel',
        status='Approved',
        review_url='https://bugzilla.redhat.com/123',
        shouldopen=None,
        upstream_url='http://www.kernel.org/',
    )
    session.add(package)

    f18_collec = model.Collection.by_name(session, 'F-18')
    devel_collec = model.Collection.by_name(session, 'devel')

    # Pkg: geany - Collection: F18 - Approved
    pkgltg = model.PackageListing(
        point_of_contact='kernel-maint',
        status='Approved',
        package_id=package.id,
        collection_id=f18_collec.id,
        critpath=True,
    )
    session.add(pkgltg)

    # Pkg: geany - Collection: devel - Approved
    pkgltg = model.PackageListing(
        point_of_contact='group::kernel-maint',
        status='Approved',
        package_id=package.id,
        collection_id=devel_collec.id,
        critpath=True,
    )
    session.add(pkgltg)

    session.commit()


def create_package_acl(session):
    """ Add packagers to packages. """
    create_package_listing(session)

    guake_pkg = model.Package.by_name(session, 'guake')
    fedocal_pkg = model.Package.by_name(session, 'fedocal')
    geany_pkg = model.Package.by_name(session, 'geany')
    f18_collec = model.Collection.by_name(session, 'F-18')
    devel_collec = model.Collection.by_name(session, 'devel')

    pklist_guake_f18 = model.PackageListing.by_pkgid_collectionid(
        session, guake_pkg.id, f18_collec.id)
    pklist_guake_devel = model.PackageListing.by_pkgid_collectionid(
        session, guake_pkg.id, devel_collec.id)
    pkglist_geany_devel = model.PackageListing.by_pkgid_collectionid(
        session, geany_pkg.id, devel_collec.id)

    packager = model.PackageListingAcl(
        fas_name='pingou',
        packagelisting_id=pklist_guake_f18.id,
        acl='commit',
        status='Approved',
    )
    session.add(packager)

    packager = model.PackageListingAcl(
        fas_name='pingou',
        packagelisting_id=pklist_guake_f18.id,
        acl='watchcommits',
        status='Approved',
    )
    session.add(packager)

    packager = model.PackageListingAcl(
        fas_name='pingou',
        packagelisting_id=pklist_guake_devel.id,
        acl='commit',
        status='Approved',
    )
    session.add(packager)

    packager = model.PackageListingAcl(
        fas_name='pingou',
        packagelisting_id=pklist_guake_devel.id,
        acl='approveacls',
        status='Approved',
    )
    session.add(packager)

    packager = model.PackageListingAcl(
        fas_name='pingou',
        packagelisting_id=pklist_guake_devel.id,
        acl='watchcommits',
        status='Approved',
    )
    session.add(packager)

    packager = model.PackageListingAcl(
        fas_name='toshio',
        packagelisting_id=pklist_guake_devel.id,
        acl='commit',
        status='Awaiting Review',
    )
    session.add(packager)

    packager = model.PackageListingAcl(
        fas_name='group::gtk-sig',
        packagelisting_id=pkglist_geany_devel.id,
        acl='commit',
        status='Approved',
    )
    session.add(packager)

    session.commit()


def create_package_acl2(session):
    """ Add packagers to packages. """
    create_package_listing(session)

    guake_pkg = model.Package.by_name(session, 'guake')
    fedocal_pkg = model.Package.by_name(session, 'fedocal')
    geany_pkg = model.Package.by_name(session, 'geany')

    f17_collec = model.Collection.by_name(session, 'F-17')
    f18_collec = model.Collection.by_name(session, 'F-18')
    devel_collec = model.Collection.by_name(session, 'devel')

    pklist_guake_f18 = model.PackageListing.by_pkgid_collectionid(
        session, guake_pkg.id, f18_collec.id)
    pklist_guake_devel = model.PackageListing.by_pkgid_collectionid(
        session, guake_pkg.id, devel_collec.id)

    pkglist_geany_devel = model.PackageListing.by_pkgid_collectionid(
        session, geany_pkg.id, devel_collec.id)

    pkglist_fedocal_devel = model.PackageListing.by_pkgid_collectionid(
        session, fedocal_pkg.id, devel_collec.id)
    pkglist_fedocal_f18 = model.PackageListing.by_pkgid_collectionid(
        session, fedocal_pkg.id, f18_collec.id)
    pkglist_fedocal_f17 = model.PackageListing.by_pkgid_collectionid(
        session, fedocal_pkg.id, f17_collec.id)

    packager = model.PackageListingAcl(
        fas_name='pingou',
        packagelisting_id=pklist_guake_f18.id,
        acl='commit',
        status='Approved',
    )
    session.add(packager)

    packager = model.PackageListingAcl(
        fas_name='pingou',
        packagelisting_id=pklist_guake_f18.id,
        acl='watchcommits',
        status='Approved',
    )
    session.add(packager)

    packager = model.PackageListingAcl(
        fas_name='pingou',
        packagelisting_id=pklist_guake_devel.id,
        acl='commit',
        status='Approved',
    )
    session.add(packager)

    packager = model.PackageListingAcl(
        fas_name='pingou',
        packagelisting_id=pklist_guake_devel.id,
        acl='watchcommits',
        status='Approved',
    )
    session.add(packager)

    packager = model.PackageListingAcl(
        fas_name='toshio',
        packagelisting_id=pklist_guake_devel.id,
        acl='commit',
        status='Awaiting Review',
    )
    session.add(packager)

    packager = model.PackageListingAcl(
        fas_name='spot',
        packagelisting_id=pklist_guake_devel.id,
        acl='commit',
        status='Approved',
    )
    session.add(packager)

    packager = model.PackageListingAcl(
        fas_name='group::gtk-sig',
        packagelisting_id=pkglist_geany_devel.id,
        acl='commit',
        status='Approved',
    )
    session.add(packager)

    packager = model.PackageListingAcl(
        fas_name='pingou',
        packagelisting_id=pkglist_fedocal_devel.id,
        acl='commit',
        status='Approved',
    )
    session.add(packager)

    packager = model.PackageListingAcl(
        fas_name='toshio',
        packagelisting_id=pkglist_fedocal_devel.id,
        acl='commit',
        status='Approved',
    )
    session.add(packager)

    packager = model.PackageListingAcl(
        fas_name='pingou',
        packagelisting_id=pkglist_fedocal_f18.id,
        acl='commit',
        status='Approved',
    )
    session.add(packager)

    packager = model.PackageListingAcl(
        fas_name='pingou',
        packagelisting_id=pkglist_fedocal_f17.id,
        acl='commit',
        status='Approved',
    )
    session.add(packager)

    session.commit()


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Modeltests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
