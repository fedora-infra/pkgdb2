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

import pkgdb
import pkgdb.lib.model


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
                pkg_collection, pkg_poc, user, pkg_reviewURL=None,
                pkg_shouldopen=None, pkg_upstreamURL=None):
    """ Create a new Package in the database and adds the corresponding
    PackageListing entry.

    :arg session: session with which to connect to the database
    :arg pkg_name:
    ...
    """
    ## TODO: check user is allowed to perform this action
    if user is None:
        raise PkgdbException("You're not allowed to add a package")

    if isinstance(pkg_name, (str, unicode)):
        if ',' in pkg_name:
            pkg_name = [item.strip() for item in pkg_name.split(',')]
        else:
            pkg_name = [pkg_name]

    if isinstance(pkg_collection, (str, unicode)):
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

        for collec in pkg_collection:
            collection = model.Collection.by_name(session, collec)
            pkglisting = package.create_listing(point_of_contact=pkg_poc,
                                                collection=collection,
                                                statusname=pkg_status)
            session.add(pkglisting)
    try:
        session.flush()
    except SQLAlchemyError, err:  # pragma: no cover
        raise PkgdbException('Could not add packages to collections')

    # Add all new ACLs to the owner
    for pkg in pkg_name:
        for collec in pkg_collection:
            for acl in ['commit', 'watchbugzilla', 'watchcommits',
                        'approveacls']:
                set_acl_package(session=session,
                                pkg_name=pkg,
                                clt_name=collec,
                                pkg_user=pkg_poc,
                                acl=acl,
                                status='Approved',
                                user=user)
    try:
        session.flush()
        return 'Package created'
    except SQLAlchemyError, err:  # pragma: no cover
        raise PkgdbException('Could not add ACLs')


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

    if not pkgdb.is_pkg_admin(user, package.name, clt_name):
        if user.username != pkg_user:
            raise PkgdbException('You are not allowed to update ACLs of '
            'someone else.')
        elif status not in \
                ('Awaiting Review', 'Removed', 'Obsolete') \
                and acl not in pkgdb.APP.config['AUTO_APPROVE']:
            raise PkgdbException(
                'You are not allowed to approve or deny '
                'ACLs for yourself.')

    try:
        pkglisting = model.PackageListing.by_pkgid_collectionid(
            session,
            package.id,
            collection.id)
    except NoResultFound:
        pkglisting = package.create_listing(owner=pkg_user,
                                            collection=collection,
                                            statusname='Approved')
        session.add(pkglisting)
        session.flush()
    ## TODO: how do we get pkg_user's object?
    personpkg = model.PackageListingAcl.get_or_create(session,
                                                      pkg_user,
                                                      pkglisting.id,
                                                      acl=acl,
                                                      status=status)
    personpkg.status = status
    session.flush()


def pkg_change_poc(session, pkg_name, clt_name, pkg_poc, user):
    """ Change the point of contact of a package.

    :arg session: session with which to connect to the database
    :arg pkg_name: the name of the package
    :arg clt_name: the branchname of the collection
    :arg pkg_poc: name of the new point of contact for the package.
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

    if pkglisting.point_of_contact == user.username \
            or pkglisting.point_of_contact == 'orphan' \
            or pkgdb.is_pkgdb_admin(user):
        pkglisting.point_of_contact = pkg_poc
        if pkg_poc == 'orphan':
            pkglisting.status = 'Orphaned'
        elif pkglisting.status in ('Orphaned', 'Deprecated'):
            pkglisting.status = 'Approved'
        session.add(pkglisting)
        session.flush()
    else:
        raise PkgdbException('You are now allowed to change the owner.')

    return 'Point of contact of branch: %s of package: %s has been changed ' \
        'to %s' %(clt_name, pkg_name, pkg_poc)

def update_pkg_status(session, pkg_name, clt_name, status, user,
                      poc='orphan'):
    """ Update the status of a package.

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

    if status not in ['Approved', 'Removed', 'Deprecated', 'Orphaned']:
        raise PkgdbException('Status not allowed for a package : %s' %
                             status)

    pkglisting = model.PackageListing.by_pkgid_collectionid(session,
                                                            package.id,
                                                            collection.id)

    if status == 'Deprecated':
        # Admins can deprecate everything
        # Users can deprecate Fedora devel and EPEL branches
        if pkgdb.is_pkgdb_admin(user) \
                or (collection.name == 'Fedora'
                    and collection.version == 'devel') \
                or collection.name == 'EPEL':
            pkglisting.status = 'Deprecated'
            pkglisting.point_of_contact = 'orphan'
            session.add(pkglisting)
            session.flush()
        else:
            raise PkgdbException('You are now allowed to deprecate the '
                'package: %s on branch %s.' % (package.name,
                collection.branchname))
    elif status == 'Orphaned':
        pkglisting.status = 'Orphaned'
        pkglisting.point_of_contact = 'orphan'
        session.add(pkglisting)
        session.flush()
    elif pkgdb.is_pkgdb_admin(user):
        if status == 'Approved':
            if pkglisting.status == 'Orphaned' and poc == 'orphan':
                raise PkgdbException('You need to specify the point of '
                    'contact of this package for this branch to un-orphan '
                    'it')
            pkglisting.point_of_contact = poc

        pkglisting.status = status
        session.add(pkglisting)
        session.flush()
    else:
        raise PkgdbException(
            'You are now allowed to update the status of '
            'the package: %s on branch %s to %s.' % (
            package.name, collection.branchname, status)
        )


