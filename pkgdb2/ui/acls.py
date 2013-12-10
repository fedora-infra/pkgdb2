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

import pkgdb2.forms
import pkgdb2.lib as pkgdblib
from pkgdb2 import (SESSION, APP, fas_login_required,
                    packager_login_required)
from pkgdb2.ui import UI


@UI.route('/acl/<package>/request/', methods=('GET', 'POST'))
@fas_login_required
def request_acl(package):
    ''' Request acls for a specific package. '''

    collections = pkgdblib.search_collection(
        SESSION, '*', 'Under Development')
    collections.extend(pkgdblib.search_collection(SESSION, '*', 'Active'))
    pkg_acl = pkgdblib.get_status(SESSION, 'pkg_acl')['pkg_acl']

    form = pkgdb2.forms.RequestAclPackageForm(
        collections=collections,
        pkg_acl_list=pkg_acl
    )
    if form.validate_on_submit():
        pkg_branchs = form.pkg_branch.data
        pkg_acls = form.pkg_acl.data

        try:
            for (collec, acl) in itertools.product(pkg_branchs, pkg_acls):
                acl_status = 'Awaiting Review'
                if acl in APP.config['AUTO_APPROVE']:
                    acl_status = 'Approved'
                elif 'packager' not in flask.g.fas_user.groups:
                    flask.flash(
                        'You must be a packager to apply to the'
                        ' ACL: %s on %s' % (acl, collec), 'errors')
                    continue

                pkgdblib.set_acl_package(
                    SESSION,
                    pkg_name=package,
                    pkg_branch=collec,
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
    ''' Request watch* ACLs on a package.
    Anyone can request these ACLs, no need to be a packager.
    '''
    try:
        pkg = pkgdblib.search_package(SESSION, pkg_name=package, limit=1)[0]
    except IndexError:
        flask.flash('No package found by this name', 'error')
        return flask.redirect(
            flask.url_for('.package_info', package=package))

    pkg_acls = ['watchcommits', 'watchbugzilla']
    pkg_branchs = [pkglist.collection.branchname for pkglist in pkg.listings]
    try:
        for (collec, acl) in itertools.product(pkg_branchs, pkg_acls):
            pkgdblib.set_acl_package(
                SESSION,
                pkg_name=package,
                pkg_branch=collec,
                pkg_user=flask.g.fas_user.username,
                acl=acl,
                status='Approved',
                user=flask.g.fas_user,
            )
        SESSION.commit()
        flask.flash('ACLs updated')
    # Let's keep this in although we should never see it
    except pkgdblib.PkgdbException, err:  # pragma: no cover
        SESSION.rollback()
        flask.flash(err.message, 'error')
    return flask.redirect(flask.url_for('.package_info', package=package))


@UI.route('/acl/<package>/comaintain/', methods=('GET', 'POST'))
@packager_login_required
def comaintain_package(package):
    ''' Asks for ACLs to co-maintain a package.
    You need to be a packager to request co-maintainership.
    '''
    # This is really wearing belt and suspenders, the decorator above
    # should take care of this
    if not 'packager' in flask.g.fas_user.groups:  # pragma: no cover
        flask.flash(
            'You must be a packager to apply to be a comaintainer',
            'errors')
        return flask.redirect(flask.url_for(
            '.package_info', package=package))

    try:
        pkg = pkgdblib.search_package(SESSION, pkg_name=package, limit=1)[0]
    except IndexError:
        flask.flash('No package found by this name', 'error')
        return flask.redirect(
            flask.url_for('.package_info', package=package))

    pkg_acls = ['commit', 'watchcommits', 'watchbugzilla']
    pkg_branchs = [pkglist.collection.branchname for pkglist in pkg.listings]

    # Make sure the requester does not already have commit
    pkg_branchs2 = []
    for pkg_branch in pkg_branchs:
        if pkgdblib.has_acls(SESSION, flask.g.fas_user.username, pkg.name,
                             pkg_branch, 'commit'):
            flask.flash(
                'You are already a co-maintainer on %s' % pkg_branch,
                'error')
        else:
            pkg_branchs2.append(pkg_branch)
    pkg_branchs = pkg_branchs2

    if not pkg_branchs:
        return flask.redirect(flask.url_for('.package_info', package=package))

    try:
        for (collec, acl) in itertools.product(pkg_branchs, pkg_acls):
            acl_status = 'Awaiting Review'
            if acl in APP.config['AUTO_APPROVE']:
                acl_status = 'Approved'
            pkgdblib.set_acl_package(
                SESSION,
                pkg_name=package,
                pkg_branch=collec,
                pkg_user=flask.g.fas_user.username,
                acl=acl,
                status=acl_status,
                user=flask.g.fas_user,
            )
        SESSION.commit()
        flask.flash('ACLs updated')
    # Let's keep this in although we should never see it
    except pkgdblib.PkgdbException, err:  # pragma: no cover
        SESSION.rollback()
        flask.flash(err.message, 'error')
    return flask.redirect(flask.url_for('.package_info', package=package))


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
    status = pkgdblib.get_status(SESSION, ['pkg_acl', 'acl_status'])

    form = pkgdb2.forms.UpdateAclPackageForm(
        collections=collections,
        pkg_acl_list=status['pkg_acl'],
        acl_status=status['acl_status'],
    )

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
                    pkg_branch=collec,
                    pkg_user=user,
                    acl=acl,
                    status=acl_status,
                    user=flask.g.fas_user,
                )
                flask.flash('ACLs updated')
            SESSION.commit()
            return flask.redirect(
                flask.url_for('.package_info',
                              package=package))
        # Let's keep this in although we should never see it
        except pkgdblib.PkgdbException, err:  # pragma: no cover
            SESSION.rollback()
            flask.flash(err.message, 'errors')

    return flask.render_template(
        'acl_update.html',
        form=form,
        package=package,
        user=user,
        branch=branch,
        pending_acls=pending_acls,
    )


@UI.route('/acl/pending/')
@packager_login_required
def pending_acl():
    ''' List the pending acls for the user logged in. '''
    pending_acls = pkgdblib.get_pending_acl_user(
        SESSION, flask.g.fas_user.username)
    return flask.render_template(
        'acl_pending.html',
        pending_acls=pending_acls,
    )
