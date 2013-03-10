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

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.exc import NoResultFound


class PkgdbException(Exception):
    """ Generic Exception object used to throw pkgdb specific error.
    """
    pass


def create_session(db_url, debug=False, pool_recycle=3600):
    """ Create the Session object to use to query the database.

    :arg db_url: URL used to connect to the database. The URL contains
    information with regards to the database engine, the host to connect
    to, the user and password and the database name.
      ie: <engine>://<user>:<password>@<host>/<dbname>
    :kwarg debug: a boolean specifying wether we should have the verbose
        output of sqlalchemy or not.
    :return a Session that can be used to query the database.
    """
    engine = sqlalchemy.create_engine(db_url, echo=debug,
        pool_recycle=pool_recycle)
    scopedsession = scoped_session(sessionmaker(bind=engine))
    return scopedsession


def add_package(session, pkg_name, pkg_summary, pkg_status,
                pkg_collection, pkg_owner, pkg_reviewURL=None,
                pkg_shouldopen=None, pkg_upstreamURL=None):
    """ Create a new Package in the database and adds the corresponding
    PackageListing entry.

    :arg session: session with which to connect to the database
    :arg pkg_name:
    ...
    """
    package = model.Package(name=pkg_name,
                            summary=pkg_summary,
                            status=pkg_status,
                            review_url=pkg_reviewURL,
                            shouldopen=pkg_shouldopen,
                            upstream_url=pkg_upstreamURL
                            )
    session.add(package)
    session.flush()
    collection = model.Collection.by_name(session, pkg_collection)
    pkglisting = package.create_listing(owner=pkg_owner,
                                       collection=collection,
                                       statusname=pkg_status)
    session.add(pkglisting)
    session.flush()


def get_acl_package(session, pkg_name):
    """ Return the ACLs for the specified package.

    :arg session: session with which to connect to the database
    :arg pkg_name: the name of the package to retrieve the ACLs for
    """
    package = model.Package.by_name(session, pkg_name)
    pkglisting = model.PackageListing.by_package_id(session, package.id)
    return pkglisting


def set_acl_package(session, pkg_name, clt_name, user, acl, status):
    """ Return the ACLs for the specified package.

    :arg session: session with which to connect to the database
    :arg pkg_name: the name of the package
    :arg colt_name: the name of the collection
    :arg user: the FAS user for which the ACL should be set/change
    :arg status: the status of the ACLs
    """
    try:
        package = model.Package.by_name(session, pkg_name)
    except NoResultFound:
        raise PkgdbException('No package found by this name')

    try:
        collection = model.Collection.by_name(session, clt_name)
    except NoResultFound:
        raise PkgdbException('No collection found by this name')

    pkglisting = model.PackageListing.by_pkgid_collectionid(session,
                                                            package.id,
                                                            collection.id)
    personpkg = model.PersonPackageListing.get_or_create(session,
                                                         user.id,
                                                         pkglisting.id)
    personpkgacl = model.PersonPackageListingAcl.get_or_create_personpkgid_acl(session,
                                                                      personpkg.id,
                                                                      acl)
    personpkgacl.status = status
    session.add(personpkgacl)
    session.flush()
