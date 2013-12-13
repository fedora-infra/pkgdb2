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
Admin interface for the Flask application.
'''

import flask

from dateutil import parser
from math import ceil

import pkgdb2.lib as pkgdblib
from pkgdb2 import SESSION, APP, is_admin
from pkgdb2.ui import UI


@UI.route('/admin/')
@is_admin
def admin():
    ''' Index page of the admin interface. '''
    return flask.render_template('admin.html')


@UI.route('/admin/log/')
@is_admin
def admin_log():
    """ Return the logs as requested by the user. """
    cnt_logs = pkgdblib.search_logs(SESSION, count=True)

    from_date = flask.request.args.get('from_date', None)
    package = flask.request.args.get('package', None)
    refresh = flask.request.args.get('refresh', False)
    limit = flask.request.args.get('limit', APP.config['ITEMS_PER_PAGE'])
    page = flask.request.args.get('page', 1)

    try:
        page = int(page)
    except ValueError:
        page = 1

    try:
        int(limit)
    except ValueError:
        limit = APP.config['ITEMS_PER_PAGE']
        flask.flash('Incorrect limit provided, using default', 'errors')

    if from_date:
        try:
            from_date = parser.parse(from_date)
        except (ValueError, TypeError):
            flask.flash(
                'Incorrect from_date provided, using default', 'errors')
            from_date = None

    ## Could not infer the date() function
    # pylint: disable=E1103
    if from_date:
        from_date = from_date.date()

    logs = []
    try:
        logs = pkgdblib.search_logs(
            SESSION,
            package=package or None,
            from_date=from_date,
            page=page,
            limit=limit,
        )
    except pkgdblib.PkgdbException, err:
        flask.flash(err, 'errors')

    total_page = int(ceil(cnt_logs / float(limit)))

    return flask.render_template(
        'list_logs.html',
        refresh=refresh,
        logs=logs,
        cnt_logs=cnt_logs,
        total_page=total_page,
        page=page,
        package=package or '',
        from_date=from_date or '',
    )
