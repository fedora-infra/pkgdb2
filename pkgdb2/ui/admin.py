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

import pkgdb2.forms
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
    from_date = flask.request.args.get('from_date', None)
    package = flask.request.args.get('package', None)
    packager = flask.request.args.get('packager', None)
    refresh = flask.request.args.get('refresh', False)
    limit = flask.request.args.get('limit', APP.config['ITEMS_PER_PAGE'])
    page = flask.request.args.get('page', 1)

    try:
        page = abs(int(page))
    except ValueError:
        page = 1

    try:
        limit = abs(int(limit))
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
    cnt_logs = 0
    try:
        logs = pkgdblib.search_logs(
            SESSION,
            package=package or None,
            packager=packager or None,
            from_date=from_date,
            page=page,
            limit=limit,
        )
        cnt_logs = pkgdblib.search_logs(
            SESSION,
            package=package or None,
            packager=packager or None,
            from_date=from_date,
            count=True
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
        packager=packager or '',
    )


@UI.route('/admin/actions/')
@is_admin
def admin_actions():
    """ Return the actions requested and requiring intervention from an
    admin.
    """
    package = flask.request.args.get('package', None)
    packager = flask.request.args.get('packager', None)
    action = flask.request.args.get('action', None)
    status = flask.request.args.get('status', 'Awaiting Review')
    limit = flask.request.args.get('limit', APP.config['ITEMS_PER_PAGE'])
    page = flask.request.args.get('page', 1)

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
            page=page,
            limit=limit,
        )
        cnt_actions = pkgdblib.search_actions(
            SESSION,
            package=package or None,
            packager=packager or None,
            action=action,
            status=status,
            count=True
        )
    except pkgdblib.PkgdbException, err:
        flask.flash(err, 'errors')

    total_page = int(ceil(cnt_actions / float(limit)))

    return flask.render_template(
        'list_actions.html',
        actions=actions,
        cnt_actions=cnt_actions,
        total_page=total_page,
        page=page,
        package=package or '',
        packager=packager or '',
        action=action,
        status=status,
    )


@UI.route('/admin/action/<action_id>/status', methods=['GET', 'POST'])
@is_admin
def admin_action_edit_status(action_id):
    """ Edit Admin Action status update
    """

    admin_action = pkgdblib.get_admin_action(SESSION, action_id)
    if not admin_action:
        flask.flash('No action found with this identifier.', 'errors')
        return flask.render_template('msg.html')

    action_status = pkgdblib.get_status(SESSION, 'acl_status')['acl_status']

    form = pkgdb2.forms.EditActionStatusForm(
        status=action_status,
        obj=admin_action
    )
    form.id.data = action_id

    if form.validate_on_submit():

        try:
            message = pkgdblib.edit_action_status(
                SESSION,
                admin_action,
                action_status=form.status.data,
                user=flask.g.fas_user
            )
            SESSION.commit()
            flask.flash(message)
        except pkgdblib.PkgdbException, err:  # pragma: no cover
            # We can only reach here in two cases:
            # 1) the user is not an admin, but that's taken care of
            #    by the decorator
            # 2) we have a SQLAlchemy problem when storing the info
            #    in the DB which we cannot test
            SESSION.rollback()
            flask.flash(err, 'errors')
            return flask.render_template('msg.html')

        return flask.redirect(
            flask.url_for('.admin_actions')
        )

    return flask.render_template(
        'actions_update.html',
        admin_action=admin_action,
        action_id=action_id,
        form=form,
    )
