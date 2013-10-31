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
API for package management.
'''

import flask
import itertools

from sqlalchemy.orm.exc import NoResultFound

import pkgdb.lib as pkgdblib
from pkgdb import SESSION, forms, is_admin, packager_login_required
from pkgdb.api import API


## Package
@API.route('/package/new/', methods=['POST'])
@is_admin
def api_package_new():
    '''``/api/package/new/``
    Create a new package.

    Accept POST queries only.

    :arg packagename: String of the package name to be created.
    :arg summary: String of the summary description of the package.

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
        pkg_name = form.pkg_name.data
        pkg_summary = form.pkg_summary.data
        pkg_review_url = form.pkg_reviewURL.data
        pkg_status = form.pkg_status.data
        pkg_shouldopen = form.pkg_shouldopen.data
        pkg_collection = form.pkg_collection.data
        pkg_poc = form.pkg_poc.data
        pkg_upstream_url = form.pkg_upstreamURL.data

        try:
            message = pkgdblib.add_package(
                SESSION,
                pkg_name=pkg_name,
                pkg_summary=pkg_summary,
                pkg_reviewURL=pkg_review_url,
                pkg_status=pkg_status,
                pkg_shouldopen=pkg_shouldopen,
                pkg_collection=pkg_collection,
                pkg_poc=pkg_poc,
                pkg_upstreamURL=pkg_upstream_url,
                user=flask.g.fas_user
            )
            SESSION.commit()
            output['output'] = 'ok'
            output['messages'] = [message]
        except pkgdblib.PkgdbException, err:
            SESSION.rollback()
            output['output'] = 'notok'
            output['error'] = err.message
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
    '''``/api/package/orphan/``
    Orphan a list of packages.

    Accept POST queries only.

    :arg packagenames: List of string of the packages name.
    :arg branches: List of string of the branches name in which these
        packages will be orphaned.
    :arg all_pkgs: boolean (defaults to False) stipulating if all the
        packages of the user (you or someon else if you are admin) are
        getting orphaned.

     '''
    httpcode = 200
    output = {}

    form = forms.PackageOwnerForm(
        csrf_enabled=False
    )
    if form.validate_on_submit():
        pkg_names = form.pkg_name.data.split(',')
        pkg_branchs = form.clt_name.data.split(',')

        try:
            for pkg_name, pkg_branch in itertools.product(
                    pkg_names, pkg_branchs):
                message = pkgdblib.update_pkg_poc(
                    SESSION,
                    pkg_name=pkg_name,
                    pkg_branch=pkg_branch,
                    pkg_poc='orphan',
                    user=flask.g.fas_user,
                )
            SESSION.commit()
            output['output'] = 'ok'
            output['messages'] = [message]
        except pkgdblib.PkgdbException, err:
            SESSION.rollback()
            output['output'] = 'notok'
            output['error'] = err.message
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


@API.route('/package/unorphan/', methods=['POST'])
@packager_login_required
def api_package_unorphan():
    '''``/api/package/unorphan/``
    Unorphan a list of packages.

    Accept POST queries only.

    :arg packagenames: List of string of the packages name.
    :arg branches: List of string of the branches name in which these
        packages will be unorphaned.
    :arg username: String of the name of the user taking ownership of
        this package. If you are not an admin, this name must be None.

    '''
    httpcode = 200
    output = {}

    form = forms.PackageOwnerForm(
        csrf_enabled=False,
    )
    if form.validate_on_submit():
        pkg_names = form.pkg_name.data.split(',')
        pkg_branchs = form.clt_name.data.split(',')
        pkg_poc = form.pkg_poc.data

        try:
            for pkg_name, pkg_branch in itertools.product(
                    pkg_names, pkg_branchs):
                message = pkgdblib.unorphan_package(
                    session=SESSION,
                    pkg_name=pkg_name,
                    pkg_branch=pkg_branch,
                    pkg_user=pkg_poc,
                    user=flask.g.fas_user
                )
            SESSION.commit()
            output['output'] = 'ok'
            output['messages'] = [message]
        except pkgdblib.PkgdbException, err:
            SESSION.rollback()
            output['output'] = 'notok'
            output['error'] = err.message
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


@API.route('/package/retire/', methods=['POST'])
@packager_login_required
def api_package_retire():
    '''``/api/package/retire/``
    Retire a list of packages.

    Accept POST queries only.

    :arg packagenames: List of string of the packages name.
    :arg branches: List of string of the branches name in which these
        packages will be retire.

    '''
    httpcode = 200
    output = {}

    form = forms.DeprecatePackageForm(csrf_enabled=False)
    if form.validate_on_submit():
        pkg_names = form.pkg_name.data.split(',')
        pkg_branchs = form.clt_name.data.split(',')

        try:
            for pkg_name, pkg_branch in itertools.product(
                    pkg_names, pkg_branchs):
                message = pkgdblib.update_pkg_status(
                    SESSION,
                    pkg_name=pkg_name,
                    pkg_branch=pkg_branch,
                    status='Retired',
                    user=flask.g.fas_user,
                )
            SESSION.commit()
            output['output'] = 'ok'
            output['messages'] = [message]
        except pkgdblib.PkgdbException, err:
            SESSION.rollback()
            output['output'] = 'notok'
            output['error'] = err.message
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


@API.route('/package/unretire/', methods=['POST'])
@packager_login_required
def api_package_unretire():
    '''``/api/package/unretire/``
    Un-deprecate a list of packages.

    Accept POST queries only.

    :arg packagenames: List of string of the packages name.
    :arg branches: List of string of the branches name in which these
        packages will be un-deprecated.

    '''
    httpcode = 200
    output = {}

    form = forms.DeprecatePackageForm(csrf_enabled=False)
    if form.validate_on_submit():
        pkg_names = form.pkg_name.data.split(',')
        pkg_branchs = form.clt_name.data.split(',')

        try:
            for pkg_name, pkg_branch in itertools.product(
                    pkg_names, pkg_branchs):
                message = pkgdblib.update_pkg_status(
                    SESSION,
                    pkg_name=pkg_name,
                    pkg_branch=pkg_branch,
                    status='Approved',
                    user=flask.g.fas_user,
                )
            SESSION.commit()
            output['output'] = 'ok'
            output['messages'] = [message]
        except pkgdblib.PkgdbException, err:
            SESSION.rollback()
            output['output'] = 'notok'
            output['error'] = err.message
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


