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
from sqlalchemy.orm.exc import NoResultFound

import pkgdb.forms
import pkgdb.lib as pkgdblib
from pkgdb import SESSION, FakeFasUser
from pkgdb.ui import UI


@UI.route('/packages/')
@UI.route('/packages/<motif>/')
def list_packages(motif=None):
    ''' Display the list of packages corresponding to the motif. '''

    pattern = flask.request.args.get('motif', motif) or '*'
    branches = flask.request.args.get('branches', None)
    owner = flask.request.args.get('owner', None)
    orphaned = bool(flask.request.args.get('orphaned', False))
    deprecated = bool(flask.request.args.get('deprecated', False))

    packages = pkgdblib.search_package(SESSION,
                                       pkg_name=pattern,
                                       clt_name=branches,
                                       pkg_owner=owner,
                                       orphaned=orphaned,
                                       deprecated=deprecated,
                                       )

    return flask.render_template(
        'list_packages.html',
        packages=packages,
    )


@UI.route('/package/<packagename>/')
def package_info(packagename):
    ''' Display the information about the specified package. '''

    package = []
    try:
        package_acl = pkgdblib.get_acl_package(SESSION, packagename)
        package = pkgdblib.search_package(SESSION, packagename)[0]
    except NoResultFound:
        SESSION.rollback()

    return flask.render_template(
        'package.html',
        package=package,
        package_acl=package_acl,
    )


## TODO: Restricted to admin
@UI.route('/new/package/', methods=('GET', 'POST'))
def package_new():
    ''' Page to create a new package. '''

    collections = pkgdb.lib.search_collection(SESSION, '*', 'Active')

    form = pkgdb.forms.AddPackageForm(collections=collections)
    if form.validate_on_submit():
        pkg_name = form.pkg_name.data
        pkg_summary = form.pkg_summary.data
        pkg_reviewURL = form.pkg_reviewURL.data
        pkg_status = form.pkg_status.data
        pkg_shouldopen = form.pkg_shouldopen.data
        pkg_collection = form.pkg_collection.data
        pkg_owner = form.pkg_owner.data
        pkg_upstreamURL = form.pkg_upstreamURL.data

        try:
            message = pkgdblib.add_package(
                SESSION,
                pkg_name=pkg_name,
                pkg_summary=pkg_summary,
                pkg_reviewURL=pkg_reviewURL,
                pkg_status=pkg_status,
                pkg_shouldopen=pkg_shouldopen,
                pkg_collection=','.join(pkg_collection),
                pkg_owner=pkg_owner,
                pkg_upstreamURL=pkg_upstreamURL,
                user=FakeFasUser(),
                #user=flask.g.fas_user,
            )
            SESSION.commit()
            flask.flash(message)
            return flask.redirect(flask.url_for('.list_packages'))
        except pkgdblib.PkgdbException, err:
            SESSION.rollback()
            flask.flash(err.message, 'error')

    return flask.render_template(
        'package_new.html',
        form=form,
    )
