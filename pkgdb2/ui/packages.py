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
    is_pkg_admin, packager_login_required, is_authenticated
from pkgdb2.ui import UI


## Some of the object we use here have inherited methods which apparently
## pylint does not detect.
# pylint: disable=E1101


@UI.route('/packages/')
@UI.route('/packages/<motif>/')
def list_packages(motif=None, orphaned=False, status='Approved',
                  origin='list_packages'):
    ''' Display the list of packages corresponding to the motif. '''

    pattern = flask.request.args.get('motif', motif) or '*'
    branches = flask.request.args.get('branches', None)
    owner = flask.request.args.get('owner', None)
    orphaned = bool(flask.request.args.get('orphaned', orphaned))
    status = flask.request.args.get('status', status)
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
        pkg_branch=branches,
        pkg_poc=owner,
        orphaned=orphaned,
        status=status,
        page=page,
        limit=limit,
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
        count=True
    )
    total_page = int(ceil(packages_count / float(limit)))

    return flask.render_template(
        'list_packages.html',
        origin=origin,
        packages=packages,
        motif=motif,
        total_page=total_page,
        packages_count=packages_count,
        page=page
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
    branch_admin = {}
    branch_poc = {}
    is_poc = False

    for pkg in package_acl:
        if pkg.collection.status == 'EOL':  # pragma: no cover
            continue

        collection_name = '%s %s' % (
            pkg.collection.name, pkg.collection.version)

        branches.add(collection_name)

        if pkg.point_of_contact not in branch_poc:
            branch_poc[pkg.point_of_contact] = set()
        branch_poc[pkg.point_of_contact].add(collection_name)

        if is_authenticated() and \
                pkg.point_of_contact == flask.g.fas_user.username:
            is_poc = True


        acls = {}
        for acl in pkg.acls:

            if acl.acl == 'approveacls' and acl.status == 'Approved':
                if acl.fas_name not in branch_admin:
                    branch_admin[acl.fas_name] = set()
                branch_admin[acl.fas_name].add(collection_name)

            if acl.acl == 'commit':
                dic = commit_acls
            elif acl.acl.startswith('watch'):
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

    #package_acls.reverse()
    #if package_acls:
        #package_acls.insert(0, package_acls.pop())

    # This section checks if the user has watch*, commit and approveacls
    # ACLs on all branches, and according to the results the options on the
    # menu on the right side will be enabled or not (default to enabled).
    #has_watch = False
    #has_commit = False
    #has_all_acls = False
    #if is_authenticated():
        #tmp_commit = []
        #tmp_watchco = []
        #tmp_watchbz = []
        #tmp_appro = []
        #username = flask.g.fas_user.username
        #for branch in package_acls:
            #if username in branch['acls']:
                #for acl in branch['acls'][username]:
                    #if acl['acl'] == 'commit':
                        #tmp_commit.append(acl['status'] == 'Approved')
                    #elif acl['acl'] == 'watchbugzilla':
                        #tmp_watchbz.append(acl['status'] == 'Approved')
                    #elif acl['acl'] == 'watchcommits':
                        #tmp_watchco.append(acl['status'] == 'Approved')
                    #elif acl['acl'] == 'approveacls':
                        #tmp_appro.append(acl['status'] == 'Approved')
        #if all(tmp_commit):
            #has_commit = True
        #if all(tmp_watchbz) and all(tmp_watchco):
            #has_watch = True
        #if all(tmp_commit) and all(tmp_watchbz) and all(tmp_watchco) \
                #and all(tmp_appro):
            #has_all_acls = True

    return flask.render_template(
        'package.html',
        package=package,
        commit_acls=commit_acls,
        watch_acls=watch_acls,
        branch_admin=branch_admin,
        branch_poc=branch_poc,
        branches=branches,
        is_poc=is_poc,
        #has_watch=has_watch,
        #has_commit=has_commit,
        #has_all_acls=has_all_acls,
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
        pkg_shouldopen = form.shouldopen.data
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
                pkg_shouldopen=pkg_shouldopen,
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
@packager_login_required
def package_give(package):
    ''' Gives the PoC of a package to someone else. '''

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
        form=form,
        packagename=packagename,
    )


@UI.route('/package/<package>/<collection>/orphan', methods=('GET', 'POST'))
@packager_login_required
def package_orphan(package, collection):
    ''' Gives the possibility to orphan or take a package. '''

    packagename = package
    package = None
    try:
        package_acl = pkgdblib.get_acl_package(SESSION, packagename)
        package = pkgdblib.search_package(SESSION, packagename, limit=1)[0]
    except (NoResultFound, IndexError):
        SESSION.rollback()
        flask.flash('No package of this name found.', 'errors')
        return flask.render_template('msg.html')

    for acl in package_acl:
        if acl.collection.branchname == collection:
            try:
                pkgdblib.update_pkg_poc(
                    session=SESSION,
                    pkg_name=package.name,
                    pkg_branch=acl.collection.branchname,
                    pkg_poc='orphan',
                    user=flask.g.fas_user
                )
                flask.flash(
                    'You are no longer point of contact on branch: %s'
                    % collection)
            except pkgdblib.PkgdbException, err:
                flask.flash(str(err), 'error')
                SESSION.rollback()
            break

    try:
        SESSION.commit()
    # Keep it in, but normally we shouldn't hit this
    except pkgdblib.PkgdbException, err:  # pragma: no cover
        SESSION.rollback()
        flask.flash(str(err), 'error')

    return flask.redirect(
        flask.url_for('.package_info', package=package.name))


@UI.route('/package/<package>/<collection>/retire', methods=('GET', 'POST'))
@packager_login_required
def package_retire(package, collection):
    ''' Gives the possibility to orphan or take a package. '''

    packagename = package
    package = None
    try:
        package_acl = pkgdblib.get_acl_package(SESSION, packagename)
        package = pkgdblib.search_package(SESSION, packagename, limit=1)[0]
    except (NoResultFound, IndexError):
        SESSION.rollback()
        flask.flash('No package of this name found.', 'errors')
        return flask.render_template('msg.html')

    for acl in package_acl:
        if acl.collection.branchname == collection:
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
                        % collection)
                except pkgdblib.PkgdbException, err:
                    flask.flash(str(err), 'error')
                    SESSION.rollback()
                break
            else:
                flask.flash(
                    'This package has not been orphaned on '
                    'branch: %s' % collection)

    try:
        SESSION.commit()
    # Keep it in, but normally we shouldn't hit this
    except pkgdblib.PkgdbException, err:  # pragma: no cover
        SESSION.rollback()
        flask.flash(str(err), 'error')

    return flask.redirect(
        flask.url_for('.package_info', package=package.name))


@UI.route('/package/<package>/<collection>/take', methods=('GET', 'POST'))
@packager_login_required
def package_take(package, collection):
    ''' Make someone Point of contact of an orphaned package. '''

    try:
        pkgdblib.unorphan_package(
            session=SESSION,
            pkg_name=package,
            pkg_branch=collection,
            pkg_user=flask.g.fas_user.username,
            user=flask.g.fas_user
        )
        SESSION.commit()
        flask.flash('You have taken the package %s on branch %s' % (
            package, collection))
    except pkgdblib.PkgdbException, err:
        SESSION.rollback()
        flask.flash(str(err), 'error')

    return flask.redirect(
        flask.url_for('.package_info', package=package))
