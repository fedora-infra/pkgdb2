# -*- coding: utf-8 -*-
#
# Copyright © 2015  Red Hat, Inc.
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
UI redirects to keep the URLs working from before the namespacing change
'''

import flask

from pkgdb2 import packager_login_required, is_admin, fas_login_required
from pkgdb2.ui import UI
import pkgdb2.ui.packages as packages
import pkgdb2.ui.acls as acls

#
# packages controller
#

@UI.route('/packages/<motif>/')
def old_list_packages(motif=None):
    return flask.redirect(flask.url_for(
        'ui_ns.list_packages', namespace='rpms', motif=motif))


@UI.route('/package/<package>/')
@UI.route('/package/<namespace>/<package>/')
def old_package_info(package):
    return flask.redirect(flask.url_for(
        'ui_ns.package_info', namespace='rpms', package=package))


@UI.route('/package/<package>/timeline')
def old_package_timeline(package):
    return flask.redirect(flask.url_for(
        'ui_ns.package_timeline', namespace='rpms', package=package))


@UI.route('/package/<package>/anitya')
@UI.route('/package/<package>/anitya/<full>')
def old_package_anitya(package, full=True):
    return flask.redirect(flask.url_for(
        'ui_ns.package_anitya', namespace='rpms', package=package, full=full))


@UI.route('/package/<package>/give', methods=('GET', 'POST'))
@UI.route('/package/<package>/give/<full>', methods=('GET', 'POST'))
@packager_login_required
def old_package_give(package, full=True):
    if flask.request.method == 'GET':
        return flask.redirect(flask.url_for(
            'ui_ns.package_give', namespace='rpms', package=package, full=full))
    else:
        return packages.package_give('rpms', package, full=full)


@UI.route('/package/<package>/orphan', methods=('GET', 'POST'))
@UI.route('/package/<package>/orphan/<full>', methods=('GET', 'POST'))
@packager_login_required
def old_package_orphan(package, full=True):
    if flask.request.method == 'GET':
        return flask.redirect(flask.url_for(
            'ui_ns.package_orphan', namespace='rpms', package=package, full=full))
    else:
        return packages.package_orphan('rpms', package, full=full)


@UI.route('/package/<package>/retire', methods=('GET', 'POST'))
@UI.route('/package/<package>/retire/<full>', methods=('GET', 'POST'))
@packager_login_required
def old_package_retire(package, full=True):
    if flask.request.method == 'GET':
        return flask.redirect(flask.url_for(
            'ui_ns.package_retire', namespace='rpms', package=package, full=full))
    else:
        return packages.package_retire('rpms', package, full=full)


@UI.route('/package/<package>/unretire', methods=('GET', 'POST'))
@UI.route('/package/<package>/unretire/<full>', methods=('GET', 'POST'))
@packager_login_required
def old_package_unretire(package, full=True):
    if flask.request.method == 'GET':
        return flask.redirect(flask.url_for(
            'ui_ns.package_unretire', namespace='rpms', package=package, full=full))
    else:
        return packages.package_unretire('rpms', package, full=full)


@UI.route('/package/<package>/take', methods=('GET', 'POST'))
@UI.route('/package/<package>/take/<full>', methods=('GET', 'POST'))
@packager_login_required
def old_package_take(package, full=True):
    if flask.request.method == 'GET':
        return flask.redirect(flask.url_for(
            'ui_ns.package_take', namespace='rpms', package=package, full=full))
    else:
        return packages.package_take('rpms', package, full=full)


@UI.route('/package/<package>/acl/<update_acl>/', methods=('GET', 'POST'))
@packager_login_required
def old_update_acl(package, update_acl):
    if flask.request.method == 'GET':
        return flask.redirect(flask.url_for(
            'ui_ns.update_acl', namespace='rpms',
            package=package, update_acl=update_acl))
    else:
        return packages.update_acl('rpms', package, update_acl=update_acl)


@UI.route('/package/<package>/delete', methods=['POST'])
@is_admin
def old_delete_package(package):
    return packages.update_acl('rpms', package)


@UI.route('/package/<package>/request_branch', methods=('GET', 'POST'))
@UI.route('/package/<package>/request_branch/<full>', methods=('GET', 'POST'))
@packager_login_required
def old_package_request_branch(package, full=True):
    if flask.request.method == 'GET':
        return flask.redirect(flask.url_for(
            'ui_ns.package_request_branch', namespace='rpms',
            package=package, full=full))
    else:
        return packages.package_request_branch(
            'rpms', package, update_acl=update_acl)

#
# ACLs controller
#

@UI.route('/acl/<package>/request/', methods=('GET', 'POST'))
@fas_login_required
def old_request_acl(package):
    if flask.request.method == 'GET':
        return flask.redirect(flask.url_for(
            'ui_ns.request_acl', namespace='rpms', package=package))
    else:
        return acls.request_acl('rpms', package)


@UI.route('/acl/<package>/request/<acl>/', methods=['POST'])
@fas_login_required
def old_request_acl_all_branch(package, acl):
    return acls.request_acl_all_branch('rpms', package)


@UI.route('/acl/<package>/giveup/<acl>/', methods=['POST'])
@fas_login_required
def old_giveup_acl(package, acl):
    return acls.giveup_acl('rpms', package)


@UI.route('/acl/<package>/give/', methods=('GET', 'POST'))
@fas_login_required
def old_package_give_acls(package):
    if flask.request.method == 'GET':
        return flask.redirect(flask.url_for(
            'ui_ns.package_give_acls', namespace='rpms', package=package))
    else:
        return acls.package_give_acls('rpms', package)


@UI.route('/acl/<package>/watch/', methods=['POST'])
@fas_login_required
def old_watch_package(package):
    return acls.watch_package('rpms', package)


@UI.route('/acl/<package>/unwatch/', methods=['POST'])
@fas_login_required
def old_unwatch_package(package):
    return acls.unwatch_package('rpms', package)


@UI.route('/acl/<package>/comaintain/', methods=['POST'])
@packager_login_required
def old_comaintain_package(package):
    return acls.comaintain_package('rpms', package)


@UI.route('/acl/<package>/dropcommit/', methods=['POST'])
@fas_login_required
def old_dropcommit_package(package):
    return acls.dropcommit_package('rpms', package)
