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
PkgDB internal API to interact with the database.
'''

import sqlalchemy

from datetime import timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError

from fedora.client.fas2 import FASError

import pkgdb2
from pkgdb2.lib import model
from pkgdb2.lib import utils


## Apparently some of our methods have too many arguments
# pylint: disable=R0913
## to many branches
# pylint: disable=R0912
## or to many variables
# pylint: disable=R0914
## Ignore warnings about TODOs
# pylint: disable=W0511
## Ignore variable name that are too short
# pylint: disable=C0103


class PkgdbException(Exception):
    """ Generic Exception object used to throw pkgdb2 specific error.
    """
    pass


def _validate_poc(pkg_poc):
    """ Validate is the provided ``pkg_poc`` is a valid poc for a package.

    A valid poc is defined as:
        - a user part of the `packager` group
        - an existing group of type `pkgdb`

    :arg pkg_poc: the username of the new Point of contact (POC).

    """
    if pkg_poc == 'orphan':
        return
    if pkg_poc.startswith('group::'):
        # if pkg_poc is a group:
        group = pkg_poc.split('group::')[1]
        # is pkg_poc a valid group (of type pkgdb)
        try:
            group_obj = pkgdb2.lib.utils.get_fas_group(group)
        except FASError as err:  # pragma: no cover
            pkgdb2.LOG.exception(err)
            raise PkgdbException('Could not find group "%s" ' % group)
        if group_obj.group_type != 'pkgdb':
            raise PkgdbException(
                'Invalid group "%s" all groups maintaining packages in pkgdb '
                'should be of type "pkgdb".' % group)
    else:
        # if pkg_poc is a packager
        packagers = pkgdb2.lib.utils.get_packagers()
        if pkg_poc not in packagers:
            raise PkgdbException(
                'The point of contact of this package is not in the packager '
                'group'
            )


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


def add_package(session, pkg_name, pkg_summary, pkg_description, pkg_status,
                pkg_collection, pkg_poc, user, pkg_reviewURL=None,
                pkg_shouldopen=None, pkg_upstreamURL=None,
                pkg_critpath=False):
    """ Create a new Package in the database and adds the corresponding
    PackageListing entry.

    :arg session: session with which to connect to the database.
    :arg pkg_name: the name of the package.
    :arg pkg_summary: a summary description of the package.
    :arg pkg_description: the description of the package.
    :arg pkg_status: the status of the package.
    :arg pkg_collection: the collection in which had the package.
    :arg pkg_poc: the point of contact for this package in this collection
    :arg user: the user performing the action
    :kwarg pkg_reviewURL: the url of the review-request on the bugzilla
    :kwarg pkg_shouldopen: a boolean
    :kwarg pkg_upstreamURL: the url of the upstream project.
    :kwarg pkg_critpath: a boolean specifying if the package is marked as
        being in critpath.
    :returns: a message informating that the package has been successfully
        created.
    :rtype: str()
    :raises pkgdb2.lib.PkgdbException: There are few conditions leading to
        this exception beeing raised:
            - You are not allowed to add a package, only pkgdb admin can
            - Something went wrong when adding the Package to the database
            - Something went wrong when adding ACLs for this package in the
                database
            - Group is incorrect
    :raises sqlalchemy.orm.exc.NoResultFound: when there is no collection
        found in the database with the name ``pkg_collection``.

    """
    if user is None or not pkgdb2.is_pkgdb_admin(user):
        raise PkgdbException("You're not allowed to add a package")

    _validate_poc(pkg_poc)

    if isinstance(pkg_collection, (str, unicode)):
        if ',' in pkg_collection:
            pkg_collection = [item.strip()
                              for item in pkg_collection.split(',')]
        else:
            pkg_collection = [pkg_collection]

    package = model.Package(name=pkg_name,
                            summary=pkg_summary,
                            description=pkg_description,
                            status=pkg_status,
                            review_url=pkg_reviewURL,
                            shouldopen=pkg_shouldopen,
                            upstream_url=pkg_upstreamURL
                            )
    session.add(package)
    try:
        session.flush()
    except SQLAlchemyError, err:  # pragma: no cover
        pkgdb2.LOG.exception(err)
        session.rollback()
        raise PkgdbException('Could not create package')

    for collec in pkg_collection:
        collection = model.Collection.by_name(session, collec)
        pkglisting = package.create_listing(point_of_contact=pkg_poc,
                                            collection=collection,
                                            statusname=pkg_status,
                                            critpath=pkg_critpath)
        session.add(pkglisting)
        try:
            session.flush()
        except SQLAlchemyError, err:  # pragma: no cover
            pkgdb2.LOG.exception(err)
            session.rollback()
            raise PkgdbException('Could not add packages to collections')
        else:
            pkgdb2.lib.utils.log(session, package, 'package.new', dict(
                agent=user.username,
                package_name=package.name,
                package_listing=pkglisting.to_json(),
            ))

    # Add all new ACLs to the owner
    acls = ['commit', 'watchbugzilla', 'watchcommits', 'approveacls']
    if pkg_poc.startswith('group::'):
        acls = ['commit', 'watchbugzilla', 'watchcommits']
    if pkg_poc.startswith('group::') and not pkg_poc.endswith('-sig'):
        session.rollback()
        raise PkgdbException(
            'Invalid group "%s" all groups in pkgdb should end with '
            '"-sig".' % pkg_poc)

    for collec in pkg_collection:
        for acl in acls:
            set_acl_package(session=session,
                            pkg_name=pkg_name,
                            pkg_branch=collec,
                            pkg_user=pkg_poc,
                            acl=acl,
                            status='Approved',
                            user=user)
    try:
        session.flush()
        return 'Package created'
    except SQLAlchemyError, err:  # pragma: no cover
        pkgdb2.LOG.exception(err)
        raise PkgdbException('Could not add ACLs')


def get_acl_package(session, pkg_name, pkg_clt=None):
    """ Return the ACLs for the specified package.

    :arg session: session with which to connect to the database.
    :arg pkg_name: the name of the package to retrieve the ACLs for.
    :kward pkg_clt: the branche name of the collection to retrieve the ACLs
        of.
    :returns: a list of ``PackageListing``.
    :rtype: list(PackageListing)
    :raises pkgdb2.lib.PkgdbException: when user restricted the acl to a
        specific branch using ``pkg_clt`` and this branch could not be
        found associated with this package.
    :raises sqlalchemy.orm.exc.NoResultFound: when there is no package
        found in the database with the name ``pkg_name``.

    """
    package = model.Package.by_name(session, pkg_name)
    pkglisting = model.PackageListing.by_package_id(session, package.id)
    if pkg_clt:
        tmp = None
        for pkglist in pkglisting:
            if pkglist.collection.branchname == pkg_clt:
                tmp = pkglist
                break
        if tmp is None:
            raise PkgdbException(
                'Collection %s is not associated with package %s' % (
                    pkg_clt, pkg_name)
            )
        else:
            pkglisting = [tmp]
    return pkglisting


def set_acl_package(session, pkg_name, pkg_branch, pkg_user, acl, status,
                    user):
    """ Set the specified ACLs for the specified package.

    :arg session: session with which to connect to the database.
    :arg pkg_name: the name of the package.
    :arg pkg_branch: the name of the collection.
    :arg pkg_user: the FAS user for which the ACL should be set/change.
    :arg status: the status of the ACLs.
    :arg user: the user making the action.
    :raises pkgdb2.lib.PkgdbException: There are few conditions leading to
        this exception beeing raised:
            - The ``pkg_name`` does not correspond to any package in the
                database.
            - The ``pkg_branch`` does not correspond to any collection in
                the database.
            - You are not allowed to perform the action, are allowed:
                - pkgdb admins.
                - People with 'approveacls' rights.
                - Anyone for 'watchcommits' and 'watchbugzilla' acls.
                - Anyone to set status to 'Awaiting review', 'Removed' and
                    'Obsolete'.
                .. note:: groups cannot have 'approveacls' rights.

    """
    try:
        package = model.Package.by_name(session, pkg_name)
    except NoResultFound:
        raise PkgdbException('No package found by this name')

    try:
        collection = model.Collection.by_name(session, pkg_branch)
    except NoResultFound:
        raise PkgdbException('No collection found by the name of %s'
                             % pkg_branch)

    if not pkgdb2.is_pkg_admin(session, user, package.name, pkg_branch):
        if user.username != pkg_user and not pkg_user.startswith('group::'):
            raise PkgdbException('You are not allowed to update ACLs of '
                                 'someone else.')
        elif user.username == pkg_user and status not in \
                ('Awaiting Review', 'Removed', 'Obsolete') \
                and acl not in pkgdb2.APP.config['AUTO_APPROVE']:
            raise PkgdbException(
                'You are not allowed to approve or deny '
                'ACLs for yourself.')

    if pkg_user.startswith('group::') and acl == 'approveacls':
        raise PkgdbException(
            'Groups cannot have "approveacls".')

    if pkg_user.startswith('group::') and not pkg_user.endswith('-sig'):
        raise PkgdbException(
            'Invalid group "%s" all groups in pkgdb should end with '
            '"-sig".' % pkg_user)

    try:
        pkglisting = model.PackageListing.by_pkgid_collectionid(
            session,
            package.id,
            collection.id)
    except NoResultFound:  # pragma: no cover  TODO: can we test this?
        pkglisting = package.create_listing(point_of_contact=pkg_user,
                                            collection=collection,
                                            statusname='Approved')
        session.add(pkglisting)
        session.flush()

    personpkg = model.PackageListingAcl.get_or_create(session,
                                                      pkg_user,
                                                      pkglisting.id,
                                                      acl=acl,
                                                      status=status)
    prev_status = personpkg.status
    personpkg.status = status
    session.flush()
    return pkgdb2.lib.utils.log(session, package, 'acl.update', dict(
        agent=user.username,
        username=pkg_user,
        acl=acl,
        previous_status=prev_status,
        status=status,
        package_name=pkglisting.package.name,
        package_listing=pkglisting.to_json(),
    ))


def update_pkg_poc(session, pkg_name, pkg_branch, pkg_poc, user):
    """ Change the point of contact of a package.

    :arg session: session with which to connect to the database.
    :arg pkg_name: the name of the package.
    :arg pkg_branch: the branchname of the collection.
    :arg pkg_poc: name of the new point of contact for the package.
    :arg user: the user making the action.
    :returns: a message informing that the point of contact has been
        successfully changed.
    :rtype: str()
    :raises pkgdb2.lib.PkgdbException: There are few conditions leading to
        this exception beeing raised:
            - The ``pkg_name`` does not correspond to any package in the
                database.
            - The ``pkg_branch`` does not correspond to any collection in
                the database.
            - You are not allowed to perform the action, are allowed:
                - pkgdb admins.
                - current point of contact.
                - anyone on orphaned packages.
                - anyone in the group when the point of contact is set to
                    said group.

    """
    try:
        package = model.Package.by_name(session, pkg_name)
    except NoResultFound:
        raise PkgdbException('No package found by this name')

    try:
        collection = model.Collection.by_name(session, pkg_branch)
    except NoResultFound:
        raise PkgdbException('No collection found by the name of %s'
                             % pkg_branch)

    pkglisting = model.PackageListing.by_pkgid_collectionid(session,
                                                            package.id,
                                                            collection.id)

    prev_poc = pkglisting.point_of_contact

    _validate_poc(pkg_poc)

    if pkglisting.point_of_contact != user.username \
            and pkglisting.point_of_contact != 'orphan' \
            and not pkgdb2.is_pkgdb_admin(user) \
            and not pkglisting.point_of_contact.startswith('group::'):
        raise PkgdbException(
            'You are not allowed to change the point of contact.')

    # Is current PoC a group?
    if pkglisting.point_of_contact.startswith('group::'):
        group = pkglisting.point_of_contact.split('group::')[1]
        if not group in user.groups:
            raise PkgdbException(
                'You are not part of the group "%s", you are not allowed to'
                ' change the point of contact.' % group)

    pkglisting.point_of_contact = pkg_poc
    if pkg_poc == 'orphan':
        pkglisting.status = 'Orphaned'
    elif pkglisting.status in ('Orphaned', 'Retired'):
        pkglisting.status = 'Approved'

    session.add(pkglisting)
    session.flush()
    output = pkgdb2.lib.utils.log(
        session, pkglisting.package, 'owner.update', dict(
            agent=user.username,
            username=pkg_poc,
            previous_owner=prev_poc,
            package_name=pkglisting.package.name,
            package_listing=pkglisting.to_json(),
        )
    )
    # Update Bugzilla about new owner
    pkgdb2.lib.utils.set_bugzilla_owner(
        pkg_poc, package.name, collection.name, collection.version)

    return output


def update_pkg_status(session, pkg_name, pkg_branch, status, user,
                      poc='orphan'):
    """ Update the status of a package.

    :arg session: session with which to connect to the database.
    :arg pkg_name: the name of the package.
    :arg pkg_branch: the name of the collection.
    :arg user: the user making the action.
    :raises pkgdb2.lib.PkgdbException: There are few conditions leading to
        this exception beeing raised:
            - The provided ``pkg_name`` does not correspond to any package
                in the database.
            - The provided ``pkg_branch`` does not correspond to any collection
                in the database.
            - The provided ``status`` is not allowed for a package.
            - You are not allowed to perform the action:
                - Deprecate:
                    - user can only deprecate on the devel branch.
                    - admin can deprecate on all branches.
                - Approve:
                    - If you approve an orphaned package you need to
                        specify a point_of_contact: ``poc``.
                - Orphan:
                    - anyone can orphan, this should not raise any exception.
                - Remove:
                    - only admin can remove.

    """
    try:
        package = model.Package.by_name(session, pkg_name)
    except NoResultFound:
        raise PkgdbException('No package found by this name')

    try:
        collection = model.Collection.by_name(session, pkg_branch)
    except NoResultFound:
        raise PkgdbException('No collection found by this name')

    if status not in ['Approved', 'Removed', 'Retired', 'Orphaned']:
        raise PkgdbException('Status not allowed for a package : %s' %
                             status)

    pkglisting = model.PackageListing.by_pkgid_collectionid(session,
                                                            package.id,
                                                            collection.id)

    prev_status = pkglisting.status
    if status == 'Retired':
        # Admins can deprecate everything
        # Users can deprecate Fedora devel and EPEL branches
        if pkgdb2.is_pkgdb_admin(user) \
                or (collection.name == 'Fedora'
                    and collection.version == 'devel') \
                or collection.name == 'EPEL':

            pkglisting.status = 'Retired'
            pkglisting.point_of_contact = 'orphan'
            session.add(pkglisting)
            session.flush()
        else:
            raise PkgdbException(
                'You are not allowed to retire the '
                'package: %s on branch %s.' % (
                    package.name, collection.branchname))
    elif status == 'Orphaned':
        pkglisting.status = 'Orphaned'
        pkglisting.point_of_contact = 'orphan'
        session.add(pkglisting)
        session.flush()
    elif pkgdb2.is_pkgdb_admin(user):
        if status == 'Approved':
            if pkglisting.status == 'Orphaned' and poc == 'orphan':
                raise PkgdbException(
                    'You need to specify the point of contact of this '
                    'package for this branch to un-orphan it')
            # is the new poc valide:
            _validate_poc(poc)
            pkglisting.point_of_contact = poc

        pkglisting.status = status
        session.add(pkglisting)
        session.flush()
        # Update Bugzilla about new owner
        pkgdb2.lib.utils.set_bugzilla_owner(
            poc, package.name, collection.name,
            collection.version)

    else:
        raise PkgdbException(
            'You are not allowed to update the status of '
            'the package: %s on branch %s to %s.' % (
                package.name, collection.branchname, status)
        )

    return pkgdb2.lib.utils.log(session, package, 'package.update.status',
        dict(
            agent=user.username,
            status=status,
            prev_status=prev_status,
            package_name=package.name,
            package_listing=pkglisting.to_json(),
        )
    )


def search_package(session, pkg_name, pkg_branch=None, pkg_poc=None,
                   orphaned=None, status=None, page=None,
                   limit=None, count=False):
    """ Return the list of packages matching the given criteria.

    :arg session: session with which to connect to the database.
    :arg pkg_name: the name of the package.
    :kwarg pkg_branch: branchname of the collection to search.
    :kwarg pkg_poc: point of contact of the packages searched.
    :kwarg orphaned: boolean to restrict search to orphaned packages.
    :kwarg status: allows filtering the packages by their status:
        Approved, Retired, Removed, Orphaned.
    :kwarg page: the page number to apply to the results.
    :kwarg limit: the number of results to return.
    :kwarg count: a boolean to return the result of a COUNT query
            if true, returns the data if false (default).
    :returns: a list of ``Package`` entry corresponding to the given
        criterias.
    :rtype: list(Package)
    :raises pkgdb2.lib.PkgdbException: There are few conditions leading to
        this exception beeing raised:
            - The provided ``limit`` is not an integer.
            - The provided ``page`` is not an integer.

    """
    if '*' in pkg_name:
        pkg_name = pkg_name.replace('*', '%')
    if orphaned:
        pkg_poc = 'orphan'
        status = 'Orphaned'

    if limit is not None:
        try:
            limit = int(limit)
        except ValueError:
            raise PkgdbException('Wrong limit provided')

    if page is not None:
        try:
            page = int(page)
        except ValueError:
            raise PkgdbException('Wrong page provided')

    if page is not None and limit is not None and limit != 0:
        page = (page - 1) * limit

    return model.Package.search(session, pkg_name=pkg_name,
                                pkg_poc=pkg_poc, pkg_status=status,
                                pkg_branch=pkg_branch, orphaned=orphaned,
                                offset=page, limit=limit, count=count)


def search_collection(session, pattern, status=None, page=None,
                      limit=None, count=False):
    """ Return the list of Collection matching the given criteria.

    :arg session: session with which to connect to the database.
    :arg pattern: pattern to match the collection.
    :kwarg status: status of the collection to search for.
    :kwarg page: the page number to apply to the results.
    :kwarg limit: the number of results to return.
    :kwarg count: a boolean to return the result of a COUNT query
            if true, returns the data if false (default).
    :returns: a list of ``Collection`` entry corresponding to the given
        criterias.
    :rtype: list(Collection)
    :raises pkgdb2.lib.PkgdbException: There are few conditions leading to
        this exception beeing raised:
            - The provided ``limit`` is not an integer.
            - The provided ``page`` is not an integer.

    """
    if '*' in pattern:
        pattern = pattern.replace('*', '%')

    if limit is not None:
        try:
            limit = int(limit)
        except ValueError:
            raise PkgdbException('Wrong limit provided')

    if page is not None:
        try:
            page = int(page)
        except ValueError:
            raise PkgdbException('Wrong page provided')

    if page is not None and limit is not None and limit != 0:
        page = (page - 1) * limit

    return model.Collection.search(session,
                                   clt_name=pattern,
                                   clt_status=status,
                                   offset=page,
                                   limit=limit,
                                   count=count)


def search_packagers(session, pattern, page=None, limit=None,
                     count=False):
    """ Return the list of Packagers maching the given pattern.

    :arg session: session with which to connect to the database.
    :arg pattern: pattern to match on the packagers.
    :kwarg page: the page number to apply to the results.
    :kwarg limit: the number of results to return.
    :kwarg count: a boolean to return the result of a COUNT query
            if true, returns the data if false (default).
    :returns: a list of ``PackageListing`` entry corresponding to the given
        criterias.
    :rtype: list(PackageListing)
    :raises pkgdb2.lib.PkgdbException: There are few conditions leading to
        this exception beeing raised:
            - The provided ``limit`` is not an integer.
            - The provided ``page`` is not an integer.

    """
    if '*' in pattern:
        pattern = pattern.replace('*', '%')

    if limit is not None:
        try:
            limit = int(limit)
        except ValueError:
            raise PkgdbException('Wrong limit provided')

    if page is not None:
        try:
            page = int(page)
        except ValueError:
            raise PkgdbException('Wrong page provided')

    if page is not None and limit is not None and limit != 0:
        page = (page - 1) * limit

    packagers = model.PackageListing.search_packagers(
        session,
        pattern=pattern,
        offset=page,
        limit=limit,
        count=count)

    return packagers


def search_logs(session, package=None, from_date=None, page=None, limit=None,
                count=False):
    """ Return the list of Collection matching the given criteria.

    :arg session: session with which to connect to the database.
    :kwarg package: retrict the logs to a certain package.
    :kwarg from_date: a date from which to retrieve the logs.
    :kwarg page: the page number to apply to the results.
    :kwarg limit: the number of results to return.
    :kwarg count: a boolean to return the result of a COUNT query
            if true, returns the data if false (default).
    :returns: a list of ``Log`` entry corresponding to the given criterias.
    :rtype: list(Log)
    :raises pkgdb2.lib.PkgdbException: There are few conditions leading to
        this exception beeing raised:
            - The provided ``limit`` is not an integer.
            - The provided ``page`` is not an integer.
            - The ``package`` name specified does not correspond to any
                package.

    """
    if limit is not None:
        try:
            limit = int(limit)
        except ValueError:
            raise PkgdbException('Wrong limit provided')

    if page is not None:
        try:
            page = int(page)
        except ValueError:
            raise PkgdbException('Wrong page provided')

    package_id = None
    if package is not None:
        package = search_package(session, package, limit=1)
        if not package:
            raise PkgdbException('No package exists')
        else:
            package_id = package[0].id

    if page is not None and limit is not None and limit != 0:
        page = (page - 1) * limit

    if from_date:
        # Make sure we get all the events of the day asked
        from_date = from_date + timedelta(days=1)

    return model.Log.search(session,
                            package_id=package_id,
                            from_date=from_date,
                            offset=page,
                            limit=limit,
                            count=count)


def get_acl_packager(session, packager):
    """ Return the list of ACL associated with a packager.

    :arg session: session with which to connect to the database.
    :arg packager: the name of the packager to retrieve the ACLs for.
    :returns: a list of ``PackageListingAcl`` associated to the specified
        user.
    :rtype: list(PackageListingAcl)

    """
    return model.PackageListingAcl.get_acl_packager(
        session, packager=packager)


def get_critpath_packages(session, branch=None):
    """ Return the list of ACL associated with a packager.

    :arg session: session with which to connect to the database.
    :kwarg branch: the name of the branch to retrieve the critpaths of.
    :returns: a list of ``PackageListing`` marked as being part of critpath.
    :rtype: list(PackageListing)

    """
    return model.PackageListing.get_critpath_packages(
        session, branch=branch)


def get_package_maintained(session, packager, poc=True):
    """ Return all the packages and branches where given packager has
    commit acl.

    :arg session: session with which to connect to the database.
    :arg packager: the name of the packager to retrieve the ACLs for.
    :kwarg poc: boolean to specify if the results should be restricted
            to packages where ``user`` is the point of contact or packages
            where ``user`` is not the point of contact.
    :returns: a list of ``Package`` associated to the specified user.
    :rtype: list(Package, [Collection])

    """
    output = {}
    for pkg, clt in model.Package.get_package_of_user(
            session, packager, poc=poc):
        if pkg.name in output:
            output[pkg.name][1].append(clt)
        else:
            output[pkg.name] = [pkg, [clt]]
    return [output[key] for key in sorted(output)]


def add_collection(session, clt_name, clt_version, clt_status,
                   clt_branchname, clt_disttag, clt_gitbranch, user):
    """ Add a new collection to the database.

    This method only flushes the new object, nothing is committed to the
    database.

    :arg session: the session with which to connect to the database.
    :kwarg clt_name: the name of the collection.
    :kwarg clt_version: the version of the collection.
    :kwarg clt_status: the status of the collection.
    :kwarg clt_branchname: the branchname of the collection.
    :kwarg clt_disttag: the dist tag of the collection.
    :kwarg clt_gitbranch: the git branch name of the collection.
    :kwarg user: The user performing the update.
    :returns: a message informing that the collection was successfully
        created.
    :rtype: str()
    :raises pkgdb2.lib.PkgdbException: There are few conditions leading to
        this exception beeing raised:
            - You are not allowed to edit a collection, only pkgdb admin can.
            - An error occured while updating the collection in the database
                the message returned is then the error message from the
                database.

    """

    if not pkgdb2.is_pkgdb_admin(user):
        raise PkgdbException('You are not allowed to create collections')

    collection = model.Collection(
        name=clt_name,
        version=clt_version,
        status=clt_status,
        owner=user.username,
        branchname=clt_branchname,
        distTag=clt_disttag,
        git_branch_name=clt_gitbranch,
    )
    try:
        session.add(collection)
        session.flush()
        pkgdb2.lib.utils.log(session, None, 'collection.new', dict(
            agent=user.username,
            collection=collection.to_json(),
        ))
        return 'Collection "%s" created' % collection.branchname
    except SQLAlchemyError, err:  # pragma: no cover
        pkgdb2.LOG.exception(err)
        raise PkgdbException('Could not add Collection to the database.')


def edit_collection(session, collection, clt_name=None, clt_version=None,
                    clt_status=None, clt_branchname=None, clt_disttag=None,
                    clt_gitbranch=None, user=None):
    """ Edit a specified collection

    This method only flushes the new object, nothing is committed to the
    database.

    :arg session: the session with which to connect to the database.
    :arg collection: the ``Collection`` object to update.
    :kwarg clt_name: the new name of the collection.
    :kwarg clt_version: the new version of the collection.
    :kwarg clt_status: the new status of the collection.
    :kwarg clt_branchname: the new branchname of the collection.
    :kwarg clt_disttag: the new dist tag of the collection.
    :kwarg clt_gitbranch: the new git branch name of the collection.
    :kwarg user: The user performing the update.
    :returns: a message informing that the collection was successfully
        updated.
    :rtype: str()
    :raises pkgdb2.lib.PkgdbException: There are few conditions leading to
        this exception beeing raised:
            - You are not allowed to edit a collection, only pkgdb admin can.
            - An error occured while updating the package in the database
                the message returned is a dummy information message to
                return to the user, the trace back is in the logs.

    """

    if not pkgdb2.is_pkgdb_admin(user):
        raise PkgdbException('You are not allowed to edit collections')

    edited = []

    if clt_name and clt_name != collection.name:
        collection.name = clt_name
        edited.append('name')
    if clt_version and clt_version != collection.version:
        collection.version = clt_version
        edited.append('version')
    if clt_status and clt_status != collection.status:
        collection.status = clt_status
        edited.append('status')
    if clt_branchname and clt_branchname != collection.branchname:
        collection.branchname = clt_branchname
        edited.append('branchname')
    if clt_disttag and clt_disttag != collection.distTag:
        collection.distTag = clt_disttag
        edited.append('distTag')
    if clt_gitbranch and clt_gitbranch != collection.git_branch_name:
        collection.git_branch_name = clt_gitbranch
        edited.append('git_branch_name')

    if edited:
        try:
            session.add(collection)
            session.flush()
            pkgdb2.lib.utils.log(session, None, 'collection.update', dict(
                agent=user.username,
                fields=edited,
                collection=collection.to_json(),
            ))
            return 'Collection "%s" edited' % collection.branchname
        except SQLAlchemyError, err:  # pragma: no cover
            pkgdb2.LOG.exception(err)
            raise PkgdbException('Could not edit Collection.')


def edit_package(session, package, pkg_name=None, pkg_summary=None,
                    pkg_description=None, pkg_review_url=None,
                    pkg_upstream_url=None, pkg_status=None, user=None):
    """ Edit a specified package

    This method only flushes the new object, nothing is committed to the
    database.

    :arg session: the session with which to connect to the database.
    :arg package: the ``Package`` object to update.
    :kwarg pkg_name: the new name of the package.
    :kwarg pkg_summary: the new summary of the package.
    :kwarg pkg_description: the new description of the package.
    :kwarg pkg_review_url: the new URL to the package review on bugzilla.
    :kwarg pkg_upstream_url: the new URL to the project upstream.
    :kwarg pkg_status: the new status to give to this package.
    :kwarg user: The user performing the update.
    :returns: a message informing that the package was successfully
        updated.
    :rtype: str()
    :raises pkgdb2.lib.PkgdbException: There are few conditions leading to
        this exception beeing raised:
            - You are not allowed to edit a package, only pkgdb admin can.
            - An error occured while updating the package in the database
                the message returned is a dummy information message to
                return to the user, the trace back is in the logs.

    """

    if not pkgdb2.is_pkgdb_admin(user):
        raise PkgdbException('You are not allowed to edit collections')

    edited = []

    if pkg_name and pkg_name != package.name:
        package.name = pkg_name
        edited.append('name')
    if pkg_summary and pkg_summary != package.summary:
        package.summary = pkg_summary
        edited.append('summary')
    if pkg_description and pkg_description != package.description:
        package.description = pkg_description
        edited.append('description')
    if pkg_review_url and pkg_review_url != package.review_url:
        package.review_url = pkg_review_url
        edited.append('review_url')
    if pkg_upstream_url and pkg_upstream_url != package.upstream_url:
        package.upstream_url = pkg_upstream_url
        edited.append('upstream_url')
    if pkg_status and pkg_status != package.status:
        package.status = pkg_status
        edited.append('status')

    if edited:
        try:
            session.add(package)
            session.flush()
            pkgdb2.lib.utils.log(session, None, 'package.update', dict(
                agent=user.username,
                fields=edited,
                package=package.to_json(),
            ))
            return 'Package "%s" edited' % package.name
        except SQLAlchemyError, err:  # pragma: no cover
            pkgdb2.LOG.exception(err)
            raise PkgdbException('Could not edit package.')



def update_collection_status(session, clt_branchname, clt_status, user):
    """ Update the status of a collection.

    This method only flushes the new object, nothing is committed to the
    database.

    :arg session: session with which to connect to the database
    :arg clt_branchname: branchname of the collection
    :arg clt_status: status of the collection
    :returns: a message information whether the status of the collection
        has been updated correclty or if it was not necessary.
    :rtype: str()
    :raises pkgdb2.lib.PkgdbException: There are few conditions leading to
        this exception beeing raised:
            - You are not allowed to edit a collection, only pkgdb admin can.
            - An error occured while updating the collection in the database
                the message returned is then the error message from the
                database.
            - The specified collection could not be found in the database.

    """
    if not pkgdb2.is_pkgdb_admin(user):
        raise PkgdbException('You are not allowed to edit collections')

    try:
        collection = model.Collection.by_name(session, clt_branchname)

        if collection.status != clt_status:
            prev_status = collection.status
            collection.status = clt_status
            message = 'Collection updated from "%s" to "%s"' % (
                prev_status, clt_status)
            session.add(collection)
            session.flush()
            pkgdb2.lib.utils.log(session, None, 'collection.update', dict(
                agent=user.username,
                fields=['status'],
                collection=collection.to_json(),
            ))
        else:
            message = 'Collection "%s" already had this status' % \
                clt_branchname

        return message
    except NoResultFound:  # pragma: no cover
        raise PkgdbException('Could not find collection "%s"' %
                             clt_branchname)
    except SQLAlchemyError, err:  # pragma: no cover
        pkgdb2.LOG.exception(err)
        raise PkgdbException('Could not update the status of collection'
                             '"%s".' % clt_branchname)


def get_pending_acl_user(session, user):
    """ Return the pending ACLs on any of the packages owned by the
    specified user.
    The method returns a list of dictionnary containing the package name
    the collection branchname, the requested ACL and the user that
    requested that ACL.

    :arg session: session with which to connect to the database.
    :arg user: the user owning the packages on which to retrieve the
        list of pending ACLs.
    :returns: a list of dictionnary containing the pending ACL for the
        specified user.
        The dictionnary has for keys: 'package', 'user', 'collection',
        'acl', 'status'.
    :rtype: [{str():str()}]

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
    """ Return the ACLs on a specified package for the specified user.

    The method returns a list of dictionnary containing the package name
    the collection branchname, the requested ACL and the user that
    requested that ACL.

    :arg session: session with which to connect to the database.
    :arg user: the user owning the packages on which to retrieve the
        list of pending ACLs.
    :arg package: the package for which to check the acl.
    :kwarg status: the status of the package to retrieve the ACLs of.
    :returns: a list of dictionnary containing the ACL the specified user
        has on a specific package.
        The dictionnary has for keys: 'package', 'user', 'collection',
        'acl', 'status'.
    :rtype: [{str():str()}]

    """
    output = []
    for package in model.PackageListingAcl.get_acl_package(
            session, user, package, status=status):
        output.append(
            {'package': package.packagelist.package.name,
             'user': package.fas_name,
             'collection': package.packagelist.collection.branchname,
             'collection_status': package.packagelist.collection.status,
             'acl': package.acl,
             'status': package.status,
             }
        )
    return output


def has_acls(session, user, package, branch, acl):
    """ Return wether the specified user has the specified acl on the
    specified package.

    :arg session: session with which to connnect to the database.
    :arg user: the name of the user for which to check the acl.
    :arg package: the name of the package on which the acl should be
        checked.
    :arg acl: the acl to check for the user on the package.
    :returns: a boolean specifying whether specified user has this ACL on
        this package and branch.
    :rtype: bool()

    """
    acls = get_acl_user_package(session, user=user,
                                package=package, status='Approved')
    user_has_acls = False
    for user_acl in acls:
        if user_acl['collection'] == branch and user_acl['acl'] == acl:
            user_has_acls = True
            break
    return user_has_acls


def get_status(session, status='all'):
    """ Return a dictionnary containing all the status and acls.

    :arg session: session with which to connnect to the database.
    :kwarg status: single keyword or multiple keywords used to retrict
        querying only for some of the status rather than all.
        Defaults to 'all' other options are: clt_status, pkg_status,
        pkg_acl, acl_status.
    :returns: a dictionnary with all the status extracted from the database,
        keys are: clt_status, pkg_status, pkg_acl, acl_status.
    :rtype: dict(str():list())

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


def get_top_maintainers(session, top=10):
    """ Return the specified top maintainer having the most commit rights

    :arg session: session with which to connect to the database.
    :arg top: the number of results to return, defaults to 10.
    :returns: a list of tuple of type: (username, number_of_packages).
    :rtype: list(tuple())

    """
    return model.PackageListingAcl.get_top_maintainers(session, top)


def get_top_poc(session, top=10):
    """ Return the specified top point of contact.

    :arg session: session with which to connect to the database.
    :arg top: the number of results to return, defaults to 10.
    :returns: a list of tuple of type: (username, number_of_poc).
    :rtype: list(tuple())

    """
    return model.PackageListing.get_top_poc(session, top)


def unorphan_package(session, pkg_name, pkg_branch, pkg_user, user):
    """ Unorphan a specific package in favor of someone and give him the
    appropriate ACLs.

    This method only flushes the changes, nothing is committed to the
    database.

    :arg session: session with which to connect to the database.
    :arg pkg_name: the name of the package.
    :arg pkg_branch: the name of the collection.
    :arg pkg_user: the FAS user requesting the package.
    :arg user: the user making the action.
    :raises pkgdb2.lib.PkgdbException: There are few conditions leading to
        this exception beeing raised:
            - The package name provided does not correspond to any package
                in the database.
            - The package could not be found in the specified branch
            - The package is not orphaned in the specified branch
            - You are are trying to unorphan the package for someone else
                while you are not a pkgdb admin
            - You are trying to unorphan the package while you are not a
                packager.

    """
    try:
        package = model.Package.by_name(session, pkg_name)
    except NoResultFound:
        raise PkgdbException('No package found by this name')

    try:
        collection = model.Collection.by_name(session, pkg_branch)
    except NoResultFound:
        raise PkgdbException('No collection found by this name')

    pkg_listing = get_acl_package(session, pkg_name, pkg_branch)[0]

    if not pkg_listing.status in ('Orphaned', 'Retired'):
        raise PkgdbException('Package is not orphaned on %s' % pkg_branch)

    if not pkgdb2.is_pkgdb_admin(user):
        if user.username != pkg_user and not pkg_user.startswith('group::'):
            raise PkgdbException('You are not allowed to update ACLs of '
                                 'someone else.')
        elif user.username == pkg_user and 'packager' not in user.groups:
            raise PkgdbException('You must be a packager to take a package.')

    status = 'Approved'
    pkg_listing.point_of_contact = pkg_user
    pkg_listing.status = status
    session.add(pkg_listing)
    session.flush()

    pkgdb2.lib.utils.log(session, pkg_listing.package, 'owner.update', dict(
        agent=user.username,
        username=pkg_user,
        previous_owner="orphan",
        status=status,
        package_name=pkg_listing.package.name,
        package_listing=pkg_listing.to_json(),
    ))
    pkgdb2.lib.utils.set_bugzilla_owner(
        user.username, package.name, collection.name, collection.version)

    acls = ['commit', 'watchbugzilla', 'watchcommits', 'approveacls']

    for acl in acls:
        personpkg = model.PackageListingAcl.get_or_create(session,
                                                          pkg_user,
                                                          pkg_listing.id,
                                                          acl=acl,
                                                          status=status)
        prev_status = personpkg.status
        personpkg.status = status
        session.add(personpkg)

        pkgdb2.lib.utils.log(session, pkg_listing.package, 'acl.update', dict(
            agent=user.username,
            username=pkg_user,
            acl=acl,
            previous_status=prev_status,
            status=status,
            package_name=pkg_listing.package.name,
            package_listing=pkg_listing.to_json(),
        ))

    session.flush()
    return 'Package %s has been unorphaned on %s by %s' % (
        pkg_name, pkg_branch, pkg_user
    )


def add_branch(session, clt_from, clt_to, user):
    """ Clone a the permission from a branch to another.

    This method only flushes the new objects, the only thing committed is
    the log message when the branching starts.

    :arg session: session with which to connect to the database.
    :arg clt_from: the ``branchname`` of the collection to branch from.
    :arg clt_to: the ``branchname`` of the collection to branch to.
    :arg user: the user making the action.
    :returns: a list of errors generated while branching, these errors
        might be the results of trying to create a PackageListing object
        already existing.
    :rtype: list(str)
    :raises pkgdb2.lib.PkgdbException: There are three conditions leading to
        this exception beeing raised:
            - You are not allowed to branch (only pkgdb admin can do it)
            - The specified branch from is invalid (does not exist)
            - The specified branch to is invalid (does not exist).

    """
    if not pkgdb2.is_pkgdb_admin(user):
        raise PkgdbException('You are not allowed to branch: %s to %s' % (
            clt_from, clt_to))

    try:
        clt_from = model.Collection.by_name(session, clt_from)
    except NoResultFound:
        raise PkgdbException('Branch %s not found' % clt_from)

    try:
        clt_to = model.Collection.by_name(session, clt_to)
    except NoResultFound:
        raise PkgdbException('Branch %s not found' % clt_to)

    pkgdb2.lib.utils.log(session, None, 'branch.start', dict(
        agent=user.username,
        collection_from=clt_from.to_json(),
        collection_to=clt_to.to_json(),
    ))
    session.commit()

    messages = []
    for pkglist in model.PackageListing.by_collectionid(
            session, clt_from.id):
        if pkglist.status == 'Approved':
            try:
                pkglist.branch(session, clt_to)
            except SQLAlchemyError, err:  # pragma: no cover
                pkgdb2.LOG.exception(err)
                messages.append(err)

    # Should we raise a PkgdbException if messages != [], or just return
    # them?

    pkgdb2.lib.utils.log(session, None, 'branch.complete', dict(
        agent=user.username,
        collection_from=clt_from.to_json(),
        collection_to=clt_to.to_json(),
    ))

    # Go for returning them for the moment, which allows the logs to be
    # inserted
    return messages


def count_collection(session):
    """ Return the number of package 'Approved' for each collection.

    :arg session: the session to connect to the database with.

    """
    return model.Package.count_collection(session)


def notify(session, eol=False, name=None, version=None):
    """ Return the user that should be notify for each package.

    :arg session: the session to connect to the database with.
    :kwarg eol: a boolean to specify wether the output should include End
        Of Life releases or not.
    :kwarg name: restricts the output to a specific collection name.
    :kwarg version: restricts the output to a specific collection version.

    """
    output = {}
    pkgs = model.notify(session=session, eol=eol, name=name,
                        version=version)
    for pkg in pkgs:
        if pkg[0] in output:  # pragma: no cover
            output[pkg[0]] += ',' + pkg[1]
        else:
            output[pkg[0]] = pkg[1]
    return output


def bugzilla(session, name=None):
    """ Return the information to sync ACLs with bugzilla.

    :arg session: the session to connect to the database with.
    :kwarg name: restricts the output to a specific collection name.

    """
    output = {}
    pkgs = model.bugzilla(session=session, name=name)
    for pkg in pkgs:
        if pkg[0] in output:
            if pkg[2] in output[pkg[0]]:
                # Check poc
                if pkg[4] == 'orphan':
                    pass
                elif pkg[6] == 'devel':
                    output[pkg[0]][pkg[2]]['poc'] = pkg[4]
                elif pkg[6] > output[pkg[0]][pkg[2]]['version']:  # pragma: no cover
                    ## TODO: check this logic w/ Toshio
                    output[pkg[0]][pkg[2]]['poc'] = pkg[4]
                # If #5 is not poc, add it to cc
                if not pkg[5] == 'orphan' \
                        and pkg[5] != output[pkg[0]][pkg[2]]['poc'] \
                        and pkg[5] not in output[pkg[0]][pkg[2]]['cc']:
                    if output[pkg[0]][pkg[2]]['cc']:
                        output[pkg[0]][pkg[2]]['cc'] += ','
                    output[pkg[0]][pkg[2]]['cc'] += pkg[5]
            else:
                cc = ''
                if pkg[5] != pkg[4]:  # pragma: no cover
                    cc = pkg[5]
                output[pkg[0]][pkg[2]] = {
                    'collection': pkg[0],
                    'name': pkg[2],
                    'summary': pkg[3],
                    'poc': pkg[4],
                    'qa': '',
                    'cc': cc,
                    'version': pkg[6],
                }
        else:
            cc = ''
            if pkg[5] != pkg[4]:
                cc = pkg[5]
            output[pkg[0]] = {
                pkg[2]: {
                    'collection': pkg[0],
                    'name': pkg[2],
                    'summary': pkg[3],
                    'poc': pkg[4],
                    'qa': '',
                    'cc': cc,
                    'version': pkg[6],
                }
            }

    return output


def vcs_acls(session):
    """ Return the information to sync ACLs with gitolite.

    :arg session: the session to connect to the database with.

    """
    output = {}
    pkgs = model.vcs_acls(session=session)
    for pkg in pkgs:
        user = None
        group = None
        if pkg[1].startswith('group::'):
            group = pkg[1].replace('group::', '@')
        else:
            user = pkg[1]

        if pkg[0] in output:
            if pkg[2] in output[pkg[0]]:
                if user:
                    if output[pkg[0]][pkg[2]]['user']:
                        output[pkg[0]][pkg[2]]['user'] += ','
                    output[pkg[0]][pkg[2]]['user'] += user
                elif group:  # pragma: no cover
                    if output[pkg[0]][pkg[2]]['group']:
                        output[pkg[0]][pkg[2]]['group'] += ','
                    output[pkg[0]][pkg[2]]['group'] += group
            else:
                if group:  # pragma: no cover
                    group = ',' + group
                output[pkg[0]][pkg[2]] = {
                    'name': pkg[0],
                    'user': user or '',
                    'group': '@provenpackager' + (group or ''),
                    'branch': pkg[2],
                }
        else:
            if group:
                group = ',' + group
            output[pkg[0]] = {
                pkg[2]: {
                    'name': pkg[0],
                    'user': user or '',
                    'group': '@provenpackager' + (group or ''),
                    'branch': pkg[2],
                }
            }

    return output
