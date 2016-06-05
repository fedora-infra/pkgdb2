# -*- coding: utf-8 -*-
#
# Copyright © 2013-2016  Red Hat, Inc.
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
Packages
========

API for package management.
'''

import flask
import itertools

from math import ceil
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

import pkgdb2.lib as pkgdblib
from pkgdb2 import APP, SESSION, forms, is_admin, packager_login_required
from pkgdb2.api import API, get_limit
from pkgdb2.lib.exceptions import PkgdbException, PkgdbBugzillaException


## Some of the object we use here have inherited methods which apparently
## pylint does not detect.
# pylint: disable=E1101
## Too many variables
# pylint: disable=R0914


## Package
@API.route('/package/new/', methods=['POST'])
@is_admin
def api_package_new():
    '''
    New package
    -----------
    Create a new package.

    ::

        /api/package/new/

    Accepts POST queries only.

    :arg pkgname: String of the package name to be created.
    :arg summary: String of the summary description of the package.
    :arg description: String describing the package (same as in the
        spec file).
    :arg review_url: the URL of the package review on the bugzilla.
    :arg status: status of the package can be one of: 'Approved',
        'Awaiting Review', 'Denied', 'Obsolete', 'Removed'
    :arg branches: one or more branch names of the collection in which
        this package is added.
    :arg poc: FAS username of the point of contact
    :arg upstream_url: the URL of the upstream project
    :arg critpath: boolean specifying if the package is in the critpath
    :kwarg namespace: String of the namespace of the package to create
        (defaults to ``rpms``).
    :kwarg monitoring_status: the new release monitoring status for this
        package (defaults to ``True``, can be ``True``, ``False`` or
        ``nobuild``).
    :kwarg koschei: the koschei integration status for this package
        (defaults to ``False``, can be ``True`` or ``False``).

    Sample response:

    ::

        {
          "output": "ok",
          "messages": ["Package created"]
        }

        {
          "output": "notok",
          "error": ["You're not allowed to add a package"]
        }

    '''
    httpcode = 200
    output = {}

    collections = pkgdblib.search_collection(
        SESSION, '*', 'Under Development')
    collections.extend(pkgdblib.search_collection(SESSION, '*', 'Active'))
    pkg_status = pkgdblib.get_status(SESSION, 'pkg_status')['pkg_status']
    namespaces = pkgdblib.get_status(SESSION, 'namespaces')['namespaces']

    form = forms.AddPackageForm(
        csrf_enabled=False,
        collections=collections,
        pkg_status_list=pkg_status,
        namespaces=namespaces,
    )

    if str(form.namespace.data) in ['None', '']:
        form.namespace.data = 'rpms'

    violation = enforce_namespace_policy(form)
    if violation:
        return violation

    if form.validate_on_submit():
        namespace = form.namespace.data
        pkg_name = form.pkgname.data
        pkg_summary = form.summary.data
        pkg_description = form.description.data
        pkg_review_url = form.review_url.data
        pkg_status = form.status.data
        pkg_collection = form.branches.data
        pkg_poc = form.poc.data
        pkg_upstream_url = form.upstream_url.data
        pkg_critpath = form.critpath.data
        monitoring_status = form.monitoring_status.data
        koschei = form.koschei.data

        try:
            message = pkgdblib.add_package(
                SESSION,
                namespace=namespace,
                pkg_name=pkg_name,
                pkg_summary=pkg_summary,
                pkg_description=pkg_description,
                pkg_review_url=pkg_review_url,
                pkg_status=pkg_status,
                pkg_collection=pkg_collection,
                pkg_poc=pkg_poc,
                pkg_upstream_url=pkg_upstream_url,
                pkg_critpath=pkg_critpath,
                monitoring_status=monitoring_status,
                koschei=koschei,
                user=flask.g.fas_user
            )
            SESSION.commit()
            output['output'] = 'ok'
            output['messages'] = [message]
        except PkgdbException as err:
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


@API.route('/package/edit/', methods=['POST'])
@is_admin
def api_package_edit():
    '''
    Edit a package
    --------------
    Edit a package.

    ::

        /api/package/edit/

    Accepts POST queries only.

    :arg pkgname: String of the package name to be edited.
    :arg summary: String of the summary description of the package.
    :arg description: String describing the package (same as in the
        spec file).
    :arg review_url: the URL of the package review on the bugzilla.
    :arg status: status of the package can be one of: 'Approved',
        'Awaiting Review', 'Denied', 'Obsolete', 'Removed'
    :arg upstream_url: the URL of the upstream project
    :kwarg namespace: String of the namespace of the package to be edited
        (defaults to ``rpms``).

    Sample response:

    ::

        {
          "output": "ok",
          "messages": ["Package edited"]
        }

        {
          "output": "notok",
          "error": ["You're not allowed to edit this package"]
        }

    '''
    httpcode = 200
    output = {}

    pkg_status = pkgdblib.get_status(SESSION, 'pkg_status')['pkg_status']
    namespaces = pkgdblib.get_status(SESSION, 'namespaces')['namespaces']

    form = forms.EditPackageForm(
        csrf_enabled=False,
        pkg_status_list=pkg_status,
        namespaces=namespaces,
    )

    if str(form.namespace.data) in ['None', '']:
        form.namespace.data = 'rpms'

    violation = enforce_namespace_policy(form)
    if violation:
        return violation

    if form.validate_on_submit():
        namespace = form.namespace.data
        pkg_name = form.pkgname.data

        package = None
        try:
            package = pkgdblib.search_package(
                SESSION, namespace, pkg_name, limit=1)[0]
        except (NoResultFound, IndexError):
            SESSION.rollback()
            output['output'] = 'notok'
            output['error'] = 'No package of this name found'
            httpcode = 500

        if package:
            pkg_summary = form.summary.data
            pkg_description = form.description.data
            pkg_review_url = form.review_url.data
            pkg_status = form.status.data
            if pkg_status == 'None':
                pkg_status = None
            pkg_upstream_url = form.upstream_url.data

            try:
                message = pkgdblib.edit_package(
                    SESSION,
                    package,
                    pkg_name=pkg_name,
                    pkg_summary=pkg_summary,
                    pkg_description=pkg_description,
                    pkg_review_url=pkg_review_url,
                    pkg_upstream_url=pkg_upstream_url,
                    pkg_status=pkg_status,
                    user=flask.g.fas_user
                )
                SESSION.commit()
                output['output'] = 'ok'
                output['messages'] = [message]
            except PkgdbException as err:  # pragma: no cover
                # We can only reach here in two cases:
                # 1) the user is not an admin, but that's taken care of
                #    by the decorator
                # 2) we have a SQLAlchemy problem when storing the info
                #    in the DB which we cannot test
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


@API.route('/package/orphan/', methods=['POST'])
@packager_login_required
def api_package_orphan():
    '''
    Orphan package
    --------------
    Orphan one or more packages.

    ::

        /api/package/orphan/

    Accepts POST queries only.

    :arg pkgnames: Comma separated list of string of the packages name.
    :arg branches: Comma separated list of string of the branches name in
        which these packages will be orphaned.
    :kwarg namespace: The namespace of the packages (can only process one
        namespace at a time), defaults to ``rpms``.
    :kwarg former_poc: Use to restrict orphaning the branches maintained by
        a specific user while providing a broader list of branches.


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

    pkgnames = flask.request.form.getlist('pkgnames', None)
    branches = flask.request.form.getlist('branches', None)
    namespace = flask.request.form.get('namespace', 'rpms')
    former_poc = flask.request.form.get('former_poc', None)

    if pkgnames and branches:
        messages = []
        errors = set()
        for pkg_name, pkg_branch in itertools.product(
                pkgnames, branches):
            try:
                message = pkgdblib.update_pkg_poc(
                    SESSION,
                    namespace=namespace,
                    pkg_name=pkg_name,
                    pkg_branch=pkg_branch,
                    pkg_poc='orphan',
                    former_poc=former_poc,
                    user=flask.g.fas_user,
                )

                messages.append(message)
                SESSION.commit()
            except PkgdbException as err:
                SESSION.rollback()
                errors.add(str(err))

        if messages:
            output['messages'] = messages
            output['output'] = 'ok'
        else:
            # If messages is empty that means that we failed all the orphans
            # so output is `notok`, otherwise it means that we succeeded at
            # least once and thus output will be `ok` to keep backward
            # compatibility.
            httpcode = 500
            output['output'] = 'notok'

        if errors:
            errors = list(errors)
            output['error'] = errors
            if len(errors) == 1:
                output['error'] = errors.pop()

    else:
        output['output'] = 'notok'
        output['error'] = 'Invalid input submitted'
        detail = []
        if not pkgnames:
            detail.append('pkgnames: This field is required.')
        if not branches:
            detail.append('branches: This field is required.')
        if detail:
            output['error_detail'] = detail
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/package/unorphan/', methods=['POST'])
@packager_login_required
def api_package_unorphan():
    '''
    Unorphan packages
    -----------------
    Unorphan one or more packages.

    ::

        /api/package/unorphan/

    Accepts POST queries only.

    :arg pkgnames: Comma separated list of string of the packages name.
    :arg branches: Comma separated list of string of the branches name in
        which these packages will be unorphaned.
    :arg poc: String of the name of the user taking ownership of
        this package. If you are not an admin, this name must be None.
    :kwarg namespace: The namespace of the packages (can only process one
        namespace at a time), defaults to ``rpms``.

    Sample response:

    ::

        {
          "output": "ok",
          "messages": ["Package $PACKAGE has been unorphaned for $BRANCH "
                       "by $USER"]
        }

        {
          "output": "notok",
          "error": ["You must be a packager to take a package."]
        }

    '''
    httpcode = 200
    output = {}

    pkgnames = flask.request.form.getlist('pkgnames', None)
    branches = flask.request.form.getlist('branches', None)
    namespace = flask.request.form.get('namespace', 'rpms')
    poc = flask.request.form.get('poc', None)

    if pkgnames and branches and poc:
        messages = []
        errors = set()
        for pkg_name, pkg_branch in itertools.product(
                pkgnames, branches):
            try:
                message = pkgdblib.unorphan_package(
                    session=SESSION,
                    namespace=namespace,
                    pkg_name=pkg_name,
                    pkg_branch=pkg_branch,
                    pkg_user=poc,
                    user=flask.g.fas_user,
                )
                messages.append(message)
                SESSION.commit()
            except PkgdbBugzillaException as err:  # pragma: no cover
                APP.logger.exception(err)
                SESSION.rollback()
                errors.add(str(err))
            except PkgdbException as err:
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
    else:
        output['output'] = 'notok'
        output['error'] = 'Invalid input submitted'
        detail = []
        if not pkgnames:
            detail.append('pkgnames: This field is required.')
        if not branches:
            detail.append('branches: This field is required.')
        if not poc:
            detail.append('poc: This field is required.')
        if detail:
            output['error_detail'] = detail
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/package/retire/', methods=['POST'])
@packager_login_required
def api_package_retire():
    '''
    Retire packages
    ---------------
    Retire one or more packages.

    ::

        /api/package/retire/

    Accepts POST queries only.

    :arg pkgnames: Comma separated list of string of the packages name.
    :arg branches: Comma separated list of string of the branches name in
        which these packages will be retire.
    :kwarg namespace: the namespace of the package to retire.

    Sample response:

    ::

        {
          "output": "ok",
          "messages": ["user: $USER updated package: $PACKAGE status from: "
                       "$PREVIOUS_STATUS to $NEW_STATUS on branch $BRANCH"]
        }

        {
          "output": "notok",
          "error": ["You are not allowed to retire the package: $PACKAGE "
                    "on branch $BRANCH."]
        }

    '''
    httpcode = 200
    output = {}

    pkgnames = flask.request.form.getlist('pkgnames', None)
    branches = flask.request.form.getlist('branches', None)
    namespace = flask.request.form.get('namespace', 'rpms')

    if pkgnames and branches:
        try:
            messages = []
            errors = set()
            for pkg_name, pkg_branch in itertools.product(
                    pkgnames, branches):
                message = pkgdblib.update_pkg_status(
                    SESSION,
                    namespace=namespace,
                    pkg_name=pkg_name,
                    pkg_branch=pkg_branch,
                    status='Retired',
                    user=flask.g.fas_user,
                )
                messages.append(message)
            SESSION.commit()
        except PkgdbException as err:
            SESSION.rollback()
            errors.add(str(err))

        if messages:
            output['messages'] = messages
            output['output'] = 'ok'
        else:
            # If messages is empty that means that we failed all the
            # retire so output is `notok`, otherwise it means that we
            # succeeded at least once and thus output will be `ok` to keep
            # backward compatibility.
            httpcode = 500
            output['output'] = 'notok'

        if errors:
            errors = list(errors)
            output['error'] = errors
            if len(errors) == 1:
                output['error'] = errors.pop()

    else:
        output['output'] = 'notok'
        output['error'] = 'Invalid input submitted'
        detail = []
        if not pkgnames:
            detail.append('pkgnames: This field is required.')
        if not branches:
            detail.append('branches: This field is required.')
        if detail:
            output['error_detail'] = detail
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/package/unretire/', methods=['POST'])
@is_admin
def api_package_unretire():
    '''
    Unretire packages
    -----------------
    Un-retire one or more packages.

    ::

        /api/package/unretire/

    Accepts POST queries only.

    :arg pkgnames: Comma separated list of the packages names.
    :arg branches: Comma separated list of string of the branches names in
        which these packages will be un-deprecated.
    :kwarg namespace: The namespace of the package to unretire (can only
        process one namespace at a time), defaults to ``rpms``.


    Sample response:

    ::

        {
          "output": "ok",
          "messages": ["user: $USER updated package: $PACKAGE status from: "
                       "$PREVIOUS_STATUS to $NEW_STATUS on branch $BRANCH"]
        }

        {
          "output": "notok",
          "error": ["You are not allowed to update the status of "
                    "the package: $PACKAGE on branch $BRANCH to $STATUS."]
        }

    '''
    httpcode = 200
    output = {}

    pkgnames = flask.request.form.getlist('pkgnames', None)
    branches = flask.request.form.getlist('branches', None)
    namespace = flask.request.form.get('namespace', 'rpms')

    if pkgnames and branches:
        try:
            messages = []
            for pkg_name, pkg_branch in itertools.product(
                    pkgnames, branches):
                message = pkgdblib.update_pkg_status(
                    SESSION,
                    namespace=namespace,
                    pkg_name=pkg_name,
                    pkg_branch=pkg_branch,
                    status='Approved',
                    user=flask.g.fas_user,
                )
                messages.append(message)
            SESSION.commit()
            output['output'] = 'ok'
            output['messages'] = messages
        except PkgdbException as err:
            SESSION.rollback()
            output['output'] = 'notok'
            output['error'] = str(err)
            httpcode = 500
    else:
        output['output'] = 'notok'
        output['error'] = 'Invalid input submitted'
        detail = []
        if not pkgnames:
            detail.append('pkgnames: This field is required.')
        if not branches:
            detail.append('branches: This field is required.')
        if detail:
            output['error_detail'] = detail
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/package/')
@API.route('/package')
@API.route('/package/<pkgname>/')
@API.route('/package/<pkgname>')
@API.route('/package/<namespace>/<pkgname>/')
@API.route('/package/<namespace>/<pkgname>')
def api_package_info(namespace=None, pkgname=None):
    '''
    Package information
    -------------------
    Return information about a specific package.

    ::

        /api/package/<pkg_name>/

        /api/package/?pkgname=<pkg_name>

    Accepts GET queries only

    :arg pkgname: The name of the package to retrieve the information of.
    :kwarg branches: Restricts the package information to one or more
        collection (branches).
    :kwarg eol: a boolean to specify whether to include results for
        EOL collections or not. Defaults to False.
        If True, it will return results for all collections (including EOL).
        If False, it will return results only for non-EOL collections.
    :kwarg acls: a boolean to specify whether to include the ACLs in the
        results. Defaults to True.
        If True, it will include the ACL of the package in the collection.
        If False, it will not include the ACL of the package in the
        collection.

    Sample response:

    ::

        {
          "output": "ok",
          "packages": [
            {
              "status": "Approved",
              "point_of_contact": "pingou",
              "critpath": False,
              "package": {
                "status": "Approved",
                "upstream_url": null,
                "description": "Guake is a drop-down terminal for Gnome "
                             "Desktop Environment, so you just need to "
                             "press a key to invoke him,and press again "
                             "to hide."
                "summary": "Drop-down terminal for GNOME",
                "creation_date": 1385365548.0,
                "review_url": null,
                "name": "guake"
              },
              "collection": {
                "status": "Under Development",
                "branchname": "master",
                "version": "devel",
                "name": "Fedora"
              },
              "acls": [
                {
                  "status": "Approved",
                  "fas_name": "pingou",
                  "acl": "watchcommits"
                },
                {
                  "status": "Approved",
                  "fas_name": "pingou",
                  "acl": "watchbugzilla"
                },
                {
                  "status": "Approved",
                  "fas_name": "pingou",
                  "acl": "commit"
                },
                {
                  "status": "Approved",
                  "fas_name": "pingou",
                  "acl": "approveacls"
                },
                {
                  "status": "Obsolete",
                  "fas_name": "maxamillion",
                  "acl": "watchcommits"
                },
                {
                  "status": "Obsolete",
                  "fas_name": "maxamillion",
                  "acl": "watchbugzilla"
                },
                {
                  "acl": "commit",
                  "fas_name": "group::provenpackager",
                  "status": "Approved"
                }
              ],
              "status_change": 1385366044.0
            },
            ...
          ]
        }

    '''
    httpcode = 200
    output = {}

    pkg_name = flask.request.args.get('pkgname', pkgname)
    namespace = flask.request.args.get('namespace', namespace) or 'rpms'
    branches = flask.request.args.getlist('branches', None)
    eol = flask.request.args.get('eol', False)
    acls = flask.request.args.get('acls', True)
    if str(acls).lower() in ['0', 'false']:
        acls = False

    try:
        packages = pkgdblib.get_acl_package(
            SESSION,
            pkg_name=pkg_name,
            namespace=namespace,
            pkg_clt=branches,
            eol=eol,
        )
        if not packages:
            output['output'] = 'notok'
            output['error'] = 'No package found on these branches: %s' \
                % ', '.join(branches)
            httpcode = 404
        else:
            output['output'] = 'ok'
            output['packages'] = [
                pkg.to_json(not_provenpackager=APP.config.get(
                    'PKGS_NOT_PROVENPACKAGER'), acls=acls)
                for pkg in packages]
    except NoResultFound:
        output['output'] = 'notok'
        output['error'] = 'Package: %s/%s not found' % (namespace, pkg_name)
        httpcode = 404

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/packages/')
@API.route('/packages')
@API.route('/packages/<pattern>/')
@API.route('/packages/<pattern>')
@API.route('/package/<namespace>/<pattern>/')
@API.route('/package/<namespace>/<pattern>')
def api_package_list(namespace=None, pattern=None):
    '''
    List packages
    -------------
    List packages based on a pattern. If no pattern is provided, return all
    the package.

    ::

        /api/packages/<pattern>/

        /api/packages/?pattern=<pattern>

        /api/packages/?pattern=<pattern>&pattern=<pattern2>

    Accepts GET queries only

    :arg pattern: Pattern to list packages from their name. Use ``*`` to
        match multiple packages by their name.
        Multiple patterns can be provided if you wish to search for multiple
        packages at once.
    :arg branches: List of string of the branches name in which these
        packages will be searched.
    :arg poc: String of the user name to to which restrict the search.
    :arg orphaned: Boolean to retrict the search to orphaned packages.
    :arg critpath: Boolean to retrict the search to critpath packages.
        Defaults to None which means results include both critpath and
        non-critpath packages.
    :arg status: Allows to filter packages based on their status: Approved,
        Orphaned, Retired, Removed.
    :arg acls: Boolean use to retrieve the acls in addition of the package
        information. Beware that this may reduce significantly the response
        time, it is advise to use it in combinaition with a specifir branch.
        Defaults to False.
    :kwarg eol: a boolean to specify whether to include results for
        EOL collections or not. Defaults to False.
        If True, it will return results for all collections (including EOL).
        If False, it will return results only for non-EOL collections.
    :kwarg limit: An integer to limit the number of results, defaults to
        250, maximum is 500.
    :kwarg page: The page number to return (useful in combination to limit).
    :kwarg count: A boolean to return the number of packages instead of the
        list. Defaults to False.

    *Results are paginated*

    Sample response:

    ::

        /api/packages/guak*

        {
          "output": "ok",
          "packages": [
            {
              "status": "Approved",
              "upstream_url": null,
              "description": "Guake is a drop-down terminal for Gnome "
                             "Desktop Environment, so you just need to "
                             "press a key to invoke him,and press again"
                             " to hide."
              "summary": "Drop-down terminal for GNOME",
               "creation_date": 1384775354.0,
                "review_url": null,
                "name": "guake"
            }
          ],
          "page_total": 1,
          "page": 1
        }

        /api/packages/?pattern=guake&pattern=tilda

        {
          "output": "ok",
          "packages": [
            {
              "acls": [],
              "creation_date": 1400063778.0,
              "description": "Tilda is a Linux terminal taking after the "
                             "likeness of many classic terminals from first "
                             "person shooter games, Quake, Doom and Half-Life "
                             "(to name a few), where the terminal has no "
                             "border and is hidden from the desktop until "
                             "a key is pressed.",
              "koschei_monitor": false,
              "monitor": false,
              "name": "tilda",
              "review_url": null,
              "status": "Approved",
              "summary": "A Gtk based drop down terminal for Linux and Unix",
              "upstream_url": "https://github.com/lanoxx/tilda"
            },
            {
              "acls": [],
              "creation_date": 1400063778.0,
              "description": "Guake is a drop-down terminal for Gnome "
                             "Desktop Environment, so you just need to "
                             "press a key to invoke him, and press again "
                             "to hide.",
              "koschei_monitor": true,
              "monitor": true,
              "name": "guake",
              "review_url": null,
              "status": "Approved",
              "summary": "Drop-down terminal for GNOME",
              "upstream_url": "http://www.guake.org/"
            }
          ],
          "page": 1,
          "page_total": 1
        }

        /api/packages/cl*?status=Orphaned&branches=f20&acls=true

        {
          "output": "ok",
          "packages": [
            {
              "status": "Approved",
              "upstream_url": null,
              "description": "clive is a video extraction tool for "
                             "user-uploaded video hosts such as Youtube,"
                             "Google Video, Dailymotion, Guba, Metacafe "
                             "and Sevenload.It can be chained with 3rd "
                             "party tools for subsequent video re-encoding"
                             " and and playing.",
              "summary": "Video extraction tool for user-uploaded video hosts",
              "acls": [
                {
                  "status": "Retired",
                  "point_of_contact": "orphan",
                  "status_change": 1385363055.0,
                  "collection": {
                    "status": "Active",
                    "branchname": "f20",
                    "version": "20",
                    "name": "Fedora"
                  },
                  "package": null
                }
              ],
              "creation_date": 1385361948.0,
              "review_url": null,
              "name": "clive"
            }
          ],
          "page_total": 1,
          "page": 1
        }

    .. note:: the ``status_change`` and ``create_date`` fields are both
            timestamps expressed in
            `Unix TIME <https://en.wikipedia.org/wiki/Unix_time>`_

    '''
    httpcode = 200
    output = {}

    patterns = flask.request.args.getlist('pattern')
    if not patterns and not pattern:
        patterns = ['*']
    elif not patterns and pattern:
        patterns = [pattern]

    namespace = flask.request.args.get('namespace', namespace) or 'rpms'
    branches = flask.request.args.getlist('branches', None)
    poc = flask.request.args.get('poc', None)
    orphaned = flask.request.args.get('orphaned', None)
    if str(orphaned).lower() in ['0', 'false']:
        orphaned = False
    elif orphaned is not None:
        orphaned = bool(orphaned)

    critpath = flask.request.args.get('critpath', None)
    if critpath and str(critpath).lower() in ['0', 'false']:
        critpath = False
    elif critpath:
        critpath = True
    acls = flask.request.args.get('acls', False)
    if str(acls).lower() in ['0', 'false']:
        acls = False
    else:
        acls = True

    statuses = flask.request.args.getlist('status', None)
    eol = flask.request.args.get('eol', False)
    page = flask.request.args.get('page', 1)
    limit = get_limit()
    count = flask.request.args.get('count', False)
    try:
        tmp_branches = branches
        if not branches:
            tmp_branches = [None]
        tmp_statuses = statuses
        if not statuses:
            tmp_statuses = [None]

        if count:
            packages = 0
            for status, branch, pattern in itertools.product(
                    tmp_statuses, tmp_branches, patterns):
                packages += pkgdblib.search_package(
                    SESSION,
                    namespace=namespace,
                    pkg_name=pattern,
                    pkg_branch=branch,
                    pkg_poc=poc,
                    orphaned=orphaned,
                    critpath=critpath,
                    status=status,
                    eol=eol,
                    page=page,
                    limit=limit,
                    count=count,
                )

            output['output'] = 'ok'
            output['packages'] = packages
            output['page'] = 1
            output['page_total'] = 1
        else:
            packages = set()
            packages_count = 0
            for status, branch, pattern in itertools.product(
                    tmp_statuses, tmp_branches, patterns):
                packages.update(
                    pkgdblib.search_package(
                        SESSION,
                        namespace=namespace,
                        pkg_name=pattern,
                        pkg_branch=branch,
                        pkg_poc=poc,
                        orphaned=orphaned,
                        critpath=critpath,
                        status=status,
                        eol=eol,
                        page=page,
                        limit=limit,
                        count=count,
                    )
                )
                packages_count += pkgdblib.search_package(
                    SESSION,
                    namespace=namespace,
                    pkg_name=pattern,
                    pkg_branch=branch,
                    pkg_poc=poc,
                    orphaned=orphaned,
                    critpath=critpath,
                    status=status,
                    eol=eol,
                    page=page,
                    limit=limit,
                    count=True,
                )

            if not packages:
                output['output'] = 'notok'
                output['packages'] = []
                output['error'] = 'No packages found for these parameters'
                httpcode = 404
            else:
                output['packages'] = [
                    pkg.to_json(acls=acls, collection=branches, package=False)
                    for pkg in packages
                ]
                output['output'] = 'ok'
                output['page'] = int(page)
                output['page_total'] = int(ceil(packages_count / float(limit)))

    except PkgdbException as err:
        SESSION.rollback()
        output['output'] = 'notok'
        output['error'] = str(err)
        httpcode = 500

    if 'page_total' not in output:
        output['page'] = 1
        output['page_total'] = 1

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/package/critpath/', methods=['POST'])
@is_admin
def api_package_critpath():
    '''
    Critpath status
    ---------------
    Update the critpath status of a package.

    ::

        /api/package/critpath/

    Accepts POST queries only.

    :arg pkgnames: A list of string of the packages name.
    :arg branches: A list of string of the branches name in which the
        critpath status will be updated.
    :kwarg namespace: The namespace of the packages (defaults to ``rpms``).
    :kwarg critpath: A boolean of the critpath status. Defaults to False.


    Sample response:

    ::

        {
            "output": "ok",
            "messages": [
                'guake: critpath updated on master to True',
                'guake: critpath updated on f18 to True'
            ]
        }

        {
          "output": "notok",
          "error": "No package found by this name"
        }

     '''
    httpcode = 200
    output = {}

    pkgnames = flask.request.form.getlist('pkgnames', None)
    namespace = flask.request.form.get('namespace', 'rpms')
    branches = flask.request.form.getlist('branches', None)
    critpath = flask.request.form.get('critpath', False)
    if str(critpath).lower() in ['1', 'true']:
        critpath = True
    elif str(critpath).lower() in ['0', 'false']:
        critpath = False

    if pkgnames and branches and namespace:
        try:
            messages = []
            for pkg_name, pkg_branch in itertools.product(
                    pkgnames, branches):
                message = pkgdblib.set_critpath_packages(
                    SESSION,
                    namespace=namespace,
                    pkg_name=pkg_name,
                    pkg_branch=pkg_branch,
                    critpath=critpath,
                    user=flask.g.fas_user,
                )
                if message:
                    messages.append(message)
            if messages:
                SESSION.commit()
                output['output'] = 'ok'
                output['messages'] = messages
            else:
                output['output'] = 'notok'
                output['error'] = 'Nothing to update'
                httpcode = 500
        except PkgdbException as err:
            SESSION.rollback()
            output['output'] = 'notok'
            output['error'] = str(err)
            httpcode = 500
    else:
        output['output'] = 'notok'
        output['error'] = 'Invalid input submitted'
        detail = []
        if not pkgnames:
            detail.append('pkgnames: This field is required.')
        if not branches:
            detail.append('branches: This field is required.')
        if not namespace:
            detail.append('namespace: This field is required.')
        if detail:
            output['error_detail'] = detail
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/package/<package>/monitor/<status>', methods=['POST'])
@API.route('/package/<namespace>/<package>/monitor/<status>', methods=['POST'])
@packager_login_required
def api_monitor_package(package, status, namespace='rpms'):
    '''
    Monitoring status
    -----------------
    Set the monitor status on the specified package.

    ::

        /api/package/<package>/monitor/<status>

    Accepts POST queries only.

    :arg package: The name of the package to update.
    :arg status: The status to set to the monitoring flag, can be either
        ``1`` or ``true`` for setting full monitoring, ``nobuild`` to set
        the monitoring but block scratch builds or ``0`` or ``false`` to
        stop the monitoring entirely.
    :kwarg namespace: The namespace of the package to update
        (default to ``rpms``).


    Sample response:

    ::

        {
            "output": "ok",
            "messages": "Monitoring status of guake set to True"
        }

        {
          "output": "notok",
          "error": "No package found by this name"
        }

     '''

    httpcode = 200
    output = {}
    if str(status).lower() in ['1', 'true']:
        status = True
    elif str(status).lower() == 'nobuild':
        status = 'nobuild'
    else:
        status = False

    try:
        msg = pkgdblib.set_monitor_package(
            SESSION, namespace, package, status, flask.g.fas_user)
        SESSION.commit()
        output['output'] = 'ok'
        output['messages'] = msg
    except PkgdbException as err:
        SESSION.rollback()
        output['output'] = 'notok'
        output['error'] = str(err)
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/package/<package>/koschei/<status>', methods=['POST'])
@API.route('/package/<namespace>/<package>/koschei/<status>', methods=['POST'])
@packager_login_required
def api_koschei_package(package, status, namespace='rpms'):
    '''
    Koschei monitoring status
    -------------------------
    Set the monitor status for koschei on the specified package.

    ::

        /api/package/<namespace>/<package>/koschei/<status>

    Accepts POST queries only.

    :arg package: The name of the package to update.
    :arg status: The status to set to the koschei monitoring flag, can be
        either ``1`` or ``true`` or ``0`` or ``false`` to stop the
        monitoring.
    :kwarg namespace: The namespace of the package to update
        (default to ``rpms``).


    Sample response:

    ::

        {
            "output": "ok",
            "messages": "Koschei monitoring status of guake set to True"
        }

        {
          "output": "notok",
          "error": "No package found by this name"
        }

     '''

    httpcode = 200
    output = {}
    if str(status).lower() in ['1', 'true']:
        status = True
    else:
        status = False

    try:
        msg = pkgdblib.set_koschei_monitor_package(
            SESSION, namespace, package, status, flask.g.fas_user)
        SESSION.commit()
        output['output'] = 'ok'
        output['messages'] = msg
    except PkgdbException as err:
        SESSION.rollback()
        output['output'] = 'notok'
        output['error'] = str(err)
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/request/package', methods=['POST'])
def api_package_request():
    '''
    New package request
    -------------------
    Request for an admin to include a new package in pkgdb.

    ::

        /api/request/package

    Accepts POST queries only.

    :arg pkgname: The name of the package to create.
    :arg summary: The summary of the package.
    :arg description: The description of the package.
    :arg upstream_url: The URL of the upstream website of the package.
    :arg review_url: The URL where the package review was done.
    :arg branches: The list of branches desired for this package.
        Note: if the ``master`` isn't requested, it will be added
        automatically.
    :kwarg namespace: The namespace of the package to create
        (defaults to ``rpms``).
    :kwarg monitoring_status: the new release monitoring status for this
        package (defaults to ``True``, can be ``True``, ``False`` or
        ``nobuild``).
    :kwarg koschei: the koschei integration status for this package
        (defaults to ``False``, can be ``True`` or ``False``).


    Sample response:

    ::

        {
          "output": "ok",
          "messages": [
            'user: pingou request package: guake on branch master',
            'user: pingou request package: guake on branch f18',
          ]
        }

        {
          "output": "notok",
          'error': 'User "pingou" is not in the packager group',
        }

        {
          "error": "Invalid input submitted",
          "error_detail": [
            "branches: 'foobar' is not a valid choice for this field",
            "review_url: This field is required."
          ],
          "output": "notok"
        }

    '''
    httpcode = 200
    output = {}
    collections = pkgdblib.search_collection(
        SESSION, '*', 'Under Development')
    collections.reverse()
    active_collections = pkgdblib.search_collection(SESSION, '*', 'Active')
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

    namespaces = pkgdblib.get_status(SESSION, 'namespaces')['namespaces']
    form = forms.RequestPackageForm(
        csrf_enabled=False,
        collections=collections,
        namespaces=namespaces,
    )

    if str(form.namespace.data) in ['None', '']:
        form.namespace.data = 'rpms'

    violation = enforce_namespace_policy(form)
    if violation:
        return violation

    if form.validate_on_submit():
        pkg_name = form.pkgname.data
        pkg_summary = form.summary.data
        pkg_description = form.description.data
        pkg_review_url = form.review_url.data
        pkg_status = 'Approved'
        pkg_critpath = False
        pkg_collection = form.branches.data
        if not 'master' in pkg_collection:
            pkg_collection.append('master')
        pkg_poc = flask.g.fas_user.username
        pkg_upstream_url = form.upstream_url.data
        pkg_namespace = form.namespace.data
        monitoring_status = form.monitoring_status.data or True
        koschei = form.koschei.data or False

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
                    pkg_namespace=pkg_namespace,
                    monitoring_status=monitoring_status,
                    koschei=koschei,
                    user=flask.g.fas_user,
                )
                if message:
                    messages.append(message)
            SESSION.commit()
            output['output'] = 'ok'
            output['messages'] = messages
        except PkgdbException as err:
            SESSION.rollback()
            output['output'] = 'notok'
            output['error'] = str(err)
            httpcode = 400
    else:
        output['output'] = 'notok'
        output['error'] = 'Invalid input submitted'
        if form.errors:
            detail = []
            for error in form.errors:
                detail.append('%s: %s' % (error,
                              '; '.join(form.errors[error])))
            output['error_detail'] = detail
        httpcode = 400

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/request/branch/<package>', methods=['POST'])
@API.route('/request/branch/<namespace>/<package>', methods=['POST'])
def api_branch_request(package, namespace='rpms'):
    '''
    New branch request
    ------------------
    Request a new branch for package in pkgdb.

    ::

        /api/request/branch/<namespace>/<package>

    Accepts POST queries only.

    :arg package: The name of the package
    :arg branches: The list of branches desired for this package.
    :arg namespace: The namespace of the package
        (default to ``rpms``).


    Sample response:

    ::

        {
          'messages': [
            'Branch f17 created for user pingou',
          ],
          'output': 'ok'
        }

        {
          "messages": [
            "Branch el6 requested for user pingou"
          ],
          "output": "ok"
        }

        {
          "output": "notok",
          'error': 'User "pingou" is not in the packager group',
        }

        {
          "error": "Invalid input submitted",
          "error_detail": [
            "branches: 'foobar' is not a valid choice for this field",
          ],
          "output": "notok"
        }

    '''
    httpcode = 200
    output = {}
    try:
        package_acl = pkgdblib.get_acl_package(SESSION, namespace, package)
        package = pkgdblib.search_package(
            SESSION, namespace, package, limit=1)[0]
    except (NoResultFound, IndexError):
        SESSION.rollback()
        output['output'] = 'notok'
        output['error'] = 'No package found: %s/%s' % (namespace, package)
        httpcode = 404
    else:

        branches = [
            pkg.collection.branchname
            for pkg in package_acl
            if pkg.collection.status != 'EOL'
        ]

        collections = pkgdblib.search_collection(
            SESSION, '*', 'Under Development')
        collections.extend(pkgdblib.search_collection(
            SESSION, '*', 'Active'))
        branches_possible = [
            collec.branchname
            for collec in collections
            if collec.branchname not in branches]

        form = forms.BranchForm(
            collections=branches_possible,
            csrf_enabled=False,
        )

        if form.validate_on_submit():
            try:
                messages = []
                for branch in form.branches.data:
                    msg = pkgdblib.add_new_branch_request(
                        session=SESSION,
                        namespace=namespace,
                        pkg_name=package.name,
                        clt_to=branch,
                        user=flask.g.fas_user)
                    if msg:
                        messages.append(msg)
                SESSION.commit()
                output['output'] = 'ok'
                output['messages'] = messages
            except PkgdbException as err:  # pragma: no cover
                SESSION.rollback()
                output['output'] = 'notok'
                output['error'] = str(err)
                httpcode = 400
            except SQLAlchemyError as err:  # pragma: no cover
                SESSION.rollback()
                APP.logger.exception(err)
                output['output'] = 'notok'
                output['error'] = 'Could not save the request to the '\
                    'database for branch: %s' % branch
                httpcode = 400
        else:
            output['output'] = 'notok'
            output['error'] = 'Invalid input submitted'
            if form.errors:
                detail = []
                for error in form.errors:
                    detail.append('%s: %s' % (error,
                                  '; '.join(form.errors[error])))
                output['error_detail'] = detail
            httpcode = 400

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


def enforce_namespace_policy(form):
    """ Check that a package change requests meets with the policy.

    Only some collections are allowed for some namespaces
    https://github.com/fedora-infra/pkgdb2/issues/341
    """

    namespace_policy = APP.config.get('PKGDB2_NAMESPACE_POLICY')
    namespace = form.namespace.data
    if namespace in namespace_policy:
        policy = namespace_policy[namespace]
        culprits = [b for b in form.branches.data if b not in policy]
        if len(culprits) > 0:
            jsonout = flask.jsonify({
                'output': 'notok',
                'error': "%s not allowed by namespace policy %s: %s" % (
                    ", ".join(culprits), namespace, ", ".join(policy)),
            })
            jsonout.status_code = 400
            return jsonout

    # No problems found...
    return None
