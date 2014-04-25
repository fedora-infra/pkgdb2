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
Packagers
=========

API for collection management.
'''

import flask

from math import ceil

import pkgdb2.lib as pkgdblib
from pkgdb2 import SESSION
from pkgdb2.api import API, get_limit


## Some of the object we use here have inherited methods which apparently
## pylint does not detect.
# pylint: disable=E1101
## similar line
# pylint: disable=R0801
## cyclic import
# pylint: disable=R0401
## Too many branches
# pylint: disable=R0912


## Packagers
@API.route('/packager/acl/')
@API.route('/packager/acl')
@API.route('/packager/acl/<packagername>/')
@API.route('/packager/acl/<packagername>')
def api_packager_acl(packagername=None):
    '''
User's ACL
----------
    List the ACLs of the user.

    ::

        /api/packager/acl/<fas_username>/

        /api/packager/acl/?packagername=<username>

    Accept GET queries only.

    :arg packagername: String of the packager name.
    :kwarg acls: One or more ACL to filter the ACLs retrieved. Options are:
        ``approveacls``, ``commit``, ``watchbugzilla``, ``watchcommits``.
    :kwarg eol: a boolean to specify whether to include results for
        EOL collections or not. Defaults to False.
        If ``True``, it will return results for all collections (including
        EOL).
        If ``False``, it will return results only for non-EOL collections.
    :kwarg poc: a boolean specifying whether the results should be
        restricted to ACL for which the provided packager is the point
        of contact or not. Defaults to None.
        If ``True`` it will only return ACLs for packages on which the
        provided packager is point of contact.
        If ``False`` it will only return ACLs for packages on which the
        provided packager is not the point of contact.
        If ``None`` it will not filter the ACLs returned based on the point
        of contact of the package (thus every packages is returned).
    :kwarg page: The page number to return (useful in combination to limit).
    :kwarg limit: An integer to limit the number of results, defaults to
        250, maximum is 500 (acls).
    :kwarg count: A boolean to return the number of packages instead of the
        list. Defaults to False.

    *Results are paginated*

    Sample response:

    ::

        /api/packager/acl/pingou

        {
          "output": "ok",
          "page": 1,
          "page_total": 12
          "acls": [
            {
              "status": "Approved",
              "fas_name": "pingou",
              "packagelist": {
                "point_of_contact": "pingou",
                "collection": {
                  "status": "EOL",
                  "branchname": "f16",
                  "version": "16",
                  "name": "Fedora"
                },
                "package": {
                  "status": "Approved",
                  "upstream_url": null,
                  "description": null,
                  "summary": "Data of T- and B-cell Acute Lymphocytic "
                             "Leukemia",
                  "creation_date": 1384775354.0,
                  "review_url": null,
                  "name": "R-ALL"
                }
              },
              "acl": "watchcommits"
            },
            {
              "status": "Approved",
              "fas_name": "pingou",
              "packagelist": {
                "point_of_contact": "pingou",
                "collection": {
                  "status": "EOL",
                  "branchname": "f16",
                  "version": "16",
                  "name": "Fedora"
                },
                "package": {
                  "status": "Approved",
                  "upstream_url": null,
                  "description": null,
                  "summary": "Data of T- and B-cell Acute Lymphocytic "
                             "Leukemia",
                  "creation_date": 1384775354.0,
                  "review_url": null,
                  "name": "R-ALL"
                }
              },
              "acl": "watchbugzilla"
            }
          ]
        }

        /api/packager/acl/?packagername=random

        {
          "output": "notok",
          "error": "No ACL found for this user",
          "page": 1
        }

    '''
    httpcode = 200
    output = {}

    packagername = flask.request.args.get('packagername', None) or packagername
    acls = flask.request.args.getlist('acls', None)
    eol = flask.request.args.get('eol', False)
    poc = flask.request.args.get('poc', None)
    if poc is not None:
        if poc in ['False', '0', 0]:
            poc = False
        poc = bool(poc)

    pkg_acl = pkgdblib.get_status(SESSION, 'pkg_acl')['pkg_acl']
    for acl in acls:
        if acl not in pkg_acl:
            output = {
                'output': 'notok',
                'error': 'Invalid request, "%s" is an invalid acl' % acl}
            httpcode = 500
            jsonout = flask.jsonify(output)
            jsonout.status_code = httpcode
            return jsonout

    page = flask.request.args.get('page', 1)
    limit = get_limit()
    count = flask.request.args.get('count', False)

    if packagername:
        packagers = pkgdblib.get_acl_packager(
            SESSION,
            packager=packagername,
            acls=acls,
            eol=eol,
            poc=poc,
            page=page,
            limit=limit,
            count=count)
        if packagers:
            output['output'] = 'ok'
            if count:
                output['acls_count'] = packagers
            else:
                output['acls'] = [pkg.to_json() for pkg in packagers]

            total_acl = pkgdblib.get_acl_packager(
                SESSION,
                packager=packagername,
                acls=acls,
                eol=eol,
                poc=poc,
                count=True)

            if count:
                output['page_total'] = 1
            else:
                output['page_total'] = int(ceil(total_acl / float(limit)))
        else:
            output = {'output': 'notok', 'error': 'No ACL found for this user'}
            httpcode = 404
    else:
        output = {'output': 'notok', 'error': 'Invalid request'}
        httpcode = 500

    output['page'] = page
    if 'page_total' not in output:
        output['page_total'] = 1

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/packager/stats/')
@API.route('/packager/stats')
@API.route('/packager/stats/<packagername>/')
@API.route('/packager/stats/<packagername>')
def api_packager_stats(packagername=None):
    '''
