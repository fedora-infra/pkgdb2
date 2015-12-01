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
import requests
from dateutil import parser
from math import ceil
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

import pkgdb2.forms
import pkgdb2.lib as pkgdblib
from pkgdb2 import SESSION, APP, is_admin, is_pkgdb_admin, is_pkg_admin, \
    packager_login_required, is_authenticated
from pkgdb2.ui import UI


## Some of the object we use here have inherited methods which apparently
## pylint does not detect.
# pylint: disable=E1101


@UI.route('/packages/')
@UI.route('/packages/<motif>/')
def list_packages(motif=None, orphaned=None, status=None,
                  origin='list_packages', case_sensitive=False):
    ''' Display the list of packages corresponding to the motif. '''

    pattern = flask.request.args.get('motif', motif) or '*'
    branches = flask.request.args.get('branches', None)
    owner = flask.request.args.get('owner', None)
    orphaned = flask.request.args.get('orphaned', orphaned)
    if str(orphaned) in ['False', '0']:
        orphaned = False
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

    if len(packages) == 1:
        flask.flash('Only one package matching, redirecting you to it')
        return flask.redirect(flask.url_for(
            '.package_info', package=packages[0].name))

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
        owner=owner,
        branches=branches,
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
            else:  # pragma: no cover  -- pass isn't `covered` by coverage
                # We managed approveacls earlier
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

    statuses = set([
        listing.status
        for listing in package.sorted_listings
        if listing.collection.status != 'EOL'
    ])

    collections = pkgdb2.lib.search_collection(
        SESSION, '*', 'Under Development')
    collections.extend(pkgdb2.lib.search_collection(SESSION, '*', 'Active'))
    branches_possible = [
        collec.branchname
        for collec in collections
        if '%s %s' % (collec.name, collec.version) not in branches]

    requester = False
    if is_authenticated():
        for req in package.requests:
            if req.user == flask.g.fas_user.username:
                requester = True
                break

    return flask.render_template(
        'package.html',
        package=package,
        commit_acls=commit_acls,
        watch_acls=watch_acls,
        pocs=pocs,
        admins=admins,
        statuses=statuses,
        pending_admins=pending_admins,
        branches=branches,
        branches_possible=branches_possible,
        committers=committers,
        form=pkgdb2.forms.ConfirmationForm(),
        requester=requester,
    )


@UI.route('/package/<package>/timeline')
def package_timeline(package):
    """ Return the timeline of a specified package.
    """
    from_date = flask.request.args.get('from_date', None)
    packager = flask.request.args.get('packager', None)
    limit = flask.request.args.get('limit', APP.config['ITEMS_PER_PAGE'])
    page = flask.request.args.get('page', 1)

    try:
        page = abs(int(page))
    except ValueError:
        page = 1

    try:
        limit = abs(int(limit))
    except ValueError:
        limit = APP.config['ITEMS_PER_PAGE']
        flask.flash('Incorrect limit provided, using default', 'errors')

    if from_date:
        try:
            from_date = parser.parse(from_date)
        except (ValueError, TypeError):
            flask.flash(
                'Incorrect from_date provided, using default', 'errors')
            from_date = None

    ## Could not infer the date() function
    # pylint: disable=E1103
    if from_date:
        from_date = from_date.date()

    logs = []
    cnt_logs = 0
    try:
        logs = pkgdblib.search_logs(
            SESSION,
            package=package or None,
            packager=packager or None,
            from_date=from_date,
            page=page,
            limit=limit,
        )
        cnt_logs = pkgdblib.search_logs(
            SESSION,
            package=package or None,
            packager=packager or None,
            from_date=from_date,
            count=True
        )
    except pkgdblib.PkgdbException, err:
        flask.flash(err, 'errors')

    total_page = int(ceil(cnt_logs / float(limit)))

    return flask.render_template(
        'package_timeline.html',
        logs=logs,
        cnt_logs=cnt_logs,
        total_page=total_page,
        page=page,
        package=package,
        from_date=from_date or '',
        packager=packager or '',
    )


