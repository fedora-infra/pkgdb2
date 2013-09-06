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
from sqlalchemy.orm.exc import NoResultFound

import pkgdb.forms
import pkgdb.lib as pkgdblib
from pkgdb import SESSION, FakeFasUser, APP, is_admin, is_pkgdb_admin, \
    is_pkg_admin, fas_login_required
from pkgdb.ui import UI


@UI.route('/packages/')
@UI.route('/packages/<motif>/')
def list_packages(motif=None):
    ''' Display the list of packages corresponding to the motif. '''

    pattern = flask.request.args.get('motif', motif) or '*'
    branches = flask.request.args.get('branches', None)
    owner = flask.request.args.get('owner', None)
    orphaned = bool(flask.request.args.get('orphaned', False))
    status = flask.request.args.get('status', None)
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


    packages = pkgdblib.search_package(
        SESSION,
        pkg_name=pattern,
        clt_name=branches,
        pkg_poc=owner,
        orphaned=orphaned,
        status=status,
        page=page,
        limit=limit,
    )
    packages_count = pkgdblib.search_package(
        SESSION,
        pkg_name=pattern,
        clt_name=branches,
        pkg_poc=owner,
        orphaned=orphaned,
        status=status,
        page=page,
        limit=limit,
        count=True
    )
    total_page = int(ceil(packages_count / float(limit)))

    return flask.render_template(
        'list_packages.html',
        packages=packages,
        motif=motif,
        total_page=total_page,
        page=page,
        admin=is_pkgdb_admin(flask.g.fas_user),
    )


@UI.route('/package/<package>/')
def package_info(package):
    ''' Display the information about the specified package. '''

    packagename = package
    package = []
    try:
        package_acl = pkgdblib.get_acl_package(SESSION, packagename)
        package = pkgdblib.search_package(SESSION, packagename)[0]
    except NoResultFound:
        SESSION.rollback()
        flask.flash('No package of this name found.', 'errors')
        return flask.render_template('error.html')
    except IndexError:
        flask.flash('No package of this name found.', 'errors')
        return flask.render_template('error.html')

    package_acls = []
    branch_admin = []
    for pkg in package_acl:
        tmp = {}
        tmp['collection'] = '%s %s' %(pkg.collection.name,
                                      pkg.collection.version)
        tmp['branchname'] = pkg.collection.branchname
        tmp['point_of_contact'] = pkg.point_of_contact
        acls = {}
        for acl in pkg.acls:
            tmp2 = {'acl': acl.acl, 'status': acl.status}
            if acl.fas_name in acls:
                acls[acl.fas_name].append(tmp2)
            else:
                acls[acl.fas_name] = [tmp2]
        ## This list is a little hacky, but we would have to save ACLs
        ## in their own table otherwise.
        planned_acls = set(['approveacls', 'commit', 'watchbugzilla',
                            'watchcommits'])
        seen_acls = set([aclobj['acl'] for aclobj in acls[acl.fas_name]])
        for aclname in planned_acls - seen_acls:
            acls[acl.fas_name].append({'acl': aclname, 'status': ''})
        tmp['acls'] = acls
        package_acls.append(tmp)
        if is_pkg_admin(flask.g.fas_user, package.name,
                pkg.collection.branchname):
            branch_admin.append(pkg.collection.branchname)

    return flask.render_template(
        'package.html',
        package=package,
        package_acl=package_acls,
        branch_admin=branch_admin,
    )


@UI.route('/new/package/', methods=('GET', 'POST'))
@is_admin
def package_new():
    ''' Page to create a new package. '''

    collections = pkgdblib.search_collection(SESSION, '*', 'Active')
    collections.extend(pkgdblib.search_collection(
        SESSION, '*', 'Under Development'))

    form = pkgdb.forms.AddPackageForm(collections=collections)
    if form.validate_on_submit():
        pkg_name = form.pkg_name.data
        pkg_summary = form.pkg_summary.data
        pkg_reviewURL = form.pkg_reviewURL.data
        pkg_status = form.pkg_status.data
        pkg_shouldopen = form.pkg_shouldopen.data
        pkg_collection = form.pkg_collection.data
        pkg_poc = form.pkg_poc.data
        pkg_upstreamURL = form.pkg_upstreamURL.data

        try:
            message = pkgdblib.add_package(
                SESSION,
                pkg_name=pkg_name,
                pkg_summary=pkg_summary,
                pkg_reviewURL=pkg_reviewURL,
                pkg_status=pkg_status,
                pkg_shouldopen=pkg_shouldopen,
                pkg_collection=pkg_collection,
                pkg_poc=pkg_poc,
                pkg_upstreamURL=pkg_upstreamURL,
                user=flask.g.fas_user,
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