User's stats
------------
    Give some stats about the ACLs of the user.

    ::

        /api/packager/stats/<fas_username>/

        /api/packager/stats/?packagername=<username>

    Accept GET queries only.

    :arg packagername: String of the packager name.

    Sample response:

    ::

        /api/packager/stats/pingou

        {
          "EL-6": {
            "co-maintainer": 8,
            "point of contact": 12
          },
          "devel": {
            "co-maintainer": 12,
            "point of contact": 60
          },
          "f19": {
            "co-maintainer": 12,
            "point of contact": 60
          },
          "f20": {
            "co-maintainer": 12,
            "point of contact": 60
          },
          "output": "ok"
        }


        /api/packager/stats/?packagername=random

        {
          "EL-6": {
            "co-maintainer": 0,
            "point of contact": 0
          },
          "devel": {
            "co-maintainer": 0,
            "point of contact": 0
          },
          "f19": {
            "co-maintainer": 0,
            "point of contact": 0
          },
          "f20": {
            "co-maintainer": 0,
            "point of contact": 0
          },
          "output": "ok"
        }

    '''

    httpcode = 200
    output = {}

    packagername = flask.request.args.get('packagername', None) or packagername

    if packagername:
        collections = pkgdblib.search_collection(
            SESSION, '*', status='Active')
        collections.extend(pkgdblib.search_collection(
            SESSION, '*', status='Under Development'))
        for collection in collections:
            packages_co = pkgdblib.get_package_maintained(
                SESSION,
                packager=packagername,
                poc=False,
                branch=collection.branchname
            )

            packages = pkgdblib.get_package_maintained(
                SESSION,
                packager=packagername,
                poc=True,
                branch=collection.branchname
            )
            output[collection.branchname] = {
                'point of contact': len(packages),
                'co-maintainer': len(packages_co)
            }
        output['output'] = 'ok'
    else:
        output = {'output': 'notok', 'error': 'Invalid request'}
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/packagers/')
@API.route('/packagers')
@API.route('/packagers/<pattern>/')
@API.route('/packagers/<pattern>')
def api_packager_list(pattern=None):
    '''
List packagers
--------------
    List packagers based on a pattern. If no pattern is provided, return
    all the packagers.

    Only packagers having at least commit right on one package on the
    active collections are returned (on the contrary to querying
    `FAS <https://admin.fedorapoject.org/accounts>`_ for the members of the
    packager group).

    ::

        /api/packagers/<pattern>/

        /api/packagers/?pattern=<pattern>

    :kwarg pattern: String of the pattern to use to list find packagers.
        If no pattern is provided, it returns the list of all packagers.


    Sample response:

    ::

        /api/packagers/rem*

        {
          "output": "ok",
          "packagers": [
            "remi"
          ]
        }

        /api/packagers/?pattern=pi*

        {
          "output": "ok",
          "packagers": [
            "pilcher",
            "pingou"
          ]
        }
    '''
    httpcode = 200
    output = {}

    pattern = flask.request.args.get('pattern', pattern) or '*'
    if pattern:
        packagers = pkgdblib.search_packagers(
            SESSION, pattern=pattern, eol=False)
        packagers = [pkg[0] for pkg in packagers]
        SESSION.commit()
        output['output'] = 'ok'
        output['packagers'] = packagers
    else:  # pragma: no cover # In theory we can never get here
        output = {'output': 'notok', 'error': 'Invalid request'}
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout
