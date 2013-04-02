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
Top level of the pkgdb Flask application.
'''

import flask
import os

import lib as pkgdblib


__version__ = '0.1.0'

APP = flask.Flask(__name__)
APP.config.from_object('pkgdb.default_config')
if 'PKGDB_CONFIG' in os.environ:  # pragma: no cover
    APP.config.from_envvar('PKGDB_CONFIG')

SESSION = pkgdblib.create_session(APP.config['DB_URL'])

# Import the API namespace
from api import API
from api import acls
from api import collections
from api import packages
from api import packagers

APP.register_blueprint(API)


# pylint: disable=W0613
@APP.teardown_request
def shutdown_session(exception=None):
    """ Remove the DB session at the end of each request. """
    SESSION.remove()