@UI.route('/package/<package>/anitya')
@UI.route('/package/<package>/anitya/<full>')
def package_anitya(package, full=True):
    """ Return information anitya integration about this package.
    """
    if str(full).lower() in ['0', 'false']:
        full = False

    pkg = None
    try:
        pkg = pkgdblib.search_package(SESSION, package, limit=1)[0]
    except (NoResultFound, IndexError):
        SESSION.rollback()
        flask.flash('No package of this name found.', 'errors')
        return flask.render_template('msg.html')

    url = '%s/api/project/%s/%s' % (
        APP.config['PKGDB2_ANITYA_URL'],
        APP.config['PKGDB2_ANITYA_DISTRO'],
        package
    )

    data = {}
    try:
        req = requests.get(url)
        if req.status_code != 200:
            raise pkgdblib.PkgdbException(
                'Querying anitya returned a status %s' % req.status_code)
        else:
            data = req.json()
    except Exception, err:
        flask.flash(err.message, 'error')
        pass

    return flask.render_template(
        'package_anitya.html',
        full=full,
        package=package,
        pkg=pkg,
        data=data,
    )


@UI.route('/package/requests/<action_id>', methods=['GET', 'POST'])
def package_request_edit(action_id):
    """ Edit an Admin Action status
    """

    admin_action = pkgdblib.get_admin_action(SESSION, action_id)
    if not admin_action:
        flask.flash('No action found with this identifier.', 'errors')
        return flask.render_template('msg.html')

    package = None
    if admin_action.package:
        package = admin_action.package.name

    if admin_action.status in ['Accepted', 'Blocked', 'Denied']:
        return flask.render_template(
            'actions_update_ro.html',
            admin_action=admin_action,
            action_id=action_id,
        )

    if not is_authenticated() or not 'packager' in flask.g.fas_user.groups:
        return flask.render_template(
            'actions_update_ro.html',
            admin_action=admin_action,
            action_id=action_id,
        )

    # Check user is the pkg/pkgdb admin
    pkg_admin = pkgdblib.has_acls(
        SESSION, flask.g.fas_user.username, package, 'approveacls')
    if not is_pkgdb_admin(flask.g.fas_user) \
            and not pkg_admin \
            and not admin_action.user == flask.g.fas_user.username:
        flask.flash(
            'Only package adminitrators (`approveacls`) and the requester '
            'can review pending branch requests', 'errors')
        if package:
            return flask.redirect(
                flask.url_for('.package_info', package=package)
            )
        else:
            return flask.redirect(
                flask.url_for(
                    '.packager_requests',
                    packager=flask.g.fas_user.username)
            )

    action_status = ['Pending', 'Awaiting Review', 'Blocked']
    if admin_action.user == flask.g.fas_user.username:
        action_status = ['Pending', 'Obsolete']
        if pkg_admin or admin_action.action in [
                'request.package', 'request.unretire']:
            action_status.append('Awaiting Review')

    form = pkgdb2.forms.EditActionStatusForm(
        status=action_status,
        obj=admin_action
    )
    form.id.data = action_id

    if form.validate_on_submit():

        try:
            message = pkgdblib.edit_action_status(
                SESSION,
                admin_action,
                action_status=form.status.data,
                user=flask.g.fas_user,
                message=form.message.data,
            )
            SESSION.commit()
            flask.flash(message)
        except pkgdblib.PkgdbException, err:  # pragma: no cover
            # We can only reach here in two cases:
            # 1) the user is not an admin, but that's taken care of
            #    by the decorator
            # 2) we have a SQLAlchemy problem when storing the info
            #    in the DB which we cannot test
            SESSION.rollback()
            flask.flash(err, 'errors')
            return flask.render_template('msg.html')

        if package:
            return flask.redirect(
                flask.url_for('.package_info', package=package)
            )
        else:
            return flask.redirect(
                flask.url_for(
                    '.packager_requests',
                    packager=flask.g.fas_user.username)
            )

    return flask.render_template(
        'actions_update.html',
        admin_action=admin_action,
        action_id=action_id,
        form=form,
        package=package,
        tag='packages',
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

    if not bool(full) or str(full) in ['0', 'False']:
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
        except pkgdblib.PkgdbBugzillaException, err:  # pragma: no cover
            APP.logger.exception(err)
            flask.flash(str(err), 'error')
            SESSION.rollback()
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

    if not bool(full) or str(full) in ['0', 'False']:
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
        and acl.status == 'Approved'
        and (
            is_pkgdb_admin(flask.g.fas_user)
            or acl.point_of_contact == flask.g.fas_user.username
            or (
                acl.point_of_contact.startswith('group::') and
                is_pkg_admin(SESSION, flask.g.fas_user, package.name)
            )
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
            except pkgdblib.PkgdbBugzillaException, err:  # pragma: no cover
                APP.logger.exception(err)
                flask.flash(str(err), 'error')
                SESSION.rollback()
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

    if not bool(full) or str(full) in ['0', 'False']:
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
        and acl.status == 'Orphaned'
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
                    except pkgdblib.PkgdbException, err:  # pragma: no cover
                        # We should never hit this
                        flask.flash(str(err), 'error')
                        SESSION.rollback()
                        APP.logger.exception(err)
                else:  # pragma: no cover
                    flask.flash(
                        'This package has not been orphaned on '
                        'branch: %s' % acl.collection.branchname)

        try:
            SESSION.commit()
        # Keep it in, but normally we shouldn't hit this
        except pkgdblib.PkgdbException, err:  # pragma: no cover
            # We should never hit this
            SESSION.rollback()
            APP.logger.exception(err)
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


@UI.route('/package/<package>/unretire', methods=('GET', 'POST'))
@UI.route('/package/<package>/unretire/<full>', methods=('GET', 'POST'))
@packager_login_required
def package_unretire(package, full=True):
    ''' Asks an admin to unretire the package. '''

    if not bool(full) or str(full) in ['0', 'False']:
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
        and acl.status == 'Retired'
    ]

    form = pkgdb2.forms.UnretireForm(collections=collections)

    if form.validate_on_submit():
        review_url = form.review_url.data
        review_url = review_url.strip() if review_url else None
        checks_ok = True
        for br in form.branches.data:
            if br == 'master' and not review_url:
                checks_ok = False
                flask.flash(
                    'You must provide a review URL to un-retire master',
                    'error')
                break
            elif br.startswith('e') and 'master' in collections and not review_url:
                checks_ok = False
                flask.flash(
                    'You must provide a review URL to un-retire an EPEL '
                    'branch if master is also retired',
                    'error')
                break

        if not checks_ok:
            return flask.redirect(
                flask.url_for('.package_info', package=package.name))

        for acl in package_acl:
            if acl.collection.branchname in form.branches.data:
                if acl.point_of_contact == 'orphan':
                    try:
                        pkgdblib.add_unretire_request(
                            session=SESSION,
                            pkg_name=package.name,
                            pkg_branch=acl.collection.branchname,
                            review_url=form.review_url.data,
                            user=flask.g.fas_user,
                        )
                        flask.flash(
                            'Admins have been asked to un-retire branch: %s'
                            % acl.collection.branchname)
                    except pkgdblib.PkgdbException, err:  # pragma: no cover
                        # We should never hit this
                        flask.flash(str(err), 'error')
                        SESSION.rollback()
                    except SQLAlchemyError, err:
                        SESSION.rollback()
                        flask.flash(
                            'Could not save the request for branch: %s, has '
                            'it already been requested?'
                            % acl.collection.branchname, 'error')
                else:  # pragma: no cover
                    flask.flash(
                        'This package is not orphaned on branch: %s'
                        % acl.collection.branchname)

        try:
            SESSION.commit()
        # Keep it in, but normally we shouldn't hit this
        except pkgdblib.PkgdbException, err:  # pragma: no cover
            # We should never hit this
            SESSION.rollback()
            APP.logger.exception(err)
            flask.flash(str(err), 'error')

        return flask.redirect(
            flask.url_for('.package_info', package=package.name))

    return flask.render_template(
        'request_unretire.html',
        full=full,
        package=package,
        form=form,
        action='unretire',
    )


@UI.route('/package/<package>/take', methods=('GET', 'POST'))
@UI.route('/package/<package>/take/<full>', methods=('GET', 'POST'))
@packager_login_required
def package_take(package, full=True):
    ''' Make someone Point of contact of an orphaned package. '''

    if not bool(full) or str(full) in ['0', 'False']:
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
        and acl.status == 'Orphaned'
    ]

    if not collections:
        flask.flash('No branches orphaned found', 'error')
        return flask.redirect(
            flask.url_for('.package_info', package=package.name))

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
            except pkgdblib.PkgdbBugzillaException, err:  # pragma: no cover
                APP.logger.exception(err)
                flask.flash(str(err), 'error')
                SESSION.rollback()
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
        changed = False

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

                    if lcl_user not in commit_acls:
                        flask.flash('Invalid user: %s' % lcl_user, 'error')
                        cnt += 1
                        continue

                    if lcl_branch not in branches_inv or (
                        branches_inv[lcl_branch] in commit_acls[lcl_user]
                            and commit_acls[lcl_user][
                                branches_inv[lcl_branch]][
                                    update_acl] == lcl_acl):
                        cnt += 1
                        continue

                    if not lcl_acl:
                        if branches_inv[lcl_branch] \
                                not in commit_acls[lcl_user]:
                            cnt += 1
                            continue
                        elif branches_inv[lcl_branch] \
                                in commit_acls[lcl_user] \
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
                        changed = True
                    except pkgdblib.PkgdbException, err:
                        SESSION.rollback()
                        flask.flash(str(err), 'error')
                    cnt += 1

            SESSION.commit()
            if not changed:
                flask.flash('Nothing to update')
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


@UI.route('/package/<package>/delete', methods=['POST'])
@is_admin
def delete_package(package):
    ''' Delete the specified package.
    '''
    form = pkgdb2.forms.ConfirmationForm()

    if not form.validate_on_submit():
        flask.flash('Invalid input', 'error')
        return flask.redirect(
            flask.url_for('.package_info', package=package))

    packagename = package
    package = None
    try:
        package = pkgdblib.search_package(SESSION, packagename, limit=1)[0]
    except (NoResultFound, IndexError):
        SESSION.rollback()
        flask.flash('No package of this name found.', 'errors')
        return flask.render_template('msg.html')

    for pkglist in package.listings:
        for acl in pkglist.acls:
            pkgdb2.lib.utils.log(SESSION, None, 'acl.delete', dict(
                agent=flask.g.fas_user.username,
                acl=acl.to_json(),
            ))
            SESSION.delete(acl)
        pkgdb2.lib.utils.log(SESSION, None, 'package.branch.delete', dict(
            agent=flask.g.fas_user.username,
            package_listing=pkglist.to_json(),
        ))
        SESSION.delete(pkglist)

    pkgdb2.lib.utils.log(SESSION, None, 'package.delete', dict(
        agent=flask.g.fas_user.username,
        package=package.to_json(),
    ))
    SESSION.delete(package)

    try:
        SESSION.commit()
        flask.flash('Package %s deleted' % packagename)
    except SQLAlchemyError, err:  # pragma: no cover
        SESSION.rollback()
        flask.flash(
            'An error occured while trying to delete the package %s'
            % packagename, 'error')
        APP.logger.debug('Could not delete package: %s', packagename)
        APP.logger.exception(err)
        return flask.redirect(
            flask.url_for('.package_info', package=package.name))

    return flask.redirect(
        flask.url_for('.list_packages'))


@UI.route('/package/<package>/request_branch', methods=('GET', 'POST'))
@UI.route('/package/<package>/request_branch/<full>', methods=('GET', 'POST'))
@packager_login_required
def package_request_branch(package, full=True):
    ''' Gives the possibility to request a new branch for this package. '''

    if not bool(full) or str(full) in ['0', 'False']:
        full = False

    try:
        package_acl = pkgdblib.get_acl_package(SESSION, package)
        package = pkgdblib.search_package(SESSION, package, limit=1)[0]
    except (NoResultFound, IndexError):
        SESSION.rollback()
        flask.flash('No package of this name found.', 'errors')
        return flask.render_template('msg.html')

    branches = [
        pkg.collection.branchname
        for pkg in package_acl
        if pkg.collection.status != 'EOL'
    ]

    collections = pkgdb2.lib.search_collection(
        SESSION, '*', 'Under Development')
    collections.extend(pkgdb2.lib.search_collection(SESSION, '*', 'Active'))
    branches_possible = [
        collec.branchname
        for collec in collections
        if collec.branchname not in branches]

    form = pkgdb2.forms.BranchForm(collections=branches_possible)

    if form.validate_on_submit():
        for branch in form.branches.data:
            try:
                msg = pkgdblib.add_new_branch_request(
                    session=SESSION,
                    pkg_name=package.name,
                    clt_to=branch,
                    user=flask.g.fas_user)
                SESSION.commit()
                flask.flash(msg)
            except pkgdblib.PkgdbException, err:  # pragma: no cover
                flask.flash(str(err), 'error')
                SESSION.rollback()
            except SQLAlchemyError, err:  # pragma: no cover
                APP.logger.exception(err)
                flask.flash(
                    'Could not save the request to the database for '
                    'branch: %s' % branch, 'error')
                SESSION.rollback()

        return flask.redirect(
            flask.url_for('.package_info', package=package.name))

    return flask.render_template(
        'request_branch.html',
        full=full,
        package=package,
        form=form,
        action='request_branch',
    )


