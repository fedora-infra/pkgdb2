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
Mapping of acl related database tables
'''

import sqlalchemy as sa
from sqlalchemy.orm import relation, backref
from sqlalchemy.orm.collections import attribute_mapped_collection

from pkgdb.lib.model import BASE


class PersonPackageListing(BASE):
    '''Associate a person with a PackageListing.

    People who are watching or can modify a packagelisting.

    Table -- PersonPackageListing
    '''

    __tablename__ = 'PersonPackageListing'

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, nullable=False)
    packageListingId = sa.Column(
        sa.Integer,
        sa.ForeignKey('PackageListing.id',
                      ondelete="CASCADE",
                      onupdate="CASCADE"
                      ),
        nullable=False,
    )

    acls = relation(PersonPackageListingAcl)
    acls2 = relation(PersonPackageListingAcl,
                     backref=backref('personpackagelisting'),
                     collection_class=attribute_mapped_collection('acl')
                     )

    __table_args__ = (
        sa.UniqueConstraint('userid', 'packageListingId'),
    )

    # pylint: disable-msg=R0903
    def __init__(self, username, packagelistingid=None):
        self.username = username
        self.packagelistingid = packagelistingid

    def __repr__(self):
        return 'PersonPackageListing(%r, %r)' % (self.username,
                                                 self.packagelistingid)


class GroupPackageListing(BASE):
    '''Associate a group with a PackageListing.

    Table -- GroupPackageListing
    '''

    __tablename__ = 'GroupPackageListing'

    id = sa.Column(sa.Integer, primary_key=True)
    groupid = sa.Column(sa.Integer, nullable=False)
    packageListingId = sa.Column(
        sa.Integer,
        sa.ForeignKey('PackageListing.id',
                      ondelete="CASCADE",
                      onupdate="CASCADE"
                      ),
        nullable=False,
    )

    acls = relation(GroupPackageListingAcl)
    acls2 = relation(GroupPackageListingAcl,
                     backref=backref('grouppackagelisting'),
                     collection_class=attribute_mapped_collection('acl')
                     )

    __table_args__ = (
        sa.UniqueConstraint('groupid', 'packageListingId'),
    )

    def __init__(self, groupname, packagelistingid=None):
        self.groupname = groupname
        self.packagelistingid = packagelistingid

    def __repr__(self):
        return 'GroupPackageListing(%r, %r)' % (self.groupname,
                                                self.packagelistingid)


class PersonPackageListingAcl(BASE):
    '''Acl on a package that a person owns.

    Table -- PersonPackageListingAcl
    '''

    __tablename__ = 'PersonPackageListingAcl'

    id = sa.Column(sa.Integer, primary_key=True)
    acl = sa.Column(sa.Enum('commit', 'build', 'watchbugzilla',
                            'watchcommits', 'approveacls', 'checkout',
                            name='acl'),
                    nullable=False
                    )
    statuscode = sa.Column(sa.Integer,
                           sa.ForeignKey('PackageACLStatusCode.id',
                                         ondelete="CASCADE",
                                         onupdate="CASCADE"
                                         ),
                           nullable=False,
                           )
    personPackageListingId = sa.Column(sa.Integer,
                                       sa.ForeignKey('PersonPackageListing.id',
                                                     ondelete="CASCADE",
                                                     onupdate="CASCADE"
                                                     ),
                                       nullable=False,
                                       )
    __table_args__ = (
        sa.UniqueConstraint('personPackageListingId', 'acl'),
    )

    def __init__(self, acl, statuscode=None,
                 personpackagelistingid=None):
        self.personpackagelistingid = personpackagelistingid
        self.acl = acl
        self.statuscode = statuscode

    def __repr__(self):
        return 'PersonPackageListingAcl(%r, %r, personpackagelistingid=%r)' \
            % (self.acl, self.statuscode, self.personpackagelistingid)


class GroupPackageListingAcl(BASE):
    '''Acl on a package that a group owns.

    Table -- GroupPackageListingAcl
    '''

    __tablename__ = 'GroupPackageListingAcl'

    id = sa.Column(sa.Integer, primary_key=True)
    acl = sa.Column(sa.Enum('commit', 'build', 'watchbugzilla',
                            'watchcommits', 'approveacls', 'checkout',
                            name='acl'),
                    nullable=False
                    )
    statuscode = sa.Column(sa.Integer,
                           sa.ForeignKey('PackageACLStatusCode.id',
                                         ondelete="CASCADE",
                                         onupdate="CASCADE"
                                         ),
                           nullable=False,
                           )
    groupPackageListingId = sa.Column(sa.Integer,
                                      sa.ForeignKey('GroupPackageListing.id',
                                                    ondelete="CASCADE",
                                                    onupdate="CASCADE"
                                                    ),
                                      nullable=False,
                                      )
    __table_args__ = (
        sa.UniqueConstraint('groupPackageListingId', 'acl'),
    )

    def __init__(self, acl, statuscode=None, grouppackagelistingid=None):
        self.grouppackagelistingid = grouppackagelistingid
        self.acl = acl
        self.statuscode = statuscode

    def __repr__(self):
        return 'GroupPackageListingAcl(%r, %r, grouppackagelistingid=%r)'\
            % (self.acl, self.statuscode, self.grouppackagelistingid)
