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

import pkgdb.forms
from pkgdb.api import API


## Package
@API.route('/package/new/', methods=['POST'])
def api_package_new():
    ''' Create a new package.

    :arg packagename: String of the package name to be created.
    :arg summary: String of the summary description of the package.

    '''
    httpcode = 200
    output = {}

    #TODO: implement the logic

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/package/orphan/', methods=['POST'])
def api_package_orphan():
    ''' Orphan a list of packages.

    :arg packagenames: List of string of the packages name.
    :arg branches: List of string of the branches name in which these
        packages will be orphaned.
    :arg all_pkgs: boolean (defaults to False) stipulating if all the
        packages of the user (you or someon else if you are admin) are
        getting orphaned.

     '''
    httpcode = 200
    output = {}

    #TODO: implement the logic

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/package/unorphan/', methods=['POST'])
def api_package_unorphan():
    ''' Unorphan a list of packages.

    :arg packagenames: List of string of the packages name.
    :arg branches: List of string of the branches name in which these
        packages will be unorphaned.
    :arg username: String of the name of the user taking ownership of
        this package. If you are not an admin, this name must be None.

    '''
    httpcode = 200
    output = {}

    #TODO: implement the logic

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/package/deprecate/', methods=['POST'])
def api_package_deprecate():
    ''' Deprecate a list of packages.

    :arg packagenames: List of string of the packages name.
    :arg branches: List of string of the branches name in which these
        packages will be deprecated.

    '''
    httpcode = 200
    output = {}

    #TODO: implement the logic

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@API.route('/package/list/')
def api_package_list():
    ''' List packages.

    :arg packagenames: Pattern to list packages from their name.
    :arg branches: List of string of the branches name in which these
        packages will be searched.
    :arg username: String of the user name to to which restrict the
        search.
    :arg orphaned: Boolean to retrict the search to orphaned packages. 
    :arg deprecated: Boolean to retrict the search to deprecated
        packages.

    '''
    httpcode = 200
    output = {}

    #TODO: implement the logic

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout
