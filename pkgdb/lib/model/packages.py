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
Mapping of package related database tables to python classes.

.. data:: DEFAULT_GROUPS
    Groups that get acls on the Package Database by default (in 0.3.x, the
    groups have to be listed here in order for them to show up in the Package
    Database at all.
'''

import logging
import datetime

import sqlalchemy as sa
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref, eagerload, relation
from sqlalchemy.orm.collections import (attribute_mapped_collection,
    mapped_collection)
from sqlalchemy.sql import and_

from pkgdb.lib.model import BASE

from pkgdb.lib.model.acls import (GroupPackageListing,
    GroupPackageListingAcl, PersonPackageListing, PersonPackageListingAcl)

error_log = logging.getLogger('pkgdb.model.packages')


DEFAULT_GROUPS = {'provenpackager': {'commit': True, 'checkout': True}}


# Package and PackageListing are straightforward translations.  Look at these
# if you're looking for a straightforward example.


class Package(BASE):
    '''Software we are packaging.

    This is equal to the software in one of our revision control directories.
    It is unversioned and not associated with a particular collection.

    Table -- Package
    '''

    __tablename__ = 'Package'
    id = sa.Column(sa.Integer, nullable=False, primary_key=True)
    name = sa.Column(sa.Text, nullable=False, unique=True)
    summary = sa.Column(sa.Text, nullable=False)
    description = sa.Column(sa.Text)
    reviewURL = sa.Column(sa.Text)
    statuscode = sa.Column(sa.Integer,
                           sa.ForeignKey('PackageStatusCode.statuscodeid',
                                         ondelete="RESTRICT",
                                         onupdate="CASCADE"
                                         ),
                           nullable=False,
                           )
    shouldopen = sa.Column(sa.Boolean, nullable=False, default=True)

    listings = relation(PackageListing)
    listings2 = relation(PackageListing,
                         backref=backref('package'),
                         collection_class=mapped_collection(collection_alias)
                         )

    def __init__(self, name, summary, statuscode, description=None,
            reviewurl=None, shouldopen=None, upstreamurl=None):
        self.name = name
        self.summary = summary
        self.statuscode = statuscode
        self.description = description
        self.reviewurl = reviewurl
        self.shouldopen = shouldopen
        self.upstreamurl = upstreamurl

    def __repr__(self):
        return 'Package(%r, %r, %r, description=%r, ' \
               'upstreamurl=%r, reviewurl=%r, shouldopen=%r)' % (
                self.name, self.summary, self.statuscode, self.description,
                self.upstreamurl, self.reviewurl, self.shouldopen)

    def api_repr(self, version):
        """ Used by fedmsg to serialize Packages in messages. """
        if version == 1:
            return dict(
                name=self.name,
                summary=self.summary,
                description=self.description,
                reviewurl=self.reviewurl,
                upstreamurl=self.upstreamurl,
            )
        else:
            raise NotImplementedError("Unsupported version %r" % version)

    def create_listing(self, collection, owner, statusname,
            qacontact=None, author_name=None):
        '''Create a new PackageListing branch on this Package.

        :arg collection: Collection that the new PackageListing lives on
        :arg owner: The owner of the PackageListing
        :arg statusname: Status to set the PackageListing to
        :kwarg qacontact: QAContact for this PackageListing in bugzilla.
        :kwarg author_name: Author of the change.  Note: will remove when
            logging is made generic
        :returns: The new PackageListing object.

        This creates a new PackageListing for this Package.  The PackageListing
        has default values set for group acls.
        '''
        from pkgdb.lib.utils import STATUS
        from pkgdb.lib.model.logs import PackageListingLog
        pkg_listing = PackageListing(owner, STATUS[statusname],
                collectionid=collection.id,
                qacontact=qacontact)
        pkg_listing.packageid = self.id
        for group in DEFAULT_GROUPS:
            new_group = GroupPackageListing(group)
            #pylint:disable-msg=E1101
            pkg_listing.groups2[group] = new_group
            #pylint:enable-msg=E1101
            for acl, status in DEFAULT_GROUPS[group].iteritems():
                if status:
                    acl_statuscode = STATUS['Approved']
                else:
                    acl_statuscode = STATUS['Denied']
                group_acl = GroupPackageListingAcl(acl, acl_statuscode)
                # :W0201: grouppackagelisting is added to the model by
                #   SQLAlchemy so it doesn't appear in __init__
                #pylint:disable-msg=W0201
                group_acl.grouppackagelisting = new_group
                #pylint:enable-msg=W0201

        # Create a log message
        log = PackageListingLog(author_name, STATUS['Added'],
                '%(user)s added a %(branch)s to %(pkg)s' %
                {'user': author_name, 'branch': collection,
                    'pkg': self.name})
        log.listing = pkg_listing

        return pkg_listing


class PackageListing(BASE):
    '''This associates a package with a particular collection.

    Table -- PackageListing
    '''

    __tablename__ = 'PackageListing'
    id = sa.Column(sa.Integer, nullable=False, primary_key=True)
    packageId = sa.Column(sa.Integer,
                          sa.ForeignKey('Package.id',
                                         ondelete="CASCADE",
                                         onupdate="CASCADE"
                                         ),
                          nullable=False)
    collectionId = sa.Column(sa.Integer,
                          sa.ForeignKey('Collection.id',
                                         ondelete="CASCADE",
                                         onupdate="CASCADE"
                                         ),
                          nullable=False)
    owner = sa.Column(sa.Integer, nullable=False)
    qacontact = sa.Column(sa.Integer)
    statuscode = sa.Column(sa.Integer,
                           sa.ForeignKey('PackageStatusCode.statuscodeid',
                                         ondelete="RESTRICT",
                                         onupdate="CASCADE"
                                         ),
                           nullable=False,
                           )
    statuschange = sa.Column(sa.Datetime, nullable=False,
                             default=datetime.datetime.utcnow())
    __table_args__ = (
        sa.UniqueConstraint('packageId', 'collectionId'),
    )

    package = relation("Package")
    collection = relation("Collection")
    people = relation(PersonPackageListing)
    people2 = relation(PersonPackageListing, backref=backref('packagelisting'),
        collection_class = attribute_mapped_collection('username'))
    groups = relation(GroupPackageListing)
    groups2 = relation(GroupPackageListing, backref=backref('packagelisting'),
        collection_class = attribute_mapped_collection('groupname'))

    def __init__(self, owner, statuscode, packageid=None, collectionid=None,
            qacontact=None, specfile=None):
        self.packageid = packageid
        self.collectionid = collectionid
        self.owner = owner
        self.qacontact = qacontact
        self.statuscode = statuscode
        self.specfile = specfile

    packagename = association_proxy('package', 'name')

    def __repr__(self):
        return 'PackageListing(%r, %r, packageid=%r, collectionid=%r,' \
               ' qacontact=%r, specfile=%r)' % (self.owner, self.statuscode,
                        self.packageid, self.collectionid, self.qacontact,
                        self.specfile)

    def api_repr(self, version):
        """ Used by fedmsg to serialize PackageListing in messages. """
        if version == 1:
            return dict(
                package=self.package.api_repr(version),
                collection=self.collection.api_repr(version),
                owner=self.owner,
                qacontact=self.qacontact,
                specfile=self.specfile,
            )
        else:
            raise NotImplementedError("Unsupported version %r" % version)

    def clone(self, branch, author_name):
        '''Clone the permissions on this PackageListing to another `Branch`.

        :arg branch: `branchname` to make a new clone for
        :arg author_name: Author of the change.  Note, will remove when logs
            are made generic
        :raises sqlalchemy.exceptions.InvalidRequestError: when a request
            does something that violates the SQL integrity of the database
            somehow.
        :returns: new branch
        :rtype: PackageListing
        '''
        from pkgdb.lib.utils import STATUS
        from pkgdb.model.collections import Branch
        from pkgdb.model.logs import GroupPackageListingAclLog, \
                PersonPackageListingAclLog
        # Retrieve the PackageListing for the to clone branch
        try:
            #pylint:disable-msg=E1101
            clone_branch = PackageListing.query.join('package'
                    ).join('collection').filter(
                        and_(Package.name==self.package.name,
                            Branch.branchname==branch)).one()
            #pylint:enable-msg=E1101
        except InvalidRequestError:
            ### Create a new package listing for this release ###

            # Retrieve the collection to make the branch for
            #pylint:disable-msg=E1101
            clone_collection = Branch.query.filter_by(branchname=branch).one()
            #pylint:enable-msg=E1101
            # Create the new PackageListing
            clone_branch = self.package.create_listing(clone_collection,
                    self.owner, STATUS[self.statuscode], qacontact=self.qacontact,
                    author_name=author_name)

        log_params = {'user': author_name,
                'pkg': self.package.name, 'branch': branch}
        # Iterate through the acls in the master_branch
        #pylint:disable-msg=E1101
        for group_name, group in self.groups2.iteritems():
        #pylint:enable-msg=E1101
            log_params['group'] = group_name
            if group_name not in clone_branch.groups2:
                # Associate the group with the packagelisting
                #pylint:disable-msg=E1101
                clone_branch.groups2[group_name] = \
                        GroupPackageListing(group_name)
                #pylint:enable-msg=E1101
            clone_group = clone_branch.groups2[group_name]
            for acl_name, acl in group.acls2.iteritems():
                if acl_name not in clone_group.acls2:
                    clone_group.acls2[acl_name] = \
                            GroupPackageListingAcl(acl_name, acl.statuscode)
                else:
                    # Set the acl to have the correct status
                    if acl.statuscode != clone_group.acls2[acl_name].statuscode:
                        clone_group.acls2[acl_name].statuscode = acl.statuscode

                # Create a log message for this acl
                log_params['acl'] = acl.acl
                log_params['status'] = acl.status.locale['C'].statusname
                log_msg = '%(user)s set %(acl)s status for %(group)s to' \
                        ' %(status)s on (%(pkg)s %(branch)s)' % log_params
                log = GroupPackageListingAclLog(author_name,
                        acl.statuscode, log_msg)
                log.acl = clone_group.acls2[acl_name]

        #pylint:disable-msg=E1101
        for person_name, person in self.people2.iteritems():
        #pylint:enable-msg=E1101
            log_params['person'] = person_name
            if person_name not in clone_branch.people2:
                # Associate the person with the packagelisting
                #pylint:disable-msg=E1101
                clone_branch.people2[person_name] = \
                        PersonPackageListing(person_name)
                #pylint:enable-msg=E1101
            clone_person = clone_branch.people2[person_name]
            for acl_name, acl in person.acls2.iteritems():
                if acl_name not in clone_person.acls2:
                    clone_person.acls2[acl_name] = \
                            PersonPackageListingAcl(acl_name, acl.statuscode)
                else:
                    # Set the acl to have the correct status
                    if clone_person.acls2[acl_name].statuscode \
                            != acl.statuscode:
                        clone_person.acls2[acl_name].statuscode = acl.statuscode
                # Create a log message for this acl
                log_params['acl'] = acl.acl
                log_params['status'] = acl.status.locale['C'].statusname
                log_msg = '%(user)s set %(acl)s status for %(person)s to' \
                        ' %(status)s on (%(pkg)s %(branch)s)' % log_params
                log = PersonPackageListingAclLog(author_name,
                        acl.statuscode, log_msg)
                log.acl = clone_person.acls2[acl_name]

        return clone_branch

def collection_alias(pkg_listing):
    '''Return the collection_alias that a package listing belongs to.

    :arg pkg_listing: PackageListing to find the Collection for.
    :returns: Collection Alias.  This is either the branchname or a combination
        of the collection name and version.

    This is used to make Branch keys for the dictionary mapping of pkg listings
    into packages.
    '''
    return pkg_listing.collection.simple_name