@API.route('/package/')
@API.route('/package')
@API.route('/package/<pkg_name>/')
@API.route('/package/<pkg_name>')
def api_package_info(pkg_name=None):
    '''``/api/package/<pkg_name>/`` \
        or ``/api/package/?pattern=<pkg_name>``

    Return information about a specific package.

    Accept GET queries only

    :arg pkg_name: The name of the package to retrieve the information of.
    :kwarg pkg_clt: Restricts the package information to a specific
        collection (branch).

    Sample response:

.. code-block:: javascript

    {
      "output": "ok",
      "packages": [
        {
          "point_of_contact": "spot",
          "collection": {
            "pendingurltemplate": "http://...",
            "publishurltemplate": "http://...",
            "branchname": "devel",
            "version": "devel",
            "name": "Fedora"
          },
          "package": {
            "upstreamurl": "http://guake.org",
            "name": "guake",
            "reviewurl": "http://bugzilla.redhat.com/450189",
            "summary": "Drop down terminal"
          }
        },
        {
          "point_of_contact": "pingou",
          "collection": {
            "pendingurltemplate": "http://...",
            "publishurltemplate": "http://...",
            "branchname": "F-19",
            "version": "19",
            "name": "Fedora"
          },
          "package": {
            "upstreamurl": "http://guake.org",
            "name": "guake",
            "reviewurl": "http://bugzilla.redhat.com/450189",
            "summary": "Drop down terminal"
          }
        }
      ]
    }

    '''
    httpcode = 200
    output = {}

    pkg_name = flask.request.args.get('pkg_name', pkg_name)
    pkg_clt = flask.request.args.get('pkg_clt', None)

    try:
        packages = pkgdblib.get_acl_package(
            SESSION,
            pkg_name=pkg_name,
            pkg_clt=pkg_clt,
        )
        output['output'] = 'ok'
        output['packages'] = [pkg.to_json() for pkg in packages]
    except NoResultFound:
        output['output'] = 'notok'
        output['error'] = 'Package: %s not found' % pkg_name
        httpcode = 404
    except pkgdblib.PkgdbException, err:
        SESSION.rollback()
        output['output'] = 'notok'
        output['error'] = err.message
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/packages/')
@API.route('/packages')
@API.route('/packages/<pattern>/')
@API.route('/packages/<pattern>')
def api_package_list(pattern=None):
    '''``/api/packages/<pattern>/`` \
        or ``/api/packages/?pattern=<pattern>``
    List packages based on a pattern. If no pattern is provided, return all
    the package.

    Accept GET queries only

    :arg packagename: Pattern to list packages from their name.
    :arg branches: List of string of the branches name in which these
        packages will be searched.
    :arg owner: String of the user name to to which restrict the search.
    :arg orphaned: Boolean to retrict the search to orphaned packages.
    :arg status: Allows to filter packages based on their status: Approved,
        Orphaned, Retired, Removed.
    :kwarg limit: An integer to limit the number of results, defaults to
        100, maybe be None.
    :kwarg page: The page number to return (useful in combination to limit).
    :kwarg count: A boolean to return the number of packages instead of the
        list. Defaults to False.

    Sample response:

.. code-block:: javascript

    {
      "output": "ok",
      "packages": [
        {
          "status": "Approved",
          "upstreamurl": "http://guake.org",
          "name": "guake",
          "summary": "Drop down terminal",
          "acls": [
            {
              "point_of_contact": "spot",
              "collection": {
                "pendingurltemplate": "http://...",
                "publishurltemplate": "http://...",
                "branchname": "devel",
                "version": "devel",
                "name": "Fedora"
              },
              "package": {
                "upstreamurl": "http://guake.org",
                "name": "guake",
                "reviewurl": "http://bugzilla.redhat.com/450189",
                "summary": "Drop down terminal"
              }
            },
            {
              "point_of_contact": "pingou",
              "collection": {
                "pendingurltemplate": "http://...",
                "publishurltemplate": "http://...",
                "branchname": "F-19",
                "version": "19",
                "name": "Fedora"
              },
              "package": {
                "upstreamurl": "http://guake.org",
                "name": "guake",
                "reviewurl": "http://bugzilla.redhat.com/450189",
                "summary": "Drop down terminal"
              }
            }
          ],
          "creation_date": "2013-09-09 14:43:21.578370",
          "reviewurl": "http://bugzilla.redhat.com/450189",
        }
      ]
    }
    '''
    httpcode = 200
    output = {}

    pattern = flask.request.args.get('pattern', pattern)
    branches = flask.request.args.get('branches', None)
    owner = flask.request.args.get('owner', None)
    orphaned = bool(flask.request.args.get('orphaned', False))
    status = flask.request.args.get('status', False)
    page = flask.request.args.get('page', None)
    limit = flask.request.args.get('limit', 100)
    count = flask.request.args.get('count', False)

    try:
        packages = pkgdblib.search_package(
            SESSION,
            pkg_name=pattern,
            pkg_branch=branches,
            pkg_poc=owner,
            orphaned=orphaned,
            status=status,
            page=page,
            limit=limit,
            count=count,
        )
        if not packages:
            output['output'] = 'notok'
            output['packages'] = []
            output['error'] = 'No packages found for these parameters'
            httpcode = 404
        else:
            output['output'] = 'ok'
            if isinstance(packages, (int, float)):
                output['packages'] = packages
            else:
                output['packages'] = [pkg.to_json() for pkg in packages]
    except pkgdblib.PkgdbException, err:
        SESSION.rollback()
        output['output'] = 'notok'
        output['error'] = err.message
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout
