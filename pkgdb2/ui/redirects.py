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

from pkgdb2 import packager_login_required
from pkgdb2.ui import UI

#@UI.route('/packages/')
#@UI.route('/packages/<motif>/')
#def list_packages(motif=None, orphaned=None, status=None, namespace=None,
                  #origin='list_packages', case_sensitive=False):

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


@UI.route('/package/<package>/give')
@UI.route('/package/<package>/give/<full>')
@packager_login_required
def old_package_give(package, full=True):
    return flask.redirect(flask.url_for(
        'ui_ns.package_give', namespace='rpms', package=package, full=full))


@UI.route('/package/<package>/orphan')
@UI.route('/package/<package>/orphan/<full>')
@packager_login_required
def old_package_orphan(package, full=True):
    return flask.redirect(flask.url_for(
        'ui_ns.package_orphan', namespace='rpms', package=package, full=full))


@UI.route('/package/<package>/retire')
@UI.route('/package/<package>/retire/<full>')
@packager_login_required
def old_package_retire(package, full=True):
    return flask.redirect(flask.url_for(
        'ui_ns.package_retire', namespace='rpms', package=package, full=full))


@UI.route('/package/<package>/unretire')
@UI.route('/package/<package>/unretire/<full>')
@packager_login_required
def old_package_unretire(package, full=True):
    return flask.redirect(flask.url_for(
        'ui_ns.package_unretire', namespace='rpms', package=package, full=full))


@UI.route('/package/<package>/take')
@UI.route('/package/<package>/take/<full>')
@packager_login_required
def old_package_take(package, full=True):
    return flask.redirect(flask.url_for(
        'ui_ns.package_take', namespace='rpms', package=package, full=full))


@UI.route('/package/<package>/acl/<update_acl>/')
@packager_login_required
def old_update_acl(package, update_acl):
    return flask.redirect(flask.url_for(
        'ui_ns.update_acl', namespace='rpms',
        package=package, update_acl=update_acl))


@UI.route('/package/<package>/request_branch')
@UI.route('/package/<package>/request_branch/<full>')
@packager_login_required
def old_package_request_branch(package, full=True):
    return flask.redirect(flask.url_for(
        'ui_ns.package_request_branch', namespace='rpms',
        package=package, full=full))