def search_package(session, pkg_name, clt_name=None, pkg_poc=None,
                   orphaned=False, status='Approved', page=None,
                   limit=None, count=False):
    """ Return the list of packages matching the given criteria.

    :arg session: session with which to connect to the database
    :arg pkg_name: the name of the package
    :kwarg clt_name: branchname of the collection to search
    :kwarg pkg_poc: point of contact of the packages searched
    :kwarg orphaned: boolean to restrict search to orphaned packages
    :kwarg deprecated: boolean to restrict search to deprecated packages
    :kwarg page: the page number to apply to the results
    :kwarg limit: the number of results to return
    :kwarg count: a boolean to return the result of a COUNT query
            if true, returns the data if false (default).

    """
    if '*' in pkg_name:
        pkg_name = pkg_name.replace('*', '%')
    if orphaned:
        pkg_poc = 'orphan'
        pkg_status = 'Orphaned'

    if limit is not None:
        try:
            int(limit)
        except ValueError:
            raise PkgdbException('Wrong limit provided')

    if page is not None and limit is not None and limit != 0:
        page = (page - 1) * int(limit)

    return model.Package.search(session, pkg_name=pkg_name,
                                pkg_poc=pkg_poc, pkg_status=status,
                                offset=page, limit=limit, count=count)


def search_collection(session, pattern, status=None, page=None,
                      limit=None, count=False):
    """ Return the list of Collection matching the given criteria.

    :arg session: session with which to connect to the database
    :arg pattern: pattern to match the collection
    :kwarg status: status of the collection to search for
    :kwarg page: the page number to apply to the results
    :kwarg limit: the number of results to return
    :kwarg count: a boolean to return the result of a COUNT query
            if true, returns the data if false (default).

    """
    if '*' in pattern:
        pattern = pattern.replace('*', '%')

    if limit is not None:
        try:
            int(limit)
        except ValueError:
            raise PkgdbException('Wrong limit provided')

    if page is not None and limit is not None and limit != 0:
        page = (page - 1) * int(limit)

    return model.Collection.search(session,
                                   clt_name=pattern,
                                   clt_status=status,
                                   offset=page,
                                   limit=limit,
                                   count=count)


def search_packagers(session, pattern, page=None, limit=None,
                     count=False):
    """ Return the list of Packagers maching the given pattern.

    :arg session: session with which to connect to the database
    :arg pattern: pattern to match on the packagers
    :kwarg page: the page number to apply to the results
    :kwarg limit: the number of results to return
    :kwarg count: a boolean to return the result of a COUNT query
            if true, returns the data if false (default).

    """
    if '*' in pattern:
        pattern = pattern.replace('*', '%')

    if limit is not None:
        try:
            int(limit)
        except ValueError:
            raise PkgdbException('Wrong limit provided')

    if page is not None and limit is not None and limit != 0:
        page = (page - 1) * int(limit)

    packages = model.PackageListing.search_point_of_contact(
        session,
        pattern=pattern,
        offset=page,
        limit=limit,
        count=count)

    return packages


def get_acl_packager(session, packager):
    """ Return the list of ACL associated with a packager.

    :arg session: session with which to connect to the database
    :arg packager: the name of the packager to retrieve the ACLs for.
    """
    return model.PackageListingAcl.get_acl_packager(
        session, packager=packager)


def add_collection(session, clt_name, clt_version, clt_status,
                   clt_publishurl, clt_pendingurl, clt_summary,
                   clt_description, clt_branchname, clt_disttag,
                   clt_gitbranch, user):
    """ Add a new collection

    """

    if not pkgdb.is_pkgdb_admin(user):
        raise PkgdbException('You are now allowed to create collections')

    collection = model.Collection(
        name=clt_name,
        version=clt_version,
        status=clt_status,
        owner=user.username,
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
        print err.message
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
            message = 'Collection "%s" already had this status' % \
                clt_branchname
        session.add(collection)
        session.flush()
        return message
    except NoResultFound:  # pragma: no cover
        raise PkgdbException('Could not find collection "%s"' %
                             clt_branchname)
    except SQLAlchemyError, err:  # pragma: no cover
        raise PkgdbException('Could not update the status of collection'
                             '"%s".' % clt_branchname)


def get_pending_acl_user(session, user):
    """ Return the pending ACLs on any of the packages owned by the
    specified user.
    The method returns a list of dictionnary containing the package name
    the collection branchname, the requested ACL and the user that
    requested that ACL.

    :arg session: session with which to connect to the database
    :arg user: the user owning the packages on which to retrieve the
        list of pending ACLs.
    """
    output = []
    for package in model.PackageListingAcl.get_pending_acl(
            session, user):
        output.append(
            {'package': package.packagelist.package.name,
             'user': package.fas_name,
             'collection': package.packagelist.collection.branchname,
             'acl': package.acl,
             'status': package.status,
             }
        )
    return output


def get_acl_user_package(session, user, package, status=None):
    """ Return the pending ACLs on a specified package for the specified
    user.
    The method returns a list of dictionnary containing the package name
    the collection branchname, the requested ACL and the user that
    requested that ACL.

    :arg session: session with which to connect to the database
    :arg user: the user owning the packages on which to retrieve the
        list of pending ACLs.
    :arg package: the package for which to check the acl
    :kwarg status: the status of the package to retrieve the ACLs of
    """
    output = []
    for package in model.PackageListingAcl.get_acl_package(
            session, user, package, status=status):
        output.append(
            {'package': package.packagelist.package.name,
             'user': package.fas_name,
             'collection': package.packagelist.collection.branchname,
             'acl': package.acl,
             'status': package.status,
             }
        )
    return output


def has_acls(session, user, package, branch, acl):
    """ Return wether the specified user has the specified acl on the
    specified package.

    :arg session: session with which to connnect to the database
    :arg user: the name of the user for which to check the acl
    :arg package: the name of the package on which the acl should be
        checked
    :arg acl: the acl to check for the user on the package
    """
    acls = get_acl_user_package(session, user=user,
                                package=package, status='Approved')
    has_acls = False
    for user_acl in acls:
        if user_acl['collection'] == branch and user_acl['acl'] == acl:
            has_acls = True
            break
    return has_acls


def get_status(session, status='all'):
    """ Return a dictionnary containing all the status and acls.

    :arg session: session with which to connnect to the database
    :kwarg status: single keyword or multiple keywords used to retrict
        querying only for some of the status rather than all.
        Defaults to 'all' other options are: clt_status, pkg_status,
        pkg_acl, acl_status
    :return: a dictionnary with all the status extracted from the database,
        keys are: clt_status, pkg_status, pkg_acl, acl_status
    """
    output = {}

    if status == 'all':
        status = ['clt_status', 'pkg_status', 'pkg_acl', 'acl_status']
    elif isinstance(status, basestring):
        status = [status]

    if 'clt_status' in status:
        output['clt_status'] = model.CollecStatus.all_txt(session)
    if 'pkg_status' in status:
        output['pkg_status'] = model.PkgStatus.all_txt(session)
    if 'pkg_acl' in status:
        output['pkg_acl'] = model.PkgAcls.all_txt(session)
    if 'acl_status' in status:
        output['acl_status'] = model.AclStatus.all_txt(session)
    return output
