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
ACLs management for the Flask application.
'''

import flask
import itertools
from sqlalchemy.orm.exc import NoResultFound

import pkgdb.forms
import pkgdb.lib as pkgdblib
from pkgdb import SESSION, FakeFasUser, APP, fas_login_required
from pkgdb.ui import UI


@UI.route('/acl/<package>/request/', methods=('GET', 'POST'))
@fas_login_required
def request_acl(package):
    ''' Request acls for a specific package. '''

    collections = pkgdb.lib.search_collection(SESSION, '*', 'Active')
    form = pkgdb.forms.RequestAclPackageForm(collections=collections)
    if form.validate_on_submit():
        pkg_branchs = form.pkg_branch.data
        pkg_acls = form.pkg_acl.data

        try:
            for (collec, acl) in itertools.product(pkg_branchs, pkg_acls):
                acl_status = 'Awaiting Review'
                if acl in APP.config['AUTO_APPROVE']:
                    acl_status = 'Approved'
                pkgdblib.set_acl_package(
                    SESSION,
                    pkg_name=package,
                    clt_name=collec,
                    pkg_user=flask.g.fas_user.username,
                    acl=acl,
                    status=acl_status,
                    user=flask.g.fas_user,
                )
            SESSION.commit()
            flask.flash('ACLs updated')
            return flask.redirect(
                flask.url_for('.package_info',
                              package=package))
        except pkgdblib.PkgdbException, err:
            SESSION.rollback()
            flask.flash(err.message, 'error')

    return flask.render_template(
        'acl_request.html',
        form=form,
        package=package,
    )


@UI.route('/acl/<package>/watch/', methods=('GET', 'POST'))
@fas_login_required
def watch_package(package):
    pkg = pkgdblib.search_package(SESSION, pkg_name=package)[0]
    pkg_acls = ['watchcommits', 'watchbugzilla']
    pkg_branchs = [pkglist.collection.branchname for pkglist in pkg.listings]
    try:
        for (collec, acl) in itertools.product(pkg_branchs, pkg_acls):
            pkgdblib.set_acl_package(
                SESSION,
                pkg_name=package,
                clt_name=collec,
                pkg_user=flask.g.fas_user.username,
                acl=acl,
                status='Approved',
                user=flask.g.fas_user,
            )
        SESSION.commit()
        flask.flash('ACLs updated')
        return flask.redirect(
            flask.url_for('.package_info',
                          package=package))
    except pkgdblib.PkgdbException, err:
        SESSION.rollback()
        flask.flash(err.message, 'error')


@UI.route('/acl/<package>/comaintain/', methods=('GET', 'POST'))
@fas_login_required
def comaintain_package(package):
    pkg = pkgdblib.search_package(SESSION, pkg_name=package)[0]
    pkg_acls = ['commit', 'watchcommits', 'watchbugzilla']
    pkg_branchs = [pkglist.collection.branchname for pkglist in pkg.listings]
    try:
        for (collec, acl) in itertools.product(pkg_branchs, pkg_acls):
            acl_status = 'Awaiting Review'
            if acl in APP.config['AUTO_APPROVE']:
                acl_status = 'Approved'
            pkgdblib.set_acl_package(
                SESSION,
                pkg_name=package,
                clt_name=collec,
                pkg_user=flask.g.fas_user,
                acl=acl,
                status=acl_status,
                user=flask.g.fas_user,
            )
        SESSION.commit()
        flask.flash('ACLs updated')
        return flask.redirect(
            flask.url_for('.package_info',
                          package=package))
    except pkgdblib.PkgdbException, err:
        SESSION.rollback()
        flask.flash(err.message, 'error')


@UI.route('/acl/<package>/update/<user>/', methods=('GET', 'POST'))
@UI.route('/acl/<package>/update/<user>/<branch>/', methods=('GET', 'POST'))
@fas_login_required
def update_acl(package, user, branch=None):
    ''' Update the acls for a specific user on a package. '''

    pending_acls = pkgdblib.get_acl_user_package(
        SESSION, user, package, status=None)
    if branch is not None:
        pending_acls2 = []
        for acls in pending_acls:
            if acls['collection'] == branch:
                pending_acls2.append(acls)
        pending_acls = pending_acls2

    collections = set([item['collection'] for item in pending_acls])
    form = pkgdb.forms.UpdateAclPackageForm(collections=collections)
    if form.validate_on_submit():
        pkg_branchs = form.pkg_branch.data
        pkg_acls = form.pkg_acl.data
        acl_status = form.acl_status.data

        try:
            for (collec, acl) in itertools.product(pkg_branchs, pkg_acls):
                if acl_status == 'Awaiting Review' and \
                        acl in APP.config['AUTO_APPROVE']:
                    acl_status = 'Approved'
                pkgdblib.set_acl_package(
                    SESSION,
                    pkg_name=package,
                    clt_name=collec,
                    pkg_user=user,
                    acl=acl,
                    status=acl_status,
                    user=flask.g.fas_user,
                )
            SESSION.commit()
            flask.flash('ACLs updated')
            return flask.redirect(
                flask.url_for('.package_info',
                              package=package))
        except pkgdblib.PkgdbException, err:
            SESSION.rollback()
            flask.flash(err.message, 'error')

    return flask.render_template(
        'acl_update.html',
        form=form,
        package=package,
        user=user,
        branch=branch,
        pending_acls=pending_acls,
    )


@UI.route('/acl/pending/')
@fas_login_required
def pending_acl():
    ''' List the pending acls for the user logged in. '''
    pending_acls = pkgdblib.get_pending_acl_user(
        SESSION, flask.g.fas_user.username)
    return flask.render_template(
        'acl_pending.html',
        pending_acls=pending_acls,
    )
