# -*- coding: utf-8 -*-
#
# Copyright © 2013-2014  Red Hat, Inc.
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

import pkgdb2.lib as pkgdblib
from pkgdb2 import (APP, SESSION, FAS, is_pkgdb_admin, __version__,
                    is_safe_url, is_authenticated)


UI = flask.Blueprint('ui_ns', __name__, url_prefix='')


@APP.template_filter('sort_branches')
def branches_filter(branches):
    """ Template filter sorting the given branches, Fedora first then EPEL,
    then whatever is left.
    """
    data = {}
    for branch in branches:
        key = branch.rsplit(' ', 1)[0]
        if key not in data:
            data[key] = []
        data[key].append(branch)

    output = []
    kkeys = ['Fedora', 'Fedora EPEL']
    for key in kkeys:
        if key in data:
            output.extend(sorted(data[key], reverse=True))
    for key in data:
        if key not in kkeys:
            output.extend(sorted(data[key], reverse=True))
    return output


@APP.template_filter('avatar')
def avatar(packager, size=64):
    """ Template filter to produce the libravatar of a given packager. """
    if is_authenticated() and packager == flask.g.fas_user.username:
        openid_template = 'http://{packager}.id.fedoraproject.org/'
        openid = openid_template.format(packager=packager)
        avatar = pkgdblib.utils.avatar_url(packager, size)
        return """<form method="POST" action="https://www.libravatar.org/openid/login/">
            <input type="hidden" name="openid_identifier" value="{openid}"/>
            <input type="image" class="avatar circle" src="{avatar}" style="outline: none;"
            title="Update your avatar"/>
        </form>""".format(openid=openid, avatar=avatar)
    else:
        return '<img class="avatar circle" src="%s"/>' % (
            pkgdblib.utils.avatar_url(packager, size)
        )


@UI.context_processor
def inject_is_admin():
    """ Inject whether the user is a pkgdb2 admin or not in every page
    (every template).
    """
    justlogedin = flask.session.get('_justloggedin', False)
    if justlogedin:  # pragma: no cover
        flask.g.pending_acls = pkgdblib.get_pending_acl_user(
            SESSION, flask.g.fas_user.username)
        flask.session['_justloggedin'] = None

    justlogedout = flask.session.get('_justloggedout', False)
    if justlogedout:
        flask.session['_justloggedout'] = None

    return dict(is_admin=is_pkgdb_admin(flask.g.fas_user),
                version=__version__)


@UI.context_processor
def inject_fedmenu():
    """ Inject fedmenu url if available. """
    if 'FEDMENU_URL' in APP.config:
        return dict(
            fedmenu_url=APP.config['FEDMENU_URL'],
            fedmenu_data_url=APP.config['FEDMENU_DATA_URL'],
        )
    return dict()


@UI.route('/')
def index():
    ''' Display the index package DB page. '''
    packages = pkgdblib.get_latest_package(SESSION, 10)
    return flask.render_template('index.html', latest_pkgs=packages)


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
    search_term = flask.request.args.get('term', '*') or '*'

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


@UI.route('/opensearch/<xmlfile>')
def opensearch(xmlfile):
    ''' Offers an opensearch provider.
    '''
    if xmlfile == 'pkgdb_packages.xml':
        xml = flask.render_template(
            'opensearch.html',
            shortname='packages',
            example='kernel'
        )
        return flask.Response(xml, mimetype='text/xml')

    if xmlfile == 'pkgdb_packager.xml':
        xml = flask.render_template(
            'opensearch.html',
            shortname='packager',
            example='spot'
        )
        return flask.Response(xml, mimetype='text/xml')

    return flask.redirect(flask.url_for('.index'))


@UI.route('/msg/')
def msg():
    """ Page used to display error messages
    """
    return flask.render_template('msg.html')


@FAS.postlogin
def check_pending_acls(return_url):  # pragma: no cover
    """ After login check if the user has ACLs awaiting review. """
    flask.session['_justloggedin'] = True
    return flask.redirect(return_url)


@UI.route('/login/', methods=['GET', 'POST'])
def login():  # pragma: no cover
    """ Login mechanism for this application.
    """
    next_url = flask.url_for('ui_ns.index')
    if 'next' in flask.request.values:
        if is_safe_url(flask.request.values['next']):
            next_url = flask.request.values['next']

    if next_url == flask.url_for('ui_ns.login'):
        next_url = flask.url_for('ui_ns.index')

    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        return flask.redirect(next_url)
    else:
        groups = pkgdblib.get_groups(SESSION)
        groups.extend(APP.config['ADMIN_GROUP'])
        groups.append('packager')
        return FAS.login(return_url=next_url, groups=groups)


@UI.route('/logout/')
def logout():
    """ Log out if the user is logged in other do nothing.
    Return to the index page at the end.
    """
    next_url = flask.url_for('ui_ns.index')
    if 'next' in flask.request.values:  # pragma: no cover
        next_url = flask.request.values['next']

    if next_url == flask.url_for('ui_ns.login'):  # pragma: no cover
        next_url = flask.url_for('ui_ns.index')
    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        FAS.logout()
        flask.flash("You are no longer logged-in")
    flask.session['_justloggedout'] = True
    return flask.redirect(next_url)
