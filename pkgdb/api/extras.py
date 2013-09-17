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


def _format_row(branch, package, output='text'):
    """ Format a row for the bugzilla output. """
    if output == 'json':
        groups = []
        users = []

        for pkg in branch.acls:
            if pkg.acl == 'commit' \
                    and pkg.fas_name != branch.point_of_contact:
                if pkg.fas_name.startswith('group::'):
                    groups.append(pkg.fas_name.replace('group::', '@'))
                else:
                    users.append(pkg.fas_name)
        out = {
            package.name: {
                'qacontact': None,
                'owner': branch.point_of_contact,
                'summary': package.summary,
                'cclist' : {
                    'groups': groups,
                    'people': users
                }
            }
        }

    else:
        cclist = ','.join(
            [pkg.fas_name
             for pkg in branch.acls if pkg.acl == 'commit'
                and pkg.fas_name != branch.point_of_contact]
        )
        out = "|".join([
                branch.collection.name,
                package.name,
                package.summary,
                branch.point_of_contact,
                cclist,
            ])
    return out


@pkgdb.cache.cache_on_arguments(expiration_time=3600)
def _bz_acls_cached(name=None, out_format='text'):
    '''Return the package attributes used by bugzilla.

    :kwarg collection: Name of the bugzilla collection to gather data on.
    :kwarg out_format: Specify if the output if text or json.

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
    if out_format == 'json':
        output = {'bugzillaAcls':{},
                  'title': 'Fedora Package Database -- Bugzilla ACLs'}
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

        if out_format == 'json':
            if branch_fed:
                if 'Fedora' not in output['bugzillaAcls']:
                    output['bugzillaAcls']['Fedora'] = []
                output['bugzillaAcls']['Fedora'].append(
                    _format_row(branch_fed, package, output=out_format))
            if branch_epel:
                if 'Fedora EPEL' not in output['bugzillaAcls']:
                    output['bugzillaAcls']['Fedora EPEL'] = []
                output['bugzillaAcls']['Fedora EPEL'].append(
                    _format_row(branch_epel, package, output=out_format))
        else:
            if branch_fed:
                output.append(_format_row(branch_fed, package, output=out_format))
            if branch_epel:
                output.append(_format_row(branch_epel, package, output=out_format))
    return output


@pkgdb.cache.cache_on_arguments(expiration_time=3600)
def _bz_notify_cache(name=None, version=None, eol=False, out_format='text'):
    '''List of usernames that should be notified of changes to a package.

    For the collections specified we want to retrieve all of the owners,
    watchbugzilla, and watchcommits accounts.

    :kwarg name: Set to a collection name to filter the results for that
    :kwarg version: Set to a collection version to further filter results
        for a single version
    :kwarg eol: Set to True if you want to include end of life
        distributions
    :kwarg out_format: Specify if the output if text or json.
    '''
    packages = pkgdblib.search_package(SESSION, '*')
    output = []
    if out_format == 'json':
        output = {'packages': [],
                  'eol': eol,
                  'name': name,
                  'version': version,
                  'title': 'Fedora Package Database -- Notification List'}
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
            if out_format == 'json':
                output['packages'].append({package.name: users})
            else:
                output.append('%s|%s' % (package.name, ','.join(users)))
    return output


@pkgdb.cache.cache_on_arguments(expiration_time=3600)
def _vcs_acls_cache(out_format='text'):
    '''Return ACLs for the version control system.
    :kwarg out_format: Specify if the output if text or json.

    '''
    packages = pkgdblib.search_package(SESSION, '*')
    output = []
    if out_format=='json':
        output = {'packageAcls': {},
                  'title': 'Fedora Package Database -- VCS ACLs'}
    for package in packages:
        for branch in package.listings:
            users = []
            groups = ['@provenpackager']

            # Skip EOL branch
            if branch.collection.status == 'EOL':
                continue

            for acl in branch.acls:
                if acl.fas_name not in users:
                    if acl.acl in ('commit'):
                        username = acl.fas_name
                        if username.startswith('group::'):
                            groups.append(username.replace('group::', '@'))
                        else:
                            users.append(username)

            if out_format=='json':
                groups = [group.replace('@', '') for group in groups]
                if not package.name in output['packageAcls']:
                    output['packageAcls'][package.name] = {}
                output['packageAcls'][package.name][
                    branch.collection.git_branch_name] = {
                        'commit': {'groups': groups, 'people': users}
                    }
            else:
                output.append('avail | %s,%s | rpms/%s/%s' % (
                    ','.join(groups), ','.join(users), package.name,
                    branch.collection.git_branch_name))
    return output


@API.route('/bugzilla/')
@API.route('/bugzilla')
def api_bugzilla():
    '''Return the package attributes used by bugzilla.

    :karg collection: Name of the bugzilla collection to gather data on.
    :kwarg out_format: Specify if the output if text or json.

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
    out_format = flask.request.args.get('format', 'text')
    if out_format not in ('text', 'json'):
        out_format='text'

    intro = """# Package Database VCS Acls
# Text Format
# Collection|Package|Description|Owner|Initial QA|Initial CCList
# Backslashes (\) are escaped as \u005c Pipes (|) are escaped as \u007c

"""

    acls = _bz_acls_cached(name, out_format)

    if out_format == 'json':
        return flask.jsonify(acls)
    else:
        return flask.Response(
            intro + "\n".join(acls),
            content_type="text/plain;charset=UTF-8"
        )


@API.route('/notify/')
@API.route('/notify')
def api_notify():
    '''List of usernames that should be notified of changes to a package.

    For the collections specified we want to retrieve all of the owners,
    watchbugzilla, and watchcommits accounts.

    :kwarg name: Set to a collection name to filter the results for that
    :kwarg version: Set to a collection version to further filter results
        for a single version
    :kwarg eol: Set to True if you want to include end of life
        distributions
    :kwarg out_format: Specify if the output if text or json.
    '''

    name = flask.request.args.get('name', None)
    version = flask.request.args.get('version', None)
    eol = flask.request.args.get('eol', False)
    out_format = flask.request.args.get('format', 'text')
    if out_format not in ('text', 'json'):
        out_format='text'

    notify = _bz_notify_cache(name, version, eol, out_format)


    if out_format == 'json':
        return flask.jsonify(notify)
    else:
        return flask.Response(
            "\n".join(notify),
            content_type="text/plain;charset=UTF-8"
        )


@API.route('/vcs/')
@API.route('/vcs')
def api_vcs():
    '''Return ACLs for the version control system.
    :kwarg out_format: Specify if the output if text or json.

    '''
    intro = """# VCS ACLs
# avail|@groups,users|rpms/Package/branch

"""

    out_format = flask.request.args.get('format', 'text')
    if out_format not in ('text', 'json'):
        out_format='text'

    acls = _vcs_acls_cache(out_format)

    if out_format == 'json':
        return flask.jsonify(acls)
    else:
        return flask.Response(
            intro + "\n".join(acls),
            content_type="text/plain;charset=UTF-8"
        )
