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
API for ACL management.
'''

import itertools
import flask

from sqlalchemy.orm.exc import NoResultFound

import pkgdb
import pkgdb.forms as forms
import pkgdb.lib as pkgdblib
from pkgdb.api import API
from pkgdb.lib import model


## ACL
@API.route('/package/acl/get/')
@API.route('/package/acl/get/<packagename>/')
def api_acl_get(packagename=None):
    ''' ``/api/package/acl/get/<packagename>/`` or ``/api/package/acl/get/?packagename=<packagename>``
    Returns the ACL for a given package.

    Accept GET queries only.

    :arg packagename: String of the package name that one wants the ACL
        of.
    :return: a JSON string containing the ACL information for that
        package.

    '''
    packagename = flask.request.args.get('packagename', None) or packagename
    httpcode = 200
    output = {}
    if packagename:
        try:
            packages = pkgdblib.get_acl_package(SESSION, packagename)
            output = {'acls': [pkg.to_json() for pkg in packages]}
        except NoResultFound:
            SESSION.rollback()
            output['output'] = 'notok'
            output['error'] = 'No package found with name "%s"' % packagename
            httpcode = 500
    else:
        output = {'output': 'notok', 'error': 'No package provided'}
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/package/acl/', methods=['POST'])
def api_acl_update():
    ''' ``/api/package/acl/``
    Update the ACL for a given package.

    Accept POST queries only.

    :arg pkg_name: String of the package name.
    :arg pkg_branch: List of strings with the name of the branches to change,
        update.
    :arg pkg_acl: List of strings of the ACL to change/update. Possible acl
        are: 'commit', 'build', 'watchbugzilla', 'watchcommits',
        'approveacls', 'checkout'.
    :arg pkg_status: String of the type of action required. Possible status
        are: 'Approved', 'Awaiting Review', 'Denied', 'Obsolete', 'Removed'.
    :kwarg pkg_user: the name of the user that is the target of this ACL
        change/update. This will only work if: 1) you are an admin,
        2) you are changing one of your package.

     '''
    httpcode = 200
    output = {}

    status = pkgdb.lib.get_status(SESSION, ['pkg_acl', 'acl_status'])

    form = forms.SetAclPackageForm(
        csrf_enabled=False,
        pkg_acl=status['pkg_acl'],
        acl_status=status['acl_status'],
    )
    if form.validate_on_submit():
        pkg_name = form.pkg_name.data
        pkg_branch = form.pkg_branch.data.split(',')
        pkg_acl = form.pkg_acl.data
        pkg_status = form.pkg_status.data
        pkg_user = form.pkg_user.data

        try:
            for branch in pkg_branch:
                message = pkgdblib.set_acl_package(
                    SESSION,
                    pkg_name=pkg_name,
                    pkg_branch=branch,
                    pkg_acl=pkg_acl,
                    pkg_status=pkg_status,
                    pkg_user=pkg_user,
                    user=flask.g.fas_user.username,
                )
            SESSION.commit()
            output['output'] = 'ok'
            output['messages'] = [message]
        except pkgdblib.PkgdbException, err:
            SESSION.rollback()
            output['output'] = 'notok'
            output['error'] = err
            httpcode = 500
    else:
        output['output'] = 'notok'
        output['error'] = 'Invalid input submitted'
        if form.errors:
            detail = []
            for error in form.errors:
                detail.append('%s: %s' % (error,
                              '; '.join(form.errors[error])))
            output['error_detail'] = detail
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/package/acl/reassign/', methods=['POST'])
def api_acl_reassign():
    ''' ``/api/package/acl/reassign/``
    Reassign the specified packages from one user to another.

    Accept POST queries only.

    :arg packages: List of strings of the package name to reassign.
    :arg branches: List of strings of the branchname of the Collection on
        which to reassign the point of contact.
    :arg user_target: User name of the new point of contact.

    '''
    httpcode = 200
    output = {}

    packages = flask.request.args.get('packages', None)
    branches = flask.request.args.get('branches', '').split(',')
    user_target = flask.request.args.get('user_target', '').split(',')

    if not packages or not branches or not user_target:
        output['output'] = 'notok'
        output['error'] = 'Invalid input submitted'
        httpcode = 500

    else:
        try:
            messages = []
            for (package, branch) in itertools.product(packages, branches):
                messages.append(
                    pkgdblib.pkg_change_poc(
                        session=SESSION,
                        pkg_name=package,
                        clt_name=branch,
                        pkg_poc=user_target,
                        user=flask.g.fas_user
                    )
                )
            SESSION.commit()
            output['output'] = 'ok'
            output['messages'] = messages
        except pkgdblib.PkgdbException, err:
            SESSION.rollback()
            output['output'] = 'notok'
            output['error'] = err
            httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout
