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
from math import ceil
from sqlalchemy.orm.exc import NoResultFound

import pkgdb2.forms
import pkgdb2.lib as pkgdblib
from pkgdb2 import SESSION, APP, is_admin, is_pkgdb_admin, \
    packager_login_required
from pkgdb2.ui import UI


## Some of the object we use here have inherited methods which apparently
## pylint does not detect.
# pylint: disable=E1101

@UI.route('/packages/')
@UI.route('/packages/<motif>/')
def list_packages(motif=None, orphaned=False, status=None,
                  origin='list_packages', case_sensitive=False):
    ''' Display the list of packages corresponding to the motif. '''

    pattern = flask.request.args.get('motif', motif) or '*'
    branches = flask.request.args.get('branches', None)
    owner = flask.request.args.get('owner', None)
    orphaned = bool(flask.request.args.get('orphaned', orphaned))
    status = flask.request.args.get('status', status)
    limit = flask.request.args.get('limit', APP.config['ITEMS_PER_PAGE'])
    page = flask.request.args.get('page', 1)
    case_sensitive = flask.request.args.get('case_sensitive', False)

    try:
        page = abs(int(page))
    except ValueError:
        page = 1

    try:
        limit = abs(int(limit))
    except ValueError:
        limit = APP.config['ITEMS_PER_PAGE']
        flask.flash('Incorrect limit provided, using default', 'errors')

    packages = pkgdblib.search_package(
        SESSION,
        pkg_name=pattern,
        pkg_branch=branches,
        pkg_poc=owner,
        orphaned=orphaned,
        status=status,
        page=page,
        limit=limit,
        case_sensitive=case_sensitive,
    )
    packages_count = pkgdblib.search_package(
        SESSION,
        pkg_name=pattern,
        pkg_branch=branches,
        pkg_poc=owner,
        orphaned=orphaned,
        status=status,
        page=page,
        limit=limit,
        count=True,
        case_sensitive=case_sensitive,
    )
    total_page = int(ceil(packages_count / float(limit)))

    select = origin.replace('list_', '')

    return flask.render_template(
        'list_packages.html',
        origin=origin,
        select=select,
        packages=packages,
        motif=motif,
        total_page=total_page,
        packages_count=packages_count,
        page=page,
        status=status,
    )


@UI.route('/orphaned/')
@UI.route('/orphaned/<motif>/')
def list_orphaned(motif=None):
    ''' Display the list of orphaned packages corresponding to the motif.'''
    return list_packages(motif=motif, orphaned=True, status='Orphaned',
                         origin='list_orphaned')


@UI.route('/retired/')
@UI.route('/retired/<motif>/')
def list_retired(motif=None):
    ''' Display the list of retired packages corresponding to the motif.'''
    return list_packages(motif=motif, status='Retired', origin='list_retired')


@UI.route('/acls/name/<package>')
@UI.route('/acls/name/<package>/')
def old_package(package):
    return flask.redirect(flask.url_for('package_info', package=package))


## Too many branches
# pylint: disable=R0912
## Too many variables
# pylint: disable=R0914
## Too many statements
# pylint: disable=R0915
@UI.route('/package/<package>/')
def package_info(package):
    ''' Display the information about the specified package. '''

    packagename = package
    package = None
    try:
        package_acl = pkgdblib.get_acl_package(SESSION, packagename)
        package = pkgdblib.search_package(SESSION, packagename, limit=1)[0]
    except (NoResultFound, IndexError):
        SESSION.rollback()
        flask.flash('No package of this name found.', 'errors')
        return flask.render_template('msg.html')

    planned_acls = set(
        pkgdblib.get_status(SESSION, 'pkg_acl')['pkg_acl'])

    branches = set()
    commit_acls = {}
    watch_acls = {}
    admins = {}
    pending_admins = {}
    pocs = {}
    committers = []

    for pkg in package_acl:
        if pkg.collection.status == 'EOL':  # pragma: no cover
            continue

        collection_name = '%s %s' % (
            pkg.collection.name, pkg.collection.version)

        branches.add(collection_name)

        if pkg.point_of_contact not in pocs:
            pocs[pkg.point_of_contact] = set()
        pocs[pkg.point_of_contact].add(collection_name)

        for acl in pkg.acls:

            if acl.acl == 'approveacls' and acl.status == 'Approved':
                if acl.fas_name not in admins:
                    admins[acl.fas_name] = set()
                admins[acl.fas_name].add(collection_name)
            elif acl.acl == 'approveacls' and acl.status == 'Awaiting Review':
                if acl.fas_name not in pending_admins:
                    pending_admins[acl.fas_name] = set()
                pending_admins[acl.fas_name].add(collection_name)

            if acl.acl == 'commit':
                dic = commit_acls
                if acl.status == 'Approved':
                    committers.append(acl.fas_name)
            elif acl.acl.startswith('watch') and acl.status == 'Approved':
                dic = watch_acls
            else:
                continue

            if acl.fas_name not in dic:
                dic[acl.fas_name] = {}
            if collection_name not in dic[acl.fas_name]:
                dic[acl.fas_name][collection_name] = {}

            dic[acl.fas_name][collection_name][acl.acl] = \
                acl.status

        for aclname in planned_acls:
            for user in commit_acls:
                if collection_name in commit_acls[user] and \
                        aclname not in commit_acls[user][collection_name]:
                    commit_acls[user][collection_name][aclname] = None

        for aclname in planned_acls:
            for user in watch_acls:
                if collection_name in watch_acls[user] and \
                        aclname not in watch_acls[user][collection_name]:
                    watch_acls[user][collection_name][aclname] = None

    return flask.render_template(
        'package.html',
        package=package,
        commit_acls=commit_acls,
        watch_acls=watch_acls,
        pocs=pocs,
        admins=admins,
        pending_admins=pending_admins,
        branches=branches,
        committers=committers,
        form=pkgdb2.forms.ConfirmationForm(),
    )


@UI.route('/new/package/', methods=('GET', 'POST'))
@is_admin
def package_new():
    ''' Page to create a new package. '''

    collections = pkgdb2.lib.search_collection(
        SESSION, '*', 'Under Development')
    collections.extend(pkgdb2.lib.search_collection(SESSION, '*', 'Active'))
    pkg_status = pkgdb2.lib.get_status(SESSION, 'pkg_status')['pkg_status']

    form = pkgdb2.forms.AddPackageForm(
        collections=collections,
        pkg_status_list=pkg_status,
    )
    if form.validate_on_submit():
        pkg_name = form.pkgname.data
        pkg_summary = form.summary.data
        pkg_description = form.description.data
        pkg_review_url = form.review_url.data
        pkg_status = form.status.data
        pkg_critpath = form.critpath.data
        pkg_collection = form.branches.data
        pkg_poc = form.poc.data
        pkg_upstream_url = form.upstream_url.data

        try:
            message = pkgdblib.add_package(
                SESSION,
                pkg_name=pkg_name,
                pkg_summary=pkg_summary,
                pkg_description=pkg_description,
                pkg_review_url=pkg_review_url,
                pkg_status=pkg_status,
                pkg_critpath=pkg_critpath,
                pkg_collection=pkg_collection,
                pkg_poc=pkg_poc,
                pkg_upstream_url=pkg_upstream_url,
                user=flask.g.fas_user,
            )
            SESSION.commit()
            flask.flash(message)
            return flask.redirect(flask.url_for('.list_packages'))
        # Keep it in, but normally we shouldn't hit this
        except pkgdblib.PkgdbException, err:  # pragma: no cover
            SESSION.rollback()
            flask.flash(str(err), 'error')

    return flask.render_template(
        'package_new.html',
        form=form,
    )


@UI.route('/package/<package>/give', methods=('GET', 'POST'))
@UI.route('/package/<package>/give/<full>', methods=('GET', 'POST'))
@packager_login_required
def package_give(package, full=True):
    ''' Gives the PoC of a package to someone else. '''

    if not bool(full) or full in ['0', 'False']:
        full = False

    packagename = package
    package = None
    try:
        package_acl = pkgdblib.get_acl_package(SESSION, packagename)
        package = pkgdblib.search_package(SESSION, packagename, limit=1)[0]
    except (NoResultFound, IndexError):
        SESSION.rollback()
        flask.flash('No package of this name found.', 'errors')
        return flask.render_template('msg.html')

    # Restrict the branch to the one current user is PoC of (unless admin
    # or group)
    collect_name = []
    for acl in package_acl:
        if acl.point_of_contact != flask.g.fas_user.username and \
                not is_pkgdb_admin(flask.g.fas_user) and \
                not acl.point_of_contact.startswith('group::'):
            pass
        else:
            if acl.point_of_contact.startswith('group::'):
                group = acl.point_of_contact.split('group::')[0]
                if group not in flask.g.fas_user.groups:
                    pass
            elif acl.collection.status != 'EOL':
                collect_name.append(acl.collection.branchname)

    form = pkgdb2.forms.GivePoCForm(collections=collect_name)

    acls = ['commit', 'watchbugzilla', 'watchcommits', 'approveacls']

    if form.validate_on_submit():
        collections = form.branches.data
        pkg_poc = form.poc.data
        if pkg_poc.startswith('group::'):
            acls = ['commit', 'watchbugzilla', 'watchcommits']

        try:
            for pkg_collection in collections:
                message = pkgdblib.update_pkg_poc(
                    SESSION,
                    pkg_name=packagename,
                    pkg_branch=pkg_collection,
                    pkg_poc=pkg_poc,
                    user=flask.g.fas_user,
                )
                flask.flash(message)

                for acl in acls:
                    pkgdblib.set_acl_package(
                        SESSION,
                        pkg_name=packagename,
                        pkg_branch=pkg_collection,
                        pkg_user=pkg_poc,
                        acl=acl,
                        status='Approved',
                        user=flask.g.fas_user
                    )

                SESSION.commit()
        except pkgdblib.PkgdbException, err:
            SESSION.rollback()
            flask.flash(str(err), 'error')

        return flask.redirect(
            flask.url_for('.package_info', package=packagename)
        )

    return flask.render_template(
        'package_give.html',
        full=full,
        form=form,
        packagename=packagename,
    )


@UI.route('/package/<package>/orphan', methods=('GET', 'POST'))
@UI.route('/package/<package>/orphan/<full>', methods=('GET', 'POST'))
@packager_login_required
def package_orphan(package, full=True):
    ''' Gives the possibility to orphan or take a package. '''

    if not bool(full) or full in ['0', 'False']:
        full = False

    try:
        package_acl = pkgdblib.get_acl_package(SESSION, package)
        package = pkgdblib.search_package(SESSION, package, limit=1)[0]
    except (NoResultFound, IndexError):
        SESSION.rollback()
        flask.flash('No package of this name found.', 'errors')
        return flask.render_template('msg.html')

    collections = [
        acl.collection.branchname
        for acl in package_acl
        if acl.collection.status in ['Active', 'Under Development']
        and (
            is_pkgdb_admin(flask.g.fas_user)
            or acl.point_of_contact == flask.g.fas_user.username
        )
    ]

    form = pkgdb2.forms.BranchForm(collections=collections)

    if form.validate_on_submit():
        for branch in form.branches.data:
            try:
                pkgdblib.update_pkg_poc(
                    session=SESSION,
                    pkg_name=package.name,
                    pkg_branch=branch,
                    pkg_poc='orphan',
                    user=flask.g.fas_user
                )
                flask.flash(
                    'You are no longer point of contact on branch: %s'
                    % branch)
            except pkgdblib.PkgdbException, err:  # pragma: no cover
                flask.flash(str(err), 'error')
                SESSION.rollback()

        try:
            SESSION.commit()
        # Keep it in, but normally we shouldn't hit this
        except pkgdblib.PkgdbException, err:  # pragma: no cover
            SESSION.rollback()
            flask.flash(str(err), 'error')

        return flask.redirect(
            flask.url_for('.package_info', package=package.name))

    return flask.render_template(
        'branch_selection.html',
        full=full,
        package=package,
        form=form,
        action='orphan',
    )


@UI.route('/package/<package>/retire', methods=('GET', 'POST'))
@UI.route('/package/<package>/retire/<full>', methods=('GET', 'POST'))
@packager_login_required
def package_retire(package, full=True):
    ''' Gives the possibility to orphan or take a package. '''

    if not bool(full) or full in ['0', 'False']:
        full = False

    try:
        package_acl = pkgdblib.get_acl_package(SESSION, package)
        package = pkgdblib.search_package(SESSION, package, limit=1)[0]
    except (NoResultFound, IndexError):
        SESSION.rollback()
        flask.flash('No package of this name found.', 'errors')
        return flask.render_template('msg.html')

    if not is_pkgdb_admin(flask.g.fas_user):
        flask.flash(
            'Only Admins are allowed to retire package here, '
            'you should use `fedpkg retire`.', 'errors')
        return flask.redirect(
            flask.url_for('.package_info', package=package.name))

    collections = [
        acl.collection.branchname
        for acl in package_acl
        if acl.collection.status in ['Active', 'Under Development']
        and acl.point_of_contact == 'orphan'
    ]

    form = pkgdb2.forms.BranchForm(collections=collections)

    if form.validate_on_submit():
        for acl in package_acl:
            if acl.collection.branchname in form.branches.data:
                if acl.point_of_contact == 'orphan':
                    try:
                        pkgdblib.update_pkg_status(
                            session=SESSION,
                            pkg_name=package.name,
                            pkg_branch=acl.collection.branchname,
                            status='Retired',
                            user=flask.g.fas_user
                        )
                        flask.flash(
                            'This package has been retired on branch: %s'
                            % acl.collection.branchname)
                    except pkgdblib.PkgdbException, err:
                        flask.flash(str(err), 'error')
                        SESSION.rollback()
                else:  # pragma: no cover
                    flask.flash(
                        'This package has not been orphaned on '
                        'branch: %s' % acl.collection.branchname)

        try:
            SESSION.commit()
        # Keep it in, but normally we shouldn't hit this
        except pkgdblib.PkgdbException, err:  # pragma: no cover
            SESSION.rollback()
            flask.flash(str(err), 'error')

        return flask.redirect(
            flask.url_for('.package_info', package=package.name))

    return flask.render_template(
        'branch_selection.html',
        full=full,
        package=package,
        form=form,
        action='retire',
    )


@UI.route('/package/<package>/take', methods=('GET', 'POST'))
@UI.route('/package/<package>/take/<full>', methods=('GET', 'POST'))
@packager_login_required
def package_take(package, full=True):
    ''' Make someone Point of contact of an orphaned package. '''

    if not bool(full) or full in ['0', 'False']:
        full = False

    try:
        package_acl = pkgdblib.get_acl_package(SESSION, package)
        package = pkgdblib.search_package(SESSION, package, limit=1)[0]
    except (NoResultFound, IndexError):
        SESSION.rollback()
        flask.flash('No package of this name found.', 'errors')
        return flask.render_template('msg.html')

    collections = [
        acl.collection.branchname
        for acl in package_acl
        if acl.collection.status in ['Active', 'Under Development']
        and acl.point_of_contact == 'orphan'
    ]

    form = pkgdb2.forms.BranchForm(collections=collections)

    if form.validate_on_submit():
        for branch in form.branches.data:
            try:
                pkgdblib.unorphan_package(
                    session=SESSION,
                    pkg_name=package.name,
                    pkg_branch=branch,
                    pkg_user=flask.g.fas_user.username,
                    user=flask.g.fas_user
                )
                SESSION.commit()
                flask.flash('You have taken the package %s on branch %s' % (
                    package.name, branch))
            except pkgdblib.PkgdbException, err:  # pragma: no cover
                flask.flash(str(err), 'error')
                SESSION.rollback()

        return flask.redirect(
            flask.url_for('.package_info', package=package.name))

    return flask.render_template(
        'branch_selection.html',
        full=full,
        package=package,
        form=form,
        action='take',
    )


