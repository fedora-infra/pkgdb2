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
Packagers
=========

API for collection management.
'''

import flask

import pkgdb2.lib as pkgdblib
from pkgdb2 import SESSION
from pkgdb2.api import API


## Some of the object we use here have inherited methods which apparently
## pylint does not detect.
# pylint: disable=E1101


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

    :arg username: String of the packager name.
    :kwarg page: The page number to return (useful in combination to limit).
    :kwarg limit: An integer to limit the number of results, defaults to
        250 (acls).
    :kwarg count: A boolean to return the number of packages instead of the
        list. Defaults to False.

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
          "error": "No ACL found for this user"
        }

    '''
    httpcode = 200
    output = {}

    packagername = flask.request.args.get('packagername', None) or packagername

    page = flask.request.args.get('page', 1)
    limit = flask.request.args.get('limit', 250)
    count = flask.request.args.get('count', False)

    if packagername:
        packagers = pkgdblib.get_acl_packager(
            SESSION,
            packager=packagername,
            page=page,
            limit=limit,
            count=count)
        if packagers:
            output['output'] = 'ok'
            output['acls'] = [pkg.to_json() for pkg in packagers]

            total_acl = pkgdblib.get_acl_packager(
            SESSION,
            packager=packagername,
            count=True)

            output['page_total'] = total_acl / limit
        else:
            output = {'output': 'notok', 'error': 'No ACL found for this user'}
            httpcode = 404
    else:
        output = {'output': 'notok', 'error': 'Invalid request'}
        httpcode = 500

    output['page'] = page

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
        packagers = pkgdblib.search_packagers(SESSION,
                                              pattern=pattern,
                                              )
        packagers = [pkg[0] for pkg in packagers]
        SESSION.commit()
        output['output'] = 'ok'
        output['packagers'] = packagers
    else:
        output = {'output': 'notok', 'error': 'Invalid request'}
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout
