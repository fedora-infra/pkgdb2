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
Packages
========

API for package management.
'''

import flask
import itertools

from math import ceil
from sqlalchemy.orm.exc import NoResultFound

import pkgdb2.lib as pkgdblib
from pkgdb2 import APP, SESSION, forms, is_admin, packager_login_required
from pkgdb2.api import API, get_limit


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

    Accept POST queries only.

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

    form = forms.AddPackageForm(
        csrf_enabled=False,
        collections=collections,
        pkg_status_list=pkg_status,
    )
    if form.validate_on_submit():
        pkg_name = form.pkgname.data
        pkg_summary = form.summary.data
        pkg_description = form.description.data
        pkg_review_url = form.review_url.data
        pkg_status = form.status.data
        pkg_collection = form.branches.data
        pkg_poc = form.poc.data
        pkg_upstream_url = form.upstream_url.data
        pkg_critpath = form.critpath.data

        try:
            message = pkgdblib.add_package(
                SESSION,
                pkg_name=pkg_name,
                pkg_summary=pkg_summary,
                pkg_description=pkg_description,
                pkg_review_url=pkg_review_url,
                pkg_status=pkg_status,
                pkg_collection=pkg_collection,
                pkg_poc=pkg_poc,
                pkg_upstream_url=pkg_upstream_url,
                pkg_critpath=pkg_critpath,
                user=flask.g.fas_user
            )
            SESSION.commit()
            output['output'] = 'ok'
            output['messages'] = [message]
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


@API.route('/package/edit/', methods=['POST'])
@is_admin
def api_package_edit():
    '''
Edit a package
--------------
    Edit a package.

    ::

        /api/package/edit/

    Accept POST queries only.

    :arg pkgname: String of the package name to be created.
    :arg summary: String of the summary description of the package.
    :arg description: String describing the package (same as in the
        spec file).
    :arg review_url: the URL of the package review on the bugzilla.
    :arg status: status of the package can be one of: 'Approved',
        'Awaiting Review', 'Denied', 'Obsolete', 'Removed'
    :arg upstream_url: the URL of the upstream project

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

    form = forms.EditPackageForm(
        csrf_enabled=False,
        pkg_status_list=pkg_status,
    )
    if form.validate_on_submit():
        pkg_name = form.pkgname.data

        package = None
        try:
            package = pkgdblib.search_package(SESSION, pkg_name, limit=1)[0]
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
            except pkgdblib.PkgdbException, err:  # pragma: no cover
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

    Accept POST queries only.

    :arg pkgnames: Comma separated list of string of the packages name.
    :arg branches: Comma separated list of string of the branches name in
        which these packages will be orphaned.


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

    if pkgnames and branches:
        messages = []
        errors = set()
        for pkg_name, pkg_branch in itertools.product(
                pkgnames, branches):
            try:
                message = pkgdblib.update_pkg_poc(
                    SESSION,
                    pkg_name=pkg_name,
                    pkg_branch=pkg_branch,
                    pkg_poc='orphan',
                    user=flask.g.fas_user,
                )

                messages.append(message)
                SESSION.commit()
            except pkgdblib.PkgdbException, err:
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

    Accept POST queries only.

    :arg pkgnames: Comma separated list of string of the packages name.
    :arg branches: Comma separated list of string of the branches name in
        which these packages will be unorphaned.
    :arg poc: String of the name of the user taking ownership of
        this package. If you are not an admin, this name must be None.

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
    poc = flask.request.form.get('poc', None)

    if pkgnames and branches and poc:
        messages = []
        errors = set()
        for pkg_name, pkg_branch in itertools.product(
                pkgnames, branches):
            try:
                message = pkgdblib.unorphan_package(
                    session=SESSION,
                    pkg_name=pkg_name,
                    pkg_branch=pkg_branch,
                    pkg_user=poc,
                    user=flask.g.fas_user
                )
                messages.append(message)
                SESSION.commit()
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

    Accept POST queries only.

    :arg pkgnames: Comma separated list of string of the packages name.
    :arg branches: Comma separated list of string of the branches name in
        which these packages will be retire.

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

    if pkgnames and branches:
        try:
            messages = []
            errors = set()
            for pkg_name, pkg_branch in itertools.product(
                    pkgnames, branches):
                message = pkgdblib.update_pkg_status(
                    SESSION,
                    pkg_name=pkg_name,
                    pkg_branch=pkg_branch,
                    status='Retired',
                    user=flask.g.fas_user,
                )
                messages.append(message)
            SESSION.commit()
        except pkgdblib.PkgdbException, err:
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
@packager_login_required
def api_package_unretire():
    '''
Unretire packages
-----------------
    Un-retire one or more packages.

    ::

        /api/package/unretire/

    Accept POST queries only.

    :arg pkgnames: Comma separated list of the packages names.
    :arg branches: Comma separated list of string of the branches names in
        which these packages will be un-deprecated.


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

    if pkgnames and branches:
        try:
            messages = []
            for pkg_name, pkg_branch in itertools.product(
                    pkgnames, branches):
                message = pkgdblib.update_pkg_status(
                    SESSION,
                    pkg_name=pkg_name,
                    pkg_branch=pkg_branch,
                    status='Approved',
                    user=flask.g.fas_user,
                )
                messages.append(message)
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
def api_package_info(pkgname=None):
    '''
Package information
-------------------
    Return information about a specific package.

    ::

        /api/package/<pkg_name>/

        /api/package/?pkgname=<pkg_name>

    Accept GET queries only

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
    branches = flask.request.args.getlist('branches', None)
    eol = flask.request.args.get('eol', False)
    acls = flask.request.args.get('acls', True)
    if str(acls).lower() in ['0', 'false']:
        acls = False

    try:
        packages = pkgdblib.get_acl_package(
            SESSION,
            pkg_name=pkg_name,
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
        output['error'] = 'Package: %s not found' % pkg_name
        httpcode = 404

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/packages/')
@API.route('/packages')
@API.route('/packages/<pattern>/')
@API.route('/packages/<pattern>')
def api_package_list(pattern=None):
    '''
List packages
-------------
    List packages based on a pattern. If no pattern is provided, return all
    the package.

    ::

        /api/packages/<pattern>/

        /api/packages/?pattern=<pattern>

    Accept GET queries only

    :arg pattern: Pattern to list packages from their name.
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

    pattern = flask.request.args.get('pattern', pattern) or '*'
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
    acls = bool(flask.request.args.get('acls', False))
    statuses = flask.request.args.getlist('status', None)
    eol = flask.request.args.get('eol', False)
    page = flask.request.args.get('page', 1)
    limit = get_limit()
    count = flask.request.args.get('count', False)
    try:
        if not branches:
            branches = [None]
        if not statuses:
            statuses = [None]

        if count:
            packages = 0
            for status, branch in itertools.product(
                    statuses, branches):
                packages += pkgdblib.search_package(
                    SESSION,
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
            for status, branch in itertools.product(
                    statuses, branches):
                packages.update(
                    pkgdblib.search_package(
                        SESSION,
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

    except pkgdblib.PkgdbException, err:
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

    Accept POST queries only.

    :arg pkgnames: A list of string of the packages name.
    :arg branches: A list of string of the branches name in which the
        critpath status will be updated.
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
    branches = flask.request.form.getlist('branches', None)
    critpath = flask.request.form.get('critpath', False)
    if str(critpath).lower() in ['1', 'true']:
        critpath = True
    elif str(critpath).lower() in ['0', 'false']:
        critpath = False

    if pkgnames and branches:
        try:
            messages = []
            for pkg_name, pkg_branch in itertools.product(
                    pkgnames, branches):
                message = pkgdblib.set_critpath_packages(
                    SESSION,
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
        except pkgdblib.PkgdbException, err:
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


@API.route('/package/<package>/monitor/<status>', methods=['POST'])
@packager_login_required
def monitor_package(package, status):
    ''' Set the monitor status on the specified package.
    '''

    httpcode = 200
    output = {}
    if str(status).lower() not in ['1', 'true']:
        status = False
    else:
        status = True

    try:
        msg = pkgdblib.set_monitor_package(
            SESSION, package, status, flask.g.fas_user)
        SESSION.commit()
        output['output'] = 'ok'
        output['messages'] = msg
    except pkgdblib.PkgdbException, err:
        SESSION.rollback()
        output['output'] = 'notok'
        output['error'] = str(err)
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout
