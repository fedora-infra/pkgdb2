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

import pkgdb.lib as pkgdblib
from pkgdb import SESSION, FAS


UI = flask.Blueprint('ui_ns', __name__, url_prefix='')


@UI.route('/')
def index():
    ''' Display the index package DB page. '''
    return flask.render_template('index.html')


@UI.route('/stats/')
def stats():
    ''' Display some statistics aboue the packages in the DB. '''
    collections = pkgdblib.search_collection(SESSION, '*', 'Active')

    packages = {}
    for collection in collections:
        packages_count = pkgdblib.search_package(
            SESSION,
            pkg_name='*',
            clt_name=collection.branchname,
            count=True
        )
        packages[collection.branchname] = packages_count

    return flask.render_template('stats.html', packages=packages)


@UI.route('/search/')
def search():
    ''' Redirect to the correct url to perform the appropriate search.
    '''
    search_type = flask.request.args.get('type', 'package')
    search_term = flask.request.args.get('term', 'a*') or None

    if not search_term.endswith('*'):
        search_term += '*'

    if search_type == 'packager':
        return flask.redirect(flask.url_for('.list_packagers',
                                            motif=search_term))
    else:
        return flask.redirect(flask.url_for('.list_packages',
                                            motif=search_term))


@UI.route('/error/')
def error():
    """ Page used to display error messages
    """
    return flask.render_template('error.html')


@UI.route('/login/', methods=['GET', 'POST'])
def login():
    """ Login mechanism for this application.
    """
    next_url = None
    if 'next' in flask.request.args:
        next_url = flask.request.args['next']

    if not next_url or next_url == flask.url_for('.login'):
        next_url = flask.url_for('.index')

    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        return flask.redirect(next_url)
    else:
        return FAS.login(return_url=next_url)


@UI.route('/logout/')
def logout():
    """ Log out if the user is logged in other do nothing.
    Return to the index page at the end.
    """
    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        FAS.logout()
    return flask.redirect(flask.url_for('.index'))
