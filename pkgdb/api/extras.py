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
Extras API endpoints for the Flask application.
'''

import itertools
import flask

from sqlalchemy.orm.exc import NoResultFound

import pkgdb
import pkgdb.lib as pkgdblib
from pkgdb import SESSION
from pkgdb.api import API


def _format_row(branch, package):
    """ Format a row for the bugzilla output. """
    cclist = ','.join(
        [pkg.fas_name
         for pkg in branch.acls if pkg.acl == 'commit'
            and pkg.fas_name != branch.point_of_contact]
    )
    output = "|".join([
            branch.collection.name,
            package.name,
            package.summary,
            branch.point_of_contact,
            cclist,
        ])
    return output


@pkgdb.cache.cache_on_arguments(expiration_time=3600)
def _bz_acls_cached(name=None):
    '''Return the package attributes used by bugzilla.

    :karg collection: Name of the bugzilla collection to gather data on.

    Note: The data returned by this function is for the way the current
    Fedora bugzilla is setup as of (2007/6/25).  In the future, bugzilla
    may change to have separate products for each collection-version.
    When that happens we'll have to change what this function returns.

    The returned data looks like this:

    bugzillaAcls[collection][package].attribute
    attribute is one of:
        :owner: FAS username for the owner
        :qacontact: if the package has a special qacontact, their userid
            is listed here
        :summary: Short description of the package
        :cclist: list of FAS userids that are watching the package
    '''

    packages = pkgdblib.search_package(SESSION, '*')
    output = []
    for package in packages:
        branch_fed = None
        branch_epel = None
        for branch in package.listings:
            # If a name is provided and the collection hasn't this name
            # keep moving
            if name and branch.collection.name != name:
                continue

            # Consider the devel branch, unless it is orphan then consider
            # the next one
            if branch.collection.name == 'Fedora':
                if branch.collection.branchname == 'devel':
                    branch_fed = branch
                    if branch.point_of_contact != 'orphan':
                        break
                elif not branch_fed \
                        or branch_fed.point_of_contact == 'orphan' \
                        or int(branch.version) > int(branch_fed.version):
                    branch_fed = branch
            elif branch.collection.name == 'Fedora EPEL':
                if branch.collection.branchname == 'EL-6':
                    branch_epel = branch
                    if branch.point_of_contact != 'orphan':
                        break
                elif not branch_epel \
                        or branch_epel.point_of_contact == 'orphan' \
                        or int(branch.version) > int(branch_epel.version):
                    branch_epel = branch

        if branch_fed:
            output.append(_format_row(branch_fed, package))
        if branch_epel:
            output.append(_format_row(branch_epel, package))
    return output


@pkgdb.cache.cache_on_arguments(expiration_time=3600)
def _bz_notify_cache(name=None, version=None, eol=False):
    '''List of usernames that should be notified of changes to a package.

    For the collections specified we want to retrieve all of the owners,
    watchbugzilla, and watchcommits accounts.

    :kwarg name: Set to a collection name to filter the results for that
    :kwarg version: Set to a collection version to further filter results
        for a single version
    :kwarg eol: Set to True if you want to include end of life
        distributions
    '''
    packages = pkgdblib.search_package(SESSION, '*')
    output = []
    for package in packages:
        users = []
        for branch in package.listings:
            # If a name is provided and the collection hasn't this name
            # keep moving
            if name and branch.collection.name != name:
                continue

            # If a version is provided and the collection hasn't this version
            # keep moving
            if version and branch.collection.version != str(version):
                continue

            # Skip EOL branch unless asked
            if not eol and branch.collection.status == 'EOL':
                continue

            for acl in branch.acls:
                if acl.fas_name not in users:
                    if acl.acl in ('commit', 'watchbugzilla',
                                   'watchcommits'):
                        users.append(acl.fas_name)

        if users:
            output.append('%s|%s' % (package.name, ','.join(users)))
    return output


@pkgdb.cache.cache_on_arguments(expiration_time=3600)
def _vcs_acls_cache():
    '''Return ACLs for the version control system.

    '''
    packages = pkgdblib.search_package(SESSION, '*')
    output = []
    for package in packages:
        for branch in package.listings:
            users = []

            # Skip EOL branch
            if branch.collection.status == 'EOL':
                continue

            for acl in branch.acls:
                if acl.fas_name not in users:
                    if acl.acl in ('commit'):
                        username = acl.fas_name
                        if username.startswith('group::'):
                            username = username.replace('group::', '@')
                        users.append(username)

            output.append('avail | @provenpackager,%s | rpms/%s/%s' % (
                ','.join(users), package.name,
                branch.collection.git_branch_name))
    return output

@API.route('/bugzilla/')
@API.route('/bugzilla')
def bugzilla():
    '''Return the package attributes used by bugzilla.

    :karg collection: Name of the bugzilla collection to gather data on.

    Note: The data returned by this function is for the way the current
    Fedora bugzilla is setup as of (2007/6/25).  In the future, bugzilla
    may change to have separate products for each collection-version.
    When that happens we'll have to change what this function returns.

    The returned data looks like this:

    bugzillaAcls[collection][package].attribute
    attribute is one of:
        :owner: FAS username for the owner
        :qacontact: if the package has a special qacontact, their userid
            is listed here
        :summary: Short description of the package
        :cclist: list of FAS userids that are watching the package
    '''

    name = flask.request.args.get('collection', None)

    intro = """# Package Database VCS Acls
# Text Format
# Collection|Package|Description|Owner|Initial QA|Initial CCList
# Backslashes (\) are escaped as \u005c Pipes (|) are escaped as \u007c

"""

    acls = _bz_acls_cached(name)

    return flask.Response(
        intro + "\n".join(acls),
        content_type="text/plain;charset=UTF-8"
    )


@API.route('/notify/')
@API.route('/notify')
def notify():
    '''List of usernames that should be notified of changes to a package.

    For the collections specified we want to retrieve all of the owners,
    watchbugzilla, and watchcommits accounts.

    :kwarg name: Set to a collection name to filter the results for that
    :kwarg version: Set to a collection version to further filter results
        for a single version
    :kwarg eol: Set to True if you want to include end of life
        distributions
    '''

    name = flask.request.args.get('name', None)
    version = flask.request.args.get('version', None)
    eol = flask.request.args.get('eol', False)

    notify = _bz_notify_cache(name, version, eol)

    return flask.Response(
        "\n".join(notify),
        content_type="text/plain;charset=UTF-8"
    )


@API.route('/vcs/')
@API.route('/vcs')
def vcs():
    '''Return ACLs for the version control system.

    '''
    intro = """# VCS ACLs
# avail|@groups,users|rpms/Package/branch

"""

    acls = _vcs_acls_cache()

    return flask.Response(
        intro + "\n".join(acls),
        content_type="text/plain;charset=UTF-8"
    )
