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
from sqlalchemy.exc import SQLAlchemyError


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
    engine = sqlalchemy.create_engine(db_url,
                                      echo=debug,
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
    if ',' in pkg_name:
        pkg_name = [item.strip() for item in pkg_name.split(',')]
    else:
        pkg_name = [pkg_name]
    if ',' in pkg_collection:
        pkg_collection = [item.strip() for item in pkg_collection.split(',')]
    else:
        pkg_collection = [pkg_collection]

    for pkg in pkg_name:
        package = model.Package(name=pkg,
                                summary=pkg_summary,
                                status=pkg_status,
                                review_url=pkg_reviewURL,
                                shouldopen=pkg_shouldopen,
                                upstream_url=pkg_upstreamURL
                                )
        session.add(package)
    try:
        session.flush()
    except SQLAlchemyError, err:  # pragma: no cover
        raise PkgdbException('Could not add packages')

    for collec in pkg_collection:
        collection = model.Collection.by_name(session, collec)
        pkglisting = package.create_listing(owner=pkg_owner,
                                            collection=collection,
                                            statusname=pkg_status)
        session.add(pkglisting)
    try:
        session.flush()
        return 'Package created'
    except SQLAlchemyError, err:  # pragma: no cover
        raise PkgdbException('Could not add packages')


def get_acl_package(session, pkg_name):
    """ Return the ACLs for the specified package.

    :arg session: session with which to connect to the database
    :arg pkg_name: the name of the package to retrieve the ACLs for
    """
    package = model.Package.by_name(session, pkg_name)
    pkglisting = model.PackageListing.by_package_id(session, package.id)
    return pkglisting


def set_acl_package(session, pkg_name, clt_name, pkg_user, acl, status,
                    user):
    """ Set the specified ACLs for the specified package.

    :arg session: session with which to connect to the database
    :arg pkg_name: the name of the package
    :arg colt_name: the name of the collection
    :arg pkg_user: the FAS user for which the ACL should be set/change
    :arg status: the status of the ACLs
    :arg user: the user making the action
    """
    try:
        package = model.Package.by_name(session, pkg_name)
    except NoResultFound:
        raise PkgdbException('No package found by this name')

    try:
        collection = model.Collection.by_name(session, clt_name)
    except NoResultFound:
        raise PkgdbException('No collection found by this name')

    ## TODO: check is user is allowed to change package

    pkglisting = model.PackageListing.by_pkgid_collectionid(session,
                                                            package.id,
                                                            collection.id)
    ## TODO: how do we get pkg_user's object?
    personpkg = model.PersonPackageListing.get_or_create(session,
                                                         pkg_user.id,
                                                         pkglisting.id)
    personpkgacl = model.PersonPackageListingAcl.get_or_create_personpkgid_acl(
                    session, personpkg.id, acl)
    personpkgacl.status = status
    session.add(personpkgacl)
    session.flush()


def pkg_change_owner(session, pkg_name, clt_name, pkg_owner, user):
    """ Change the owner of a package.

    :arg session: session with which to connect to the database
    :arg pkg_name: the name of the package
    :arg clt_name: the name of the collection
    :arg pkg_owner: name of the new owner of the package.
    :arg user: the user making the action
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

    ## TODO: Check if flask.g.fas_user is an admin

    if pkglisting.owner == user.name:
        pkglisting.owner = pkg_owner
        if pkg_owner == 'orphan':
            pkglisting.status = 'Orphaned'
        session.add(pkglisting)
        session.flush()
    else:
        raise PkgdbException('You are now allowed to change the owner.')


def pkg_deprecate(session, pkg_name, clt_name, user):
    """ Deprecates a package.

    :arg session: session with which to connect to the database
    :arg pkg_name: the name of the package
    :arg clt_name: the name of the collection
    :arg user: the user making the action
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

    ## TODO: Check if user is allowed to do the action

    pkglisting.status = 'Deprecated'
    session.add(pkglisting)
    session.flush()


def search_package(session, pkg_name, clt_name, pkg_owner, orphaned,
                   deprecated):
    """ Return the list of packages matching the given criteria.

    :arg session: session with which to connect to the database
    :arg pkg_name: the name of the package
    :arg clt_name: the name of the collection
    :arg pkg_owner: name of the new owner of the package
    :arg orphaned: a boolean to restricted to orphaned packages
    :arg deprecated: a boolean to restricted to deprecated packages
    """
    if '*' in pkg_name:
        pkg_name = pkg_name.replace('*', '%')
    if orphaned:
        pkg_name = 'orphan'
    status = None
    if deprecated:
        status = 'Deprecated'

    collection = model.Collection.by_name(session, clt_name)

    return model.PackageListing.search(session,
                                       pkg_name=pkg_name,
                                       clt_id=collection.id,
                                       pkg_owner=pkg_owner,
                                       pkg_status=status)


def search_collection(session, clt_name, eold=False):
    """ Return the list of Collection matching the given criteria.

    :arg session: session with which to connect to the database
    :arg clt_name: pattern to match the collection
    :kwarg eold: boolean to filter in or out the collection which have
        been "end of life"'d (defaults to False)
    """
    if '*' in clt_name:
        clt_name = clt_name.replace('*', '%')
    status = None
    if eold:
        status = 'EOL'

    return model.Collection.search(session,
                                   clt_name=clt_name,
                                   clt_status=status)


def add_collection(session, clt_name, clt_version, clt_status,
                   clt_publishurl, clt_pendingurl, clt_summary,
                   clt_description, clt_branchname, clt_disttag,
                   clt_gitbranch, user):
    """ Add a new collection

    
    """

    ## TODO: check if user is allowed to add a new collection

    collection = model.Collection(
        name=clt_name,
        version=clt_version,
        status=clt_status,
        owner=user.id,
        publishURLTemplate=clt_publishurl,
        pendingURLTemplate=clt_pendingurl,
        summary=clt_summary,
        description=clt_description,
        branchname=clt_branchname,
        distTag=clt_disttag,
        git_branch_name=clt_gitbranch,
    )
    try:
        session.add(collection)
        session.flush()
        return 'Collection "%s" created' % collection.branchname
    except SQLAlchemyError, err:  # pragma: no cover
        raise PkgdbException('Could not add Collection to the database.')


def update_collection_status(session, clt_branchname, clt_status):
    """ Update the status of a collection.

    :arg session: session with which to connect to the database
    :arg clt_branchname: branchname of the collection
    :arg clt_status: status of the collection
    """
    try:
        collection = model.Collection.by_name(session, clt_branchname)
        
        if collection.status != clt_status:
            collection.status = clt_status
            message = 'Collection updated to "%s"' % clt_status
        else:
            message = 'Collection "%s" already had this status' % clt_branchname
        session.add(collection)
        session.flush()
        return message
    except NoResultFound:  # pragma: no cover
        raise PkgdbException('Could not find collection "%s"' %
            clt_branchname)
    except SQLAlchemyError, err:  # pragma: no cover
        raise PkgdbException('Could not update the status of collection'
            '"%s".' % clt_branchname)
