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
API for collection management.
'''

import flask

import pkgdb.lib as pkgdblib
import pkgdb.forms as forms
from pkgdb.api import API
from pkgdb.lib import model


## Collection
@API.route('/collection/new/', methods=['POST'])
@API.route('/collection/new', methods=['POST'])
def api_collection_new():
    ''' Create a new collection.

    :arg collectionname: String of the collection name to be created.
    :arg version: String of the version of the collection.
    :arg owner: String of the name of the user owner of the collection.

    '''
    httpcode = 200
    output = {}

    form = forms.AddCollectionForm(csrf_enabled=False)
    if form.validate_on_submit():
        clt_name = form.collection_name.data
        clt_version = form.collection_version.data
        clt_status = form.collection_status.data
        clt_publishurl = form.collection_publishURLTemplate.data
        clt_pendingurl = form.collection_pendingURLTemplate.data
        clt_summary = form.collection_summary.data
        clt_description = form.collection_description.data
        clt_branchname = form.collection_branchname.data
        clt_disttag = form.collection_distTag.data
        clt_gitbranch = form.collection_git_branch_name.data

        try:
            message = pkgdblib.add_collection(
                SESSION,
                clt_name=clt_name,
                clt_version=clt_version,
                clt_status=clt_status,
                clt_publishurl=clt_publishurl,
                clt_pendingurl=clt_pendingurl,
                clt_summary=clt_summary,
                clt_description=clt_description,
                clt_branchname=clt_branchname,
                clt_disttag=clt_disttag,
                clt_gitbranch=clt_gitbranch,
                user=flask.g.fas_user,
            )
            SESSION.commit()
            output['output'] = 'ok'
            output['messages'] = [message]
        except pkgdblib.PkgdbException, err:
            SESSION.rollback()
            output['output'] = 'notok'
            output['error'] = err
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
def api_collection_status(collection):
    ''' Update the status of collection.

    :arg branchname: String of the collection branch name to change.
    :arg status: String of the status to change the collection to

    '''
    httpcode = 200
    output = {}

    form = forms.CollectionStatusForm(csrf_enabled=False)
    if form.validate_on_submit():
        clt_branchname = form.collection_branchname.data
        clt_status = form.collection_status.data

        if collection == clt_branchname:
            try:
                message = pkgdblib.update_collection_status(
                    SESSION,
                    clt_branchname,
                    clt_status,
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
@API.route('/collections/<pattern>/')
@API.route('/collections/<pattern>')
def api_collection_list(pattern=None):
    ''' List collections.

    '''
    httpcode = 200
    output = {}

    pattern = flask.request.args.get('pattern', None) or pattern
    status = flask.request.args.get('status', None)
    if pattern:
        collections = pkgdblib.search_collection(SESSION,
                                                 pattern=pattern,
                                                 status=status
                                                 )
    else:
        collections = model.Collection.all(SESSION)
    output = {'collections':
              [collec.api_repr(1) for collec in collections]
              }

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout
