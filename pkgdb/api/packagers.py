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

import pkgdb.forms
from pkgdb.api import API


## Packagers
@API.route('/packager/acl/')
@API.route('/packager/acl/<packagername>/')
def api_packager_acl(packagername=None):
    ''' List the pending ACL action of the user.

    :arg username: String of the packager name.

    '''
    httpcode = 200
    output = {}

    packagername = flask.request.args.get('packagername', None) or packagername
    if packagername:
        #TODO: implement the logic
        pass
    else:
        output = {'output': 'notok', 'error': 'Invalid request'}
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/packager/list/')
@API.route('/packager/list/<pattern>/')
def api_packager_list(pattern=None):
    ''' List packagers.

    :kwarg pattern: String of the pattern to use to list find packagers.
        If no pattern is provided, it returns the list of all packagers.

    '''
    httpcode = 200
    output = {}

    pattern = flask.request.args.get('pattern', None) or pattern
    if pattern:
        packagers = pkgdblib.search_packagers(SESSION,
                                              pkg_name=pattern,
                                              )
        SESSION.commit()
        output['output'] = 'ok'
        output['packagers'] = packagers
    else:
        output = {'output': 'notok', 'error': 'Invalid request'}
        httpcode = 500

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout
