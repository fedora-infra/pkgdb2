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
API for collection management.
'''

import flask

import pkgdb.lib as pkgdblib
from pkgdb import SESSION
from pkgdb.api import API


## Packagers
@API.route('/packager/acl/')
@API.route('/packager/acl')
@API.route('/packager/acl/<packagername>/')
@API.route('/packager/acl/<packagername>')
def api_packager_acl(packagername=None):
    '''``/api/packager/acl/"fas_username"/``
        or ``/api/packager/acl/?packagername="fas_username"``
    List the ACLs of the user.

    Accept GET queries only.

    :arg username: String of the packager name.

    '''
    httpcode = 200
    output = {}

    packagername = flask.request.args.get('packagername', None) or packagername
    if packagername:
        packagers = pkgdblib.get_acl_packager(SESSION,
                                              packager=packagername,
                                              )
        SESSION.commit()
        output['output'] = 'ok'
        output['acls'] = [pkg.to_json() for pkg in packagers]
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
    '''``/api/packagers/"pattern"/`` or ``/api/packagers/?pattern="pattern"``
    List packagers based on a pattern. If no pattern is provided, return
    all the packagers.

    :kwarg pattern: String of the pattern to use to list find packagers.
        If no pattern is provided, it returns the list of all packagers.

    '''
    httpcode = 200
    output = {}

    pattern = flask.request.args.get('pattern', None) or pattern
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
