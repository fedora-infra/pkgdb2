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
ACLs
====

API for ACL management.
'''

import itertools
import flask

import pkgdb2
import pkgdb2.forms as forms
import pkgdb2.lib as pkgdblib
from pkgdb2 import SESSION, APP
from pkgdb2.api import API


## Some of the object we use here have inherited methods which apparently
## pylint does not detect.
# pylint: disable=E1101


## ACL
@API.route('/package/acl/', methods=['POST'])
@pkgdb2.packager_login_required
def api_acl_update():
    '''
    Update package ACL
    ------------------
    Update the ACL for a given package.

    ::

        /api/package/acl/

    Accepts POST queries only.

    :arg pkgname: String of the package name.
    :arg branches: List of strings with the name of the branches to change,
        update.
    :arg acl: List of strings of the ACL to change/update. Possible acl
        are: 'commit', 'build', 'watchbugzilla', 'watchcommits',
        'approveacls', 'checkout'.
    :arg acl_status: String of the type of action required. Possible status
        are: 'Approved', 'Awaiting Review', 'Denied', 'Obsolete', 'Removed'.
    :kwarg user: the name of the user that is the target of this ACL
        change/update. This will only work if: 1) you are an admin,
        2) you are changing one of your package.

    Sample response:

    ::

        {
          "output": "ok",
          "messages": ["user: $USER set acl: $ACL of package: $PACKAGE "
                       "from: $PREVIOUS_STATUS to $NEW_STATUS on branch: "
                       "$BRANCH"]
        }

        {
          "output": "notok",
          "error": ["You are not allowed to update ACLs of someone else."]
        }

    '''
    httpcode = 200
    output = {}

    status = pkgdblib.get_status(SESSION, ['pkg_acl', 'acl_status'])
    collections = pkgdblib.search_collection(
        SESSION, '*', 'Under Development')
    collections.extend(pkgdblib.search_collection(SESSION, '*', 'Active'))

    form = forms.SetAclPackageForm(
        csrf_enabled=False,
        collections=[col.branchname for col in collections],
        pkg_acl=status['pkg_acl'],
        acl_status=status['acl_status'],
    )

    if form.validate_on_submit():
        pkg_name = form.pkgname.data
        pkg_branch = form.branches.data
        pkg_acl = form.acl.data
        acl_status = form.acl_status.data
        pkg_user = form.user.data

        try:
            messages = []
            for (branch, acl) in itertools.product(pkg_branch, pkg_acl):

                acl_status2 = acl_status

                if acl_status2 == 'Awaiting Review' and \
                        acl in APP.config['AUTO_APPROVE']:
                    acl_status2 = 'Approved'

                message = pkgdblib.set_acl_package(
                    SESSION,
                    pkg_name=pkg_name,
                    pkg_branch=branch,
                    acl=acl,
                    status=acl_status2,
                    pkg_user=pkg_user,
                    user=flask.g.fas_user,
                )
                if message:
                    messages.append(message)
                else:
                    messages.append(
                        'Nothing to update on branch: %s for acl: %s' %
                        (branch, acl))
            SESSION.commit()
            output['output'] = 'ok'
            output['messages'] = messages
        except pkgdblib.PkgdbException, err:
            SESSION.rollback()
            output['output'] = 'notok'
            output['error'] = str(err)
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
@pkgdb2.packager_login_required
def api_acl_reassign():
    '''
    Reassign packages
    -----------------
    Reassign the specified packages from one user to another.

    ::

        /api/package/acl/reassign/

    Accepts POST queries only.

    :arg pkgnames: List of strings of the package name to reassign.
    :arg branches: List of strings of the branchname of the Collection on
        which to reassign the point of contact.
    :arg poc: User name of the new point of contact.
    :kwarg former_poc: Specify the former poc of the packages you want to
        reassign. This allows to specify more branches than the former_poc
        had while still only reassigning the branches the former_poc had.

    Sample response:

    ::

        {
          "output": "ok",
          "messages": ["User: $USER changed poc of package: $PACKAGE from "
                       "$PREVIOUS_POC to $NEW_POC on branch: $BRANCH"]
        }

        {
          "output": "notok",
          "error": ["You are not allowed to change the point of contact."]
        }

    '''
    httpcode = 200
    output = {}

    packages = flask.request.form.getlist('pkgnames', None)
    branches = flask.request.form.getlist('branches', None)
    former_poc = flask.request.form.get('former_poc', None)
    user_target = flask.request.form.get('poc', None)

    if not packages or not branches or not user_target:
        output['output'] = 'notok'
        output['error'] = 'Invalid input submitted'
        httpcode = 500

    else:
        messages = []
        errors = set()
        for (package, branch) in itertools.product(packages, branches):
            try:
                message = pkgdblib.update_pkg_poc(
                    session=SESSION,
                    pkg_name=package,
                    pkg_branch=branch,
                    pkg_poc=user_target,
                    former_poc=former_poc,
                    user=flask.g.fas_user
                )
                SESSION.commit()
                messages.append(message)
            except pkgdblib.PkgdbBugzillaException, err:  # pragma: no cover
                APP.logger.exception(err)
                SESSION.rollback()
                errors.add(str(err))
            except pkgdblib.PkgdbException, err:
                SESSION.rollback()
                errors.add(str(err))

        if messages:
            output['messages'] = messages
            output['output'] = 'ok'
        else:
            # If messages is empty that means that we failed all the
            # unorphans so output is `notok`, otherwise it means that we
            # succeeded at least once and thus output will be `ok` to keep
            # backward compatibility.
            httpcode = 500
            output['output'] = 'notok'

        if errors:
            errors = list(errors)
            output['error'] = errors
            if len(errors) == 1:
                output['error'] = errors.pop()

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout
