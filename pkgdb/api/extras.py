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
Extras API endpoints for the Flask application.
'''

import itertools
import flask

from sqlalchemy.orm.exc import NoResultFound

import pkgdb
import pkgdb.lib as pkgdblib
from pkgdb import SESSION
from pkgdb.api import API


def __format_row(branch, package):
    """ Format a row for the bugzilla output. """
    cclist = ','.join(
        [pkg.fas_name
         for pkg in branch.acls if pkg.acl == 'commit'
            and pkg.fas_name != branch.point_of_contact]
    )
    output = "|".join([
            branch.collection.name,
            package.name,
            package.summary,
            branch.point_of_contact,
            cclist,
        ])
    return output


@pkgdb.cache.cache_on_arguments(expiration_time=3600)
def bz_acls_cached():
    packages = pkgdblib.search_package(SESSION, '*')
    output = []
    for package in packages:
        branch_fed = None
        branch_epel = None
        for branch in package.listings:
            # Consider the devel branch, unless it is orphan then consider
            # the next one
            if branch.collection.name == 'Fedora':
                if branch.collection.branchname == 'devel':
                    branch_fed = branch
                    if branch.point_of_contact != 'orphan':
                        break
                elif not branch_fed \
                        or branch_fed.point_of_contact == 'orphan' \
                        or int(branch.version) > int(branch_fed.version):
                    branch_fed = branch
            elif branch.collection.name == 'Fedora EPEL':
                if branch.collection.branchname == 'EL-6':
                    branch_epel = branch
                    if branch.point_of_contact != 'orphan':
                        break
                elif not branch_epel \
                        or branch_epel.point_of_contact == 'orphan' \
                        or int(branch.version) > int(branch_epel.version):
                    branch_epel = branch

        if branch_fed:
            output.append(__format_row(branch_fed, package))
        if branch_epel:
            output.append(__format_row(branch_epel, package))
    return output


@API.route('/bugzilla/')
@API.route('/bugzilla')
def bugzilla():
    ''' Return a list of the Database VCS ACLs in text format. '''
    intro = """# Package Database VCS Acls
# Text Format
# Collection|Package|Description|Owner|Initial QA|Initial CCList
# Backslashes (\) are escaped as \u005c Pipes (|) are escaped as \u007c

"""

    acls = bz_acls_cached()

    return flask.Response(
        intro + "\n".join(acls),
        content_type="text/plain;charset=UTF-8"
    )
