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
from pkgdb2 import SESSION, APP
from pkgdb2.api import API, get_limit


@API.route('/admin/actions/')
def api_admin_actions():
    """
List admin actions
------------------
    List actions requiring intervention from an admin.

    ::

        /api/admin/actions

        /api/admin/actions

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
          "packages": [
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
