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
Mapping of database tables for logs to python classes.
'''

import datetime

import sqlalchemy as sa
from sqlalchemy.orm import polymorphic_union, relation
from turbogears.database import metadata, mapper, get_engine

from pkgdb.lib.model import BASE

from pkgdb.lib.model.packages import Package, PackageListing
from pkgdb.lib.model.acls import PersonPackageListingAcl, GroupPackageListingAcl


class Log(BASE):
    '''Base Log record.

    This is a Log record.  All logs will be entered via a subclass of this.

    Table -- Log
    '''

    __tablename__ = 'Log'
    id = sa.Column(sa.Integer, nullable=False, primary_key=True)
    user_id = sa.Column(sa.Integer, nullable=False)
    change_time = sa.Column(sa.DateTime, nullable=False,
                           default=datetime.datetime.utcnow())
    package_id = sa.Column(sa.Integer,
                           sa.ForeignKey('Package.id',
                                         ondelete='RESTRICT',
                                         onupdate='CASCADE'
                                         ),
                           nullable=False,
                           )
    description = sa.Column(sa.Text, nullable=False)

    def __init__(self, user_id, package_id, description):
        self.user_id = user_id
        self.package_id = package_id
        self.description = description

    def __repr__(self):
        return 'Log(%r, description=%r, changetime=%r)' % (self.username,
                self.description, self.changetime)

    def save(self, session):
        ''' Save the current log entry. '''
        session.add(self)

    @classmethod
    def insert(cls, session, user_id, package, description):
        ''' Insert the given log entry into the database.

        :arg session: the session to connect to the database with
        :arg user: the identifier of the user doing the action
        :arg package: the `Package` object of the package changed
        :arg description: a short textual description of the action
            performed

        '''
        log = Log(user_id, package.id, description)
        log.save(session)