@UI.route('/request/package/', methods=('GET', 'POST'))
@packager_login_required
def package_request_new():
    ''' Page to request a new package. '''

    collections = pkgdb2.lib.search_collection(SESSION, '*', 'Under Development')
    collections.reverse()
    active_collections = pkgdb2.lib.search_collection(SESSION, '*', 'Active')
    active_collections.reverse()
    # We want all the branch `Under Development` as well as all the `Active`
    # branch but we can only have at max 2 Fedora branch active at the same
    # time. In other words, when Fedora n+1 is released one can no longer
    # request a package to be added to Fedora n-1
    cnt = 0
    for collection in active_collections:
        if collection.name.lower() == 'fedora':
            if cnt >= 2:
                continue
            cnt += 1
        collections.append(collection)

    form = pkgdb2.forms.RequestPackageForm(
        collections=collections,
    )

    if form.validate_on_submit():
        pkg_name = form.pkgname.data
        pkg_summary = form.summary.data
        pkg_description = form.description.data
        pkg_review_url = form.review_url.data
        pkg_status = 'Approved'
        pkg_critpath = False
        pkg_collection = form.branches.data
        if not 'master' in pkg_collection:
            flask.flash(
                'Adding a request for `master` branch, this branch is '
                'mandatory')
            pkg_collection.append('master')
        pkg_poc = flask.g.fas_user.username
        pkg_upstream_url = form.upstream_url.data

        bz = APP.config.get('PKGDB2_BUGZILLA_URL')
        if bz not in pkg_review_url:
            try:
                int(pkg_review_url)
                pkg_review_url = bz + '/' + pkg_review_url
            except (TypeError, ValueError):
                pass

        try:
            messages = []
            for clt in pkg_collection:
                message = pkgdblib.add_new_package_request(
                    SESSION,
                    pkg_name=pkg_name,
                    pkg_summary=pkg_summary,
                    pkg_description=pkg_description,
                    pkg_review_url=pkg_review_url,
                    pkg_status=pkg_status,
                    pkg_critpath=pkg_critpath,
                    pkg_collection=clt,
                    pkg_poc=pkg_poc,
                    pkg_upstream_url=pkg_upstream_url,
                    user=flask.g.fas_user,
                )
                if message:
                    messages.append(message)
            SESSION.commit()
            for message in messages:
                flask.flash(message)
            return flask.redirect(flask.url_for('.index'))
        # Keep it in, but normally we shouldn't hit this
        except pkgdblib.PkgdbException, err:  # pragma: no cover
            SESSION.rollback()
            flask.flash(str(err), 'error')

    return flask.render_template(
        'package_request.html',
        form=form,
    )
