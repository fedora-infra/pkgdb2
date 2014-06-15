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
from pkgdb2 import SESSION, APP, is_admin
from pkgdb2.api import API


@API.route('/admin/actions/')
@is_admin
def admin_actions():
    """ Return the actions requested and requiring intervention from an
    admin.
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

    try:
        limit = abs(int(limit))
    except ValueError:
        limit = APP.config['ITEMS_PER_PAGE']
        flask.flash('Incorrect limit provided, using default', 'errors')

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
            eol=eol,
            count=True,
        )
    except pkgdblib.PkgdbException, err:
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
        output['packages'] = [
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