@UI.route('/package/<package>/acl/<update_acl>/', methods=('GET', 'POST'))
@packager_login_required
def update_acl(package, update_acl):
    ''' Update the acls of a package. '''

    packagename = package
    package = None
    try:
        package_acl = pkgdblib.get_acl_package(SESSION, packagename)
        package = pkgdblib.search_package(SESSION, packagename, limit=1)[0]
    except (NoResultFound, IndexError):
        SESSION.rollback()
        flask.flash('No package of this name found.', 'errors')
        return flask.render_template('msg.html')

    statues = pkgdblib.get_status(SESSION)
    planned_acls = set(statues['pkg_acl'])
    acl_status = list(set(statues['acl_status']))
    acl_status.insert(0, '')

    if update_acl not in planned_acls:
        flask.flash('Invalid ACL to update.', 'errors')
        return flask.redirect(
            flask.url_for('.package_info', package=package.name))

    branches = {}
    branches_inv = {}
    commit_acls = {}
    admins = {}
    committers = []

    for pkg in package_acl:
        if pkg.collection.status == 'EOL':  # pragma: no cover
            continue

        collection_name = '%s %s' % (
            pkg.collection.name, pkg.collection.version)

        if collection_name not in branches:
            branches[collection_name] = pkg.collection.branchname

        if pkg.collection.branchname not in branches_inv:
            branches_inv[pkg.collection.branchname] = collection_name

        for acl in pkg.acls:

            if acl.acl == 'approveacls' and acl.status == 'Approved':
                if acl.fas_name not in admins:
                    admins[acl.fas_name] = set()
                admins[acl.fas_name].add(collection_name)

            if acl.acl != update_acl:
                continue

            committers.append(acl.fas_name)
            if acl.fas_name not in commit_acls:
                commit_acls[acl.fas_name] = {}
            if collection_name not in commit_acls[acl.fas_name]:
                commit_acls[acl.fas_name][collection_name] = {}

            commit_acls[acl.fas_name][collection_name][acl.acl] = \
                acl.status

        for aclname in planned_acls:
            for user in commit_acls:
                if collection_name in commit_acls[user] and \
                        aclname not in commit_acls[user][collection_name]:
                    commit_acls[user][collection_name][aclname] = None

    # If the user is not an admin, he/she can only access his/her ACLs
    username = flask.g.fas_user.username
    if username not in admins and not is_pkgdb_admin(flask.g.fas_user):
        tmp = {username: []}
        if username in commit_acls:
            tmp = {username: commit_acls[username]}
        commit_acls = tmp

    form = pkgdb2.forms.ConfirmationForm()

    if form.validate_on_submit():
        sub_acls = flask.request.values.getlist('acls')
        sub_users = flask.request.values.getlist('user')
        sub_branches = flask.request.values.getlist('branch')

        if sub_acls and len(sub_acls) == (len(sub_users) * len(sub_branches)):
            cnt = 0
            for cnt_u in range(len(sub_users)):
                for cnt_b in range(len(sub_branches)):
                    lcl_acl = sub_acls[cnt]
                    lcl_user = sub_users[cnt_u]
                    lcl_branch = sub_branches[cnt_b]

                    if lcl_acl not in acl_status:
                        flask.flash('Invalid ACL: %s' % lcl_acl, 'error')
                        cnt += 1
                        continue

                    if branches_inv[lcl_branch] in commit_acls[lcl_user] \
                            and commit_acls[lcl_user][
                                branches_inv[lcl_branch]
                            ][update_acl] == lcl_acl:
                        cnt += 1
                        continue

                    if not lcl_acl:
                        if branches_inv[lcl_branch] \
                                not in commit_acls[lcl_user]:
                            cnt += 1
                            continue
                        elif branches_inv[lcl_branch] in commit_acls[lcl_user] \
                                and username != lcl_user:
                            flask.flash(
                                'Only the user can remove his/her ACL',
                                'error')
                            cnt += 1
                            continue

                    try:
                        pkgdblib.set_acl_package(
                            SESSION,
                            pkg_name=package.name,
                            pkg_branch=lcl_branch,
                            pkg_user=lcl_user,
                            acl=update_acl,
                            status=lcl_acl,
                            user=flask.g.fas_user,
                        )
                        SESSION.commit()
                        flask.flash("%s's %s ACL updated on %s" % (
                            lcl_user, update_acl, lcl_branch))
                    except pkgdblib.PkgdbException, err:
                        SESSION.rollback()
                        flask.flash(str(err), 'error')
                    cnt += 1

            SESSION.commit()
            return flask.redirect(
                flask.url_for('.package_info', package=package.name))
        else:
            flask.flash('Invalid input submitted', 'error')

    return flask.render_template(
        'acl_update.html',
        acl=update_acl,
        acl_status=acl_status,
        package=package,
        form=form,
        branches=branches,
        commit_acls=commit_acls,
        admins=admins,
        committers=committers,
    )
