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

import flask

import pkgdb2.lib as pkgdblib
from pkgdb2 import SESSION
from pkgdb2.api import API


def request_wants_json():
    """ Return weather a json output was requested. """
    best = flask.request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        flask.request.accept_mimetypes[best] > \
        flask.request.accept_mimetypes['text/html']


#@pkgdb.CACHE.cache_on_arguments(expiration_time=3600)
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

    packages = pkgdblib.bugzilla(
        session=SESSION,
        name=name)

    output = []
    if out_format == 'json':
        output = {'bugzillaAcls': {},
                  'title': 'Fedora Package Database -- Bugzilla ACLs'}

    for clt in sorted(packages):
        for pkg in sorted(packages[clt]):
            if out_format == 'json':
                user = []
                group = []
                for ppl in packages[clt][pkg]['cc'].split(','):
                    if ppl.startswith('group::'):
                        group.append(ppl)
                    elif ppl:
                        user.append(ppl)
                poc = packages[clt][pkg]['poc']
                if poc.startswith('group::'):
                    poc = poc.replace('group::', '@')
                if not clt in output['bugzillaAcls']:
                    output['bugzillaAcls'][clt] = []
                output['bugzillaAcls'][clt].append({pkg: {
                    'owner': poc,
                    'cclist': {
                        'groups': group,
                        'people': user,
                    },
                    'qacontact': None,
                    'summary': packages[clt][pkg]['summary']
                }})
            else:
                output.append(
                    '%(collection)s|%(name)s|%(summary)s|%(poc)s|%(qa)s'
                    '|%(cc)s' % (packages[clt][pkg])
                )
    return output


#@pkgdb.CACHE.cache_on_arguments(expiration_time=3600)
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
    packages = pkgdblib.notify(
        session=SESSION,
        eol=eol,
        name=name,
        version=version)
    output = []
    if out_format == 'json':
        output = {'packages': [],
                  'eol': eol,
                  'name': name,
                  'version': version,
                  'title': 'Fedora Package Database -- Notification List'}
    for package in sorted(packages):
        if out_format == 'json':
            output['packages'].append(
                {package: packages[package].split(',')})
        else:
            output.append('%s|%s\n' % (package, packages[package]))
    return output


#@pkgdb.CACHE.cache_on_arguments(expiration_time=3600)
def _vcs_acls_cache(out_format='text'):
    '''Return ACLs for the version control system.
    :kwarg out_format: Specify if the output if text or json.

    '''
    packages = pkgdblib.vcs_acls(session=SESSION)
    output = []
    if out_format == 'json':
        output = {'packageAcls': {},
                  'title': 'Fedora Package Database -- VCS ACLs'}
    for package in sorted(packages):
        for branch in sorted(packages[package]):
            if out_format == 'json':
                if not package in output['packageAcls']:
                    output['packageAcls'][package] = {}
                groups = []
                if packages[package][branch]['group']:
                    groups = packages[package][branch]['group'].replace(
                        '@', '').split(',')
                users = []
                if packages[package][branch]['user']:
                    users = packages[package][branch]['user'].split(',')
                output['packageAcls'][package][branch] = {
                    'commit': {
                        'groups': groups,
                        'people': users
                    }
                }
            else:
                output.append(
                    'avail | %(group)s,%(user)s | rpms/%(name)s/%(branch)s'
                    % (packages[package][branch]))
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
        out_format = 'text'

    if request_wants_json():
        out_format = 'json'

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
        out_format = 'text'

    if request_wants_json():
        out_format = 'json'

    output = _bz_notify_cache(name, version, eol, out_format)

    if out_format == 'json':
        return flask.jsonify(output)
    else:
        return flask.Response(
            output,
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
        out_format = 'text'

    if request_wants_json():
        out_format = 'json'

    acls = _vcs_acls_cache(out_format)

    if out_format == 'json':
        return flask.jsonify(acls)
    else:
        return flask.Response(
            intro + "\n".join(acls),
            content_type="text/plain;charset=UTF-8"
        )


@API.route('/critpath/')
@API.route('/critpath')
def api_critpath():
    '''Return the list of package marked as critpath for all active release
    of fedora.

    :kwarg out_format: Specify if the output if text or json.

    '''

    out_format = flask.request.args.get('format', 'text')
    if out_format not in ('text', 'json'):
        out_format = 'text'

    if request_wants_json():
        out_format = 'json'

    output = {}

    active_collections = pkgdblib.search_collection(
        SESSION, '*', status='Under Development')
    active_collections.extend(
        pkgdblib.search_collection(SESSION, '*', status='Active'))

    for collection in active_collections:
        if collection.name != 'Fedora':
            continue
        pkgs = pkgdblib.get_critpath_packages(
            SESSION, branch=collection.branchname)
        if not pkgs:
            continue
        output[collection.branchname] = [pkg.package.name for pkg in pkgs]

    if out_format == 'json':
        output = {"pkgs": output}
        return flask.jsonify(output)
    else:
        output_str = ""
        keys = output.keys()
        keys.reverse()
        for key in keys:
            output_str += "== %s ==\n" % key
            for pkg in output[key]:
                output_str += "* %s\n" % pkg
        return flask.Response(
            output_str,
            content_type="text/plain;charset=UTF-8"
        )
