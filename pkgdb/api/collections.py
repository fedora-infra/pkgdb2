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


## Collection
@API.route('/collection/new/', methods=['POST'])
def api_collection_new():
    ''' Create a new collection.

    :arg collectionname: String of the collection name to be created.
    :arg version: String of the version of the collection.
    :arg owner: String of the name of the user owner of the collection.

    '''
    httpcode = 200
    output = {}

    #TODO: implement the logic

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/collection/eol/', methods=['POST'])
def api_collection_eol():
    ''' End Of Life for a collection.

    :arg collectionname: String of the collection name to be created.
    :arg version: String of the version of the collection.

    '''
    httpcode = 200
    output = {}

    #TODO: implement the logic

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/collection/list/', methods=['POST'])
def api_collection_list():
    ''' List collections.

    '''
    httpcode = 200
    output = {}

    #TODO: implement the logic

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout
