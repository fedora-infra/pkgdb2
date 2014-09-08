# -*- coding: utf-8 -*-
#
# Copyright © 2014  Red Hat, Inc.
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
Admin interface for the API.
'''

import flask

from dateutil import parser
from math import ceil

import pkgdb2.lib as pkgdblib
import pkgdb2.forms
from pkgdb2 import SESSION, APP, is_admin
from pkgdb2.api import API, get_limit


@API.route('/admin/actions/')
@API.route('/admin/actions')
def api_admin_actions():
    """
List admin actions
------------------
    List actions requiring intervention from an admin.

    ::

        /api/admin/actions/

    Accept GET queries only.

    :kwarg package: restrict the actions to a specific package.
    :kwarg packager: restrict the actions to a specific packager.
    :kwarg action: restrict the actions to a specific action, options are:
        ``request.branch``.
    :kwarg status: restrict the actions depending on their status, options
        are: ``Awaiting Review``, ``Approved``, ``Denied``, ``Obsolete``,
        ``Removed``.
    :kwarg limit: An integer to limit the number of results, defaults to
        250, maximum is 500.
    :kwarg page: The page number to return (useful in combination to limit).

    Sample response:

    ::

        /api/admin/actions

        {
          "output": "ok",
          "actions": [
            {
              "action": "request.branch",
              "collection": {
                "branchname": "epel7",
                "dist_tag": ".el7",
                "koji_name": "epel7",
                "name": "Fedora EPEL",
                "status": "Active",
                "version": "7"
              },
              "date_created": 1402470695.0,
              "date_updated": 1402470695.0,
              "from_collection": {
                "branchname": "f19",
                "dist_tag": ".fc19",
                "koji_name": "f19",
                "name": "Fedora",
                "status": "Active",
                "version": "19"
              },
              "id": 8,
              "info": null,
              "package": {
                "acls": [],
                "creation_date": 1400063778.0,
                "description": "Guake is a drop-down terminal for Gnome "
                               "Desktop Environment, so you just need to "
                               "press a key to invoke him, and press again "
                               "to hide.",
                "name": "guake",
                "review_url": null,
                "status": "Approved",
                "summary": "Drop-down terminal for GNOME",
                "upstream_url": "http://guake.org/"
              },
              "status": "Awaiting Review",
              "user": "pingou"
            }
          ],
          "page": 1,
          "page_total": 1
        }

    .. note:: the ``date_created`` and ``date_updated`` fields are both
            timestamps expressed in
            `Unix TIME <https://en.wikipedia.org/wiki/Unix_time>`_

    """
    package = flask.request.args.get('package', None)
    packager = flask.request.args.get('packager', None)
    action = flask.request.args.get('action', None)
    status = flask.request.args.get('status', None)
    page = flask.request.args.get('page', 1)
    limit = get_limit()

    httpcode = 200
    output = {}

    try:
        page = abs(int(page))
    except ValueError:
        page = 1

    actions = []
    cnt_actions = 0
    try:
        actions = pkgdblib.search_actions(
            SESSION,
            package=package or None,
            packager=packager or None,
            action=action,
            status=status,
            limit=limit,
            page=page
        )

        cnt_actions += pkgdblib.search_actions(
            SESSION,
            package=package or None,
            packager=packager or None,
            action=action,
            status=status,
            count=True,
        )
    except pkgdblib.PkgdbException, err:  # pragma: no cover
        SESSION.rollback()
        output['output'] = 'notok'
        output['error'] = str(err)
        httpcode = 500

    if not actions:
        output['output'] = 'notok'
        output['actions'] = []
        output['error'] = 'No actions found for these parameters'
        httpcode = 404
    else:
        output['actions'] = [
            action.to_json()
            for action in actions
        ]
        output['output'] = 'ok'
        output['page'] = int(page)
        output['page_total'] = int(ceil(cnt_actions / float(limit)))

    if 'page_total' not in output:
        output['page'] = 1
        output['page_total'] = 1

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/admin/action/<actionid>')
@API.route('/admin/action/')
def api_admin_action(actionid=None):
    '''
Return a specific Admin Action
------------------------------
    Return the desired Admin Action using its identifier.

    ::

        /admin/action/<actionid>
        /admin/action/?actionid=<actionid>

    Accept GET queries only.

    :arg actionid: An integer representing the identifier of the admin
        action in the database. The identifier is returned in the
        API, see ``List admin actions``.

    Sample response:

    ::

        {
          "action": "request.branch",
          "collection": {
            "branchname": "epel7",
            "dist_tag": ".el7",
            "koji_name": "epel7",
            "name": "Fedora EPEL",
            "status": "Active",
            "version": "7"
          },
          "date_created": 1410161489.0,
          "date_updated": 1410168952.0,
          "from_collection": {
            "branchname": "master",
            "dist_tag": ".fc21",
            "koji_name": "rawhide",
            "name": "Fedora",
            "status": "Under Development",
            "version": "devel"
          },
          "id": 1,
          "info": {},
          "package": {
            "acls": [],
            "creation_date": 1397204290.0,
            "description": null,
            "name": "R-BiocGenerics",
            "review_url": null,
            "status": "Approved",
            "summary": "Generic functions for Bioconductor",
            "upstream_url": null
          },
          "status": "Approved",
          "user": "pingou"
        }

    '''
    httpcode = 200
    output = {}

    actionid = flask.request.args.get('actionid', actionid)

    admin_action = pkgdblib.get_admin_action(SESSION, actionid)
    if not admin_action:
        output['output'] = 'notok'
        output['error'] = 'No Admin action with this identifier found'
        httpcode = 500
    else:
        output = admin_action.to_json()
        output['output'] = 'ok'

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/admin/action/status', methods=['POST'])
@is_admin
def api_admin_action_edit_status():
    '''
Edit Admin Action status update
-------------------------------
    Edit the status of an Admin Action.

    ::

        /admin/action/status

    Accept POST queries only.

    :arg id: An integer representing the identifier of the admin
        action to update in the database. The identifier is returned in the
        API, see ``List admin actions``.
    :arg status: The status to which the action should be updated.
        Can be any of: ``Approved``, ``Awaiting Review``, ``Denied``,
        ``Obsolete``, ``Removed``.

    Sample response:

    ::

        {
          "output": "ok",
          "messages": ["Admin action status updated to: Approved"]
        }

        {
          "output": "notok",
          "error": ["You are not an admin"]
        }

    '''
    httpcode = 200
    output = {}

    action_status = pkgdblib.get_status(SESSION, 'acl_status')['acl_status']

    form = pkgdb2.forms.EditActionStatusForm(
        csrf_enabled=False,
        status=action_status,
    )
    if form.validate_on_submit():
        action_id = form.id.data

        admin_action = pkgdblib.get_admin_action(SESSION, action_id)
        if not admin_action:
            output['output'] = 'notok'
            output['error'] = 'No Admin action with this identifier found'
            httpcode = 500
        else:

            try:
                message = pkgdblib.edit_action_status(
                    SESSION,
                    admin_action,
                    action_status=form.status.data,
                    user=flask.g.fas_user
                )
                SESSION.commit()
                output['output'] = 'ok'
                output['messages'] = [message]
            except pkgdblib.PkgdbException, err:  # pragma: no cover
                # We can only reach here in two cases:
                # 1) the user is not an admin, but that's taken care of
                #    by the decorator
                # 2) we have a SQLAlchemy problem when storing the info
                #    in the DB which we cannot test
                SESSION.rollback()
                output['output'] = 'notok'
                output['error'] = str(err)
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
