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
        page = int(page)
    except ValueError:
        page = 1

    try:
        int(limit)
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

    return flask.render_template(
        'list_packagers.html',
        packagers=[pkg[0] for pkg in packagers],
        motif=motif,
        total_page=total_page,
        page=page
    )


@UI.route('/packager/<packager>/')
def packager_info(packager):
    ''' Display the information about the specified packager. '''

    packages_co = pkgdblib.get_package_maintained(
        SESSION,
        packager=packager,
        poc=False,
    )

    packages = pkgdblib.get_package_maintained(
        SESSION,
        packager=packager,
        poc=True,
    )

    if not packages and not packages_co:
        flask.flash('No packager of this name found.', 'errors')
        return flask.render_template('msg.html')

    return flask.render_template(
        'packager.html',
        packager=packager,
        packages=packages,
        packages_co=packages_co,
    )
