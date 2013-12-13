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
Collections
===========

API for collection management.
'''

import flask

import pkgdb2.lib as pkgdblib
from pkgdb2 import SESSION, forms, is_admin
from pkgdb2.api import API
from pkgdb2.lib import model


## Some of the object we use here have inherited methods which apparently
## pylint does not detect.
# pylint: disable=E1101


## Collection
@API.route('/collection/new/', methods=['POST'])
@API.route('/collection/new', methods=['POST'])
@is_admin
def api_collection_new():
    '''
New collection
--------------
    Create a new collection.

    ::

        /api/collection/new/

    Accept POST queries only.

    :arg collection_name: String of the collection name to be created.
    :arg collection_version: String of the version of the collection.
    :arg collection_status: String of the name of the user owner of the
        collection.
    :arg collection_publishURLTemplate:
    :arg collection_pendingURLTemplate:
    :arg collection_summary: A summary description of the collection.
    :arg collection_description: A description of the collection.
    :arg collection_branchname: The short name of the collection (ie: F-18).
    :arg collection_distTag: The dist tag used by rpm for this collection
        (ie: .fc18).
    :arg collection_git_branch_name: The git branch name for this collection
        (ie: f18).

    Sample response:

    ::

        {
          "output": "ok",
          "messages": ["Collection F-20 created"]
        }

        {
          "output": "notok",
          "error": ["You are not allowed to create collections"]
        }

    '''
    httpcode = 200
    output = {}

    clt_status = pkgdblib.get_status(SESSION, 'clt_status')['clt_status']

    form = forms.AddCollectionForm(
        csrf_enabled=False,
        clt_status=clt_status,
    )
    if form.validate_on_submit():
        clt_name = form.collection_name.data
        clt_version = form.collection_version.data
        clt_status = form.collection_status.data
        clt_branchname = form.collection_branchname.data
        clt_disttag = form.collection_distTag.data
        clt_gitbranch = form.collection_git_branch_name.data

        try:
            message = pkgdblib.add_collection(
                SESSION,
                clt_name=clt_name,
                clt_version=clt_version,
                clt_status=clt_status,
                clt_branchname=clt_branchname,
                clt_disttag=clt_disttag,
                clt_gitbranch=clt_gitbranch,
                user=flask.g.fas_user,
            )
            SESSION.commit()
            output['output'] = 'ok'
            output['messages'] = [message]
        # Apparently we're pretty tight on checks and looks like we cannot
        # raise this exception in a normal situation
        except pkgdblib.PkgdbException, err:  # pragma: no cover
            SESSION.rollback()
            output['output'] = 'notok'
            output['error'] = err.message
            httpcode = 500
    else:
        output['output'] = 'notok'
        output['error'] = 'Invalid input submitted'
        if form.errors:
            detail = []
            for error in form.errors:
                detail.append('%s: %s' % (error,
                              '; '.join(form.errors[error])))
            output['error_detail'] = detail
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/collection/<collection>/status/', methods=['POST'])
@API.route('/collection/<collection>/status', methods=['POST'])
@is_admin
def api_collection_status(collection):
    '''
Update collection status
------------------------
    Update the status of collection.

    ::

        /api/collection/<collection branchname>/status/

    Accept POST query only.

    :arg collection_branchname: String of the collection branch name to change.
    :arg collection_status: String of the status to change the collection to

    Sample response:

    ::

        {
          "output": "ok",
          "messages": ["Collection updated to \"EOL\""]
        }

        {
          "output": "notok",
          "error": ["You are not allowed to edit collections"]
        }

    '''
    httpcode = 200
    output = {}

    clt_status = pkgdblib.get_status(SESSION, 'clt_status')['clt_status']

    form = forms.CollectionStatusForm(
        csrf_enabled=False,
        clt_status=clt_status,
    )
    if form.validate_on_submit():
        clt_branchname = form.collection_branchname.data
        clt_status = form.collection_status.data

        if collection == clt_branchname:
            try:
                message = pkgdblib.update_collection_status(
                    SESSION,
                    clt_branchname,
                    clt_status,
                    user=flask.g.fas_user
                )
                SESSION.commit()
                output['output'] = 'ok'
                output['messages'] = [message]
            except pkgdblib.PkgdbException, err:
                SESSION.rollback()
                output['output'] = 'notok'
                output['error'] = err.message
                httpcode = 500
        else:
            output['output'] = 'notok'
            output['error'] = "You're trying to update the " \
                              "wrong collection"
            httpcode = 500
    else:
        output['output'] = 'notok'
        output['error'] = 'Invalid input submitted'
        if form.errors:
            detail = []
            for error in form.errors:
                detail.append('%s: %s' % (error,
                              '; '.join(form.errors[error])))
            output['error_detail'] = detail
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/collections/')
@API.route('/collections')
@API.route('/collections/<pattern>/')
@API.route('/collections/<pattern>')
def api_collection_list(pattern=None):
    '''
List collections
----------------
    List the collections based on a pattern. If no pattern is provided, it
    will return all the collection.

    ::

        /api/collections/<pattern>/

        /api/collections/?pattern=<pattern>

    Accept GET queries only.

    :arg pattern: a pattern to which the collection searched should match.
    :arg status: restrict the search to certain status.

    Sample response:

    ::

        /api/collections

        {
          "collections": [
            {
              "status": "Active",
              "branchname": "f20",
              "version": "20",
              "name": "Fedora"
            },
            {
              "status": "EOL",
              "branchname": "F-17",
              "version": "17",
              "name": "Fedora"
            },
                {
              "status": "Active",
              "branchname": "EL-6",
              "version": "6",
              "name": "Fedora EPEL"
            }
          ]
        }

    ::

        /api/collections?pattern=EL*

        {
          "collections": [
            {
              "status": "EOL",
              "branchname": "EL-4",
              "version": "4",
              "name": "Fedora EPEL"
            },
            {
              "status": "Active",
              "branchname": "EL-5",
              "version": "5",
              "name": "Fedora EPEL"
            },
            {
              "status": "Active",
              "branchname": "EL-6",
              "version": "6",
              "name": "Fedora EPEL"
            }
          ]
        }
    '''
    httpcode = 200
    output = {}

    pattern = flask.request.args.get('pattern', None) or pattern
    status = flask.request.args.get('status', None)
    if pattern:
        if status:
            if ',' in status:
                status = status.split(',')
            else:
                status = [status]
            collections = []
            for stat in status:
                collections.extend(pkgdblib.search_collection(
                    SESSION, pattern=pattern, status=stat)
                )
        else:
            collections = pkgdblib.search_collection(
                SESSION, pattern=pattern)
    else:
        collections = model.Collection.all(SESSION)
    output = {'collections':
              [collec.to_json() for collec in collections]
              }

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout
