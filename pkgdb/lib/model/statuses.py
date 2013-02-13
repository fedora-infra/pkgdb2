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
Mapping of database tables related to Statuses to python classes
'''

import sqlalchemy as sa
from sqlalchemy.orm import relation, backref
from sqlalchemy.orm.collections import attribute_mapped_collection

from sqlalchemy.ext.declarative import declarative_base
BASE = declarative_base()

from pkgdb.lib.model.packages import Package, PackageListing
from pkgdb.lib.model.pkgcollections import CollectionPackage, Collection
from pkgdb.lib.model.acls import PersonPackageListingAcl, GroupPackageListingAcl


# These are a bit convoluted as we have a 1:1:N relation between
# SpecificStatusTable:StatusCodeTable:StatusTranslationTable


class StatusTranslation(BASE):
    '''Map status codes to status names in various languages.

    Table -- StatusCodeTranslation
    '''

    __tablename__ = 'StatusCodeTranslation'
    statuscodeid = sa.Column(sa.Integer,
                             sa.ForeignKey('StatusCode.id',
                                           ondelete="CASCADE",
                                           onupdate="CASCADE"
                                           ),
                             nullable=False,
                             primary_key=True)
    language = sa.Column(sa.String(32), nullable=False, default='C',
                         primary_key=True)
    statusName = sa.Column(sa.Text, nullable=False)
    description = sa.Column(sa.Text)

    def __init__(self, statuscodeid, statusname, language=None,
                 description=None):
        '''
        :statuscodeid: id of the status this translation applies to
        :statusname: translated string
        :language: Languages code that this string is for.  if not given.
            defaults to 'C'
        :description: a description of what this status means.  May be
            used in online help
        '''
        self.statuscodeid = statuscodeid
        self.statusname = statusname
        self.language = language or None
        self.description = description or None

    def __repr__(self):
        return 'StatusTranslation(%r, %r, language=%r, description=%r)' \
            % (self.statuscodeid, self.statusname, self.language,
               self.description)


class BaseStatus(BASE):
    '''Fields common to all Statuses.'''

    statuscodeid = sa.Column(sa.Integer,
                             sa.ForeignKey('StatusCode.id',
                                           ondelete="CASCADE",
                                           onupdate="CASCADE"
                                           ),
                             nullable=False,
                             primary_key=True)

    def __init__(self, statuscodeid):
        self.statuscodeid = statuscodeid


class CollectionStatus(BaseStatus):
    '''Subset of status codes that are applicable to collections.

    Table -- CollectionStatusCode
    '''

    __tablename__ = 'CollectionStatusCode'
    collections = relation(Collection, backref=backref('status')),
    collectionPackages = relation(CollectionPackage,
                                  backref=backref('status'))
    translations = relation(StatusTranslation,
                            order_by=StatusTranslation.language,
                            primaryjoin=StatusTranslation.statuscodeid
                                == CollectionStatus.statuscodeid,
                            foreign_keys=[StatusTranslation.statuscodeid]
                            )
    locale = relation(StatusTranslation,
                      primaryjoin=StatusTranslation.statuscodeid
                        == CollectionStatus.statuscodeid,
                      foreign_keys=[StatusTranslation.statuscodeid],
                      collection_class=attribute_mapped_collection('language'),
                      backref=backref('cstatuscode',
                        foreign_keys=[StatusTranslation.statuscodeid],
                        primaryjoin=StatusTranslation.statuscodeid
                            == CollectionStatus.statuscodeid)
                      )
    
    def __repr__(self):
        return 'CollectionStatus(%r)' % self.statuscodeid


class PackageStatus(BaseStatus):
    '''Subset of status codes that apply to packages.

    Table -- PackageStatusCode
    '''
    
    __tablename__ = 'PackageStatusCode'
    packages = relation(Package, backref=backref('status'))
    translations = relation(StatusTranslation,
        order_by=StatusTranslation.language,
        primaryjoin=StatusTranslation.statuscodeid \
                == PackageStatus.statuscodeid,
        foreign_keys=[StatusTranslation.statuscodeid])
    locale = relation(StatusTranslation,
        order_by=StatusTranslation.language,
        primaryjoin=StatusTranslation.statuscodeid \
                == PackageStatus.statuscodeid,
        foreign_keys=[StatusTranslation.statuscodeid],
        collection_class=attribute_mapped_collection('language'),
        backref=backref('pstatuscode',
            foreign_keys=[StatusTranslation.statuscodeid],
            primaryjoin=StatusTranslation.statuscodeid \
                    == PackageStatus.statuscodeid))

    def __repr__(self):
        return 'PackageStatus(%r)' % self.statuscodeid


class PackageListingStatus(BaseStatus):
    '''Subset of status codes that are applicable to package listings.

    Table -- PackageListingStatusCode
    '''

    __tablename__ = 'PackageListingStatusCode'
    listings = relation(PackageListing, backref=backref('status'))
    translations = relation(StatusTranslation,
        order_by=StatusTranslation.language,
        primaryjoin=StatusTranslation.statuscodeid \
                == PackageListingStatus.statuscodeid,
        foreign_keys=[StatusTranslation.statuscodeid])
    locale = relation(StatusTranslation,
        order_by=StatusTranslation.language,
        primaryjoin=StatusTranslation.statuscodeid \
                == PackageListingStatus.statuscodeid,
        foreign_keys=[StatusTranslation.statuscodeid],
        collection_class=attribute_mapped_collection('language'),
        backref=backref('plstatuscode',
            foreign_keys=[StatusTranslation.statuscodeid],
            primaryjoin=StatusTranslation.statuscodeid \
                    == PackageListingStatus.statuscodeid))

    def __repr__(self):
        return 'PackageListingStatus(%r)' % self.statuscodeid


class PackageAclStatus(BaseStatus):
    ''' Subset of status codes that apply to Person and Group Package Acls.

    Table -- PackageAclStatusCode
    '''

    __tablename__ = 'PackageAclStatusCode'
    pacls = relation(PersonPackageListingAcl,
        backref=backref('status')),
    gacls = relation(GroupPackageListingAcl,
        backref=backref('status')),
    translations = relation(StatusTranslation,
        order_by=StatusTranslation.language,
        primaryjoin=StatusTranslation.statuscodeid \
                == PackageAclStatus.statuscodeid,
        foreign_keys=[StatusTranslation.statuscodeid]),
    locale = relation(StatusTranslation,
        order_by=StatusTranslation.language,
        primaryjoin=StatusTranslation.statuscodeid \
                == PackageAclStatus.statuscodeid,
        foreign_keys=[StatusTranslation.statuscodeid],
        collection_class=attribute_mapped_collection('language'),
        backref=backref('pastatuscode',
            foreign_keys=[StatusTranslation.statuscodeid],
            primaryjoin=StatusTranslation.statuscodeid \
                    == PackageAclStatus.statuscodeid))

    def __repr__(self):
        return 'PackageAclStatus(%r)' % self.statuscodeid
