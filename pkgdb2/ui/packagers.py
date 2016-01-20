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
UI namespace for the Flask application.
'''

import flask
from math import ceil

import pkgdb2.lib as pkgdblib
from pkgdb2 import SESSION, APP
from pkgdb2.ui import UI


@UI.route('/packagers/')
@UI.route('/packagers/<motif>/')
@UI.route('/packagers/<motif>/')
def list_packagers(motif=None):
    ''' Display the list of packagers corresponding to the motif. '''

    pattern = flask.request.args.get('motif', motif) or '*'
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

    packagers = pkgdblib.search_packagers(
        SESSION,
        pattern=pattern,
        page=page,
        limit=limit,
    )

    packagers_count = pkgdblib.search_packagers(
        SESSION,
        pattern=pattern,
        page=page,
        limit=limit,
        count=True,
    )
    total_page = int(ceil(packagers_count / float(limit)))

    packagers = [pkg[0] for pkg in packagers]

    if len(packagers) == 1:
        flask.flash(
            'Only one packager matching, redirecting you to ''his/her page')
        return flask.redirect(flask.url_for(
            '.packager_info', packager=packagers[0]))

    return flask.render_template(
        'list_packagers.html',
        select='packagers',
        packagers=packagers,
        motif=motif,
        total_page=total_page,
        page=page
    )


@UI.route('/packager/<packager>/')
def packager_info(packager):
    ''' Display the information about the specified packager. '''
    eol = flask.request.args.get('eol', False)

    packages_co = pkgdblib.get_package_maintained(
        SESSION,
        packager=packager,
        poc=False,
        eol=eol,
    )

    packages = pkgdblib.get_package_maintained(
        SESSION,
        packager=packager,
        poc=True,
        eol=eol,
    )

    packages_watch = pkgdblib.get_package_watch(
        SESSION,
        packager=packager,
        eol=eol,
    )

    # Filter out from the watch list packaged where user has commit rights
    packages_obj = set([it[0] for it in packages_co])
    packages_obj = packages_obj.union(set([it[0] for it in packages]))
    packages_watch = [
        it for it in packages_watch if it[0] not in packages_obj]

    if not packages and not packages_co and not packages_watch:
        flask.flash('No packager of this name found.', 'errors')
        return flask.render_template('msg.html')

    return flask.render_template(
        'packager.html',
        select='packagers',
        packager=packager,
        packages=packages,
        packages_co=packages_co,
        packages_watch=packages_watch,
    )


@UI.route('/packager/<packager>/requests')
def packager_requests(packager):
    ''' Display the requests made by the specified packager. '''
    action = flask.request.args.get('action') or None
    package = flask.request.args.get('package') or None
    status = flask.request.args.get('status', 'All')
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
            packager=packager,
            package=package,
            action=action,
            status=status,
            page=page,
            limit=limit,
            order='desc',
        )
        cnt_actions = pkgdblib.search_actions(
            SESSION,
            packager=packager,
            package=package,
            action=action,
            status=status,
            page=page,
            limit=limit,
            count=True,
        )
    except pkgdblib.PkgdbException, err:
        flask.flash(err, 'errors')

    total_page = int(ceil(cnt_actions / float(limit)))

    action_status = pkgdblib.get_status(
        SESSION, 'admin_status')['admin_status']
    action_status.insert(0, 'All')

    return flask.render_template(
        'list_actions.html',
        select='packagers',
        actions=actions,
        cnt_actions=cnt_actions,
        total_page=total_page,
        page=page,
        package=package or '',
        packager=packager,
        action=action,
        status=status,
        statuses=action_status,
    )
