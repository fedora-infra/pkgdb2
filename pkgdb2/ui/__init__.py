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

from urlparse import urlparse

import pkgdb2.lib as pkgdblib
from pkgdb2 import SESSION, FAS, is_pkgdb_admin, __version__


UI = flask.Blueprint('ui_ns', __name__, url_prefix='')


@UI.context_processor
def inject_is_admin():
    """ Inject whether the user is a nuancier admin or not in every page
    (every template).
    """
    return dict(is_admin=is_pkgdb_admin(flask.g.fas_user),
                version=__version__)


@UI.route('/')
def index():
    ''' Display the index package DB page. '''
    return flask.render_template('index.html')


@UI.route('/stats/')
def stats():
    ''' Display some statistics aboue the packages in the DB. '''
    collections = pkgdblib.search_collection(SESSION, '*', 'Active')
    collections.extend(pkgdblib.search_collection(
        SESSION, '*', 'Under Development'))

    collections = pkgdblib.count_collection(SESSION)
    collections_fedora = pkgdblib.count_fedora_collection(SESSION)

    cnt = 1
    collections_fedora_lbl = []
    collections_fedora_data = []
    for item in collections_fedora:
        collections_fedora_lbl.append([cnt, str(item[0])])
        collections_fedora_data.append([cnt, float(item[1])])
        cnt += 1

    # Top maintainers
    top_maintainers = pkgdblib.get_top_maintainers(SESSION)
    # Top point of contact
    top_poc = pkgdblib.get_top_poc(SESSION)

    return flask.render_template(
        'stats.html',
        collections=collections,
        collections_fedora_lbl=collections_fedora_lbl,
        collections_fedora_data=collections_fedora_data,
        top_maintainers=top_maintainers,
        top_poc=top_poc,
    )


@UI.route('/search/')
def search():
    ''' Redirect to the correct url to perform the appropriate search.
    '''
    search_type = flask.request.args.get('type', 'package')
    search_term = flask.request.args.get('term', 'a*') or 'a*'

    if not search_term.endswith('*'):
        search_term += '*'

    if search_type == 'packager':
        return flask.redirect(flask.url_for('.list_packagers',
                                            motif=search_term))
    if search_type == 'orphaned':
        return flask.redirect(flask.url_for('.list_orphaned',
                                            motif=search_term))
    if search_type == 'retired':
        return flask.redirect(flask.url_for('.list_retired',
                                            motif=search_term))
    else:
        return flask.redirect(flask.url_for('.list_packages',
                                            motif=search_term))


@UI.route('/msg/')
def msg():
    """ Page used to display error messages
    """
    return flask.render_template('msg.html')


@UI.route('/login/', methods=['GET', 'POST'])
def login():  # pragma: no cover
    """ Login mechanism for this application.
    """
    next_url = flask.url_for('ui_ns.index')
    if 'next' in flask.request.args:
        next_url = flask.request.args['next']
    elif 'next' in flask.request.form:
        next_url = flask.request.form['next']

    if next_url == flask.url_for('ui_ns.login'):
        next_url = flask.url_for('ui_ns.index')

    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        return flask.redirect(next_url)
    else:
        return FAS.login(return_url=next_url)


@UI.route('/logout/')
def logout():
    """ Log out if the user is logged in other do nothing.
    Return to the index page at the end.
    """
    next_url = flask.url_for('ui_ns.index')
    if 'next' in flask.request.args:  # pragma: no cover
        next_url = flask.request.args['next']
    elif 'next' in flask.request.form:  # pragma: no cover
        next_url = flask.request.form['next']

    if next_url == flask.url_for('ui_ns.login'):  # pragma: no cover
        next_url = flask.url_for('ui_ns.index')
    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        FAS.logout()
        flask.flash("You are no longer logged-in")
    return flask.redirect(next_url)
