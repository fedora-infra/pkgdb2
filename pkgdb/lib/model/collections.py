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
Mapping of collection and repo related database tables to python classes
'''

from sqlalchemy.orm import polymorphic_union, relation, backref
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm.collections import attribute_mapped_collection
import sqlalchemy as sa


from pkgdb.lib.model.packages import PackageListing

from pkgdb.lib.model import BASE


CollectionJoin = polymorphic_union (
        {'b' : select((CollectionTable.join(
            BranchTable, CollectionTable.c.id == BranchTable.c.collectionid),)),
         'c' : select((CollectionTable,),
             not_(CollectionTable.c.id.in_(select(
                 (CollectionTable.c.id,),
                 CollectionTable.c.id == BranchTable.c.collectionid)
             )))
         },
        'kind', 'CollectionJoin'
        )

#
# Mapped Classes
#

class Collection(BASE):
    '''A Collection of packages.

    Table -- Collection
    '''

    __tablename__ = 'Collection'
    id = sa.Column(sa.Integer, nullable=False, primary_key=True)
    name = sa.Column(sa.Text, nullable=False)
    version = sa.Column(sa.Text, nullable=False)
    statuscode = sa.Column(sa.Integer,
                           sa.ForeignKey('CollectionStatusCode.statusCodeId',
                                         ondelete="RESTRICT",
                                         onupdate="CASCADE"
                                         ),
                           nullable=False)
    owner = sa.Column(sa.Integer, nullable=False)
    publishURLTemplate = sa.Column(sa.Text)
    pendingURLTemplate = sa.Column(sa.Text)
    summary = sa.Column(sa.Text)
    description = sa.Column(sa.Text)

    __table_args__ = (
        sa.UniqueConstraint('name', 'version'),
    )

    # pylint: disable-msg=R0902, R0903
    def __init__(self, name, version, statuscode, owner,
            publishurltemplate=None, pendingurltemplate=None, summary=None,
            description=None):
        # pylint: disable-msg=R0913
        super(Collection, self).__init__()
        self.name = name
        self.version = version
        self.statuscode = statuscode
        self.owner = owner
        self.publishurltemplate = publishurltemplate
        self.pendingurltemplate = pendingurltemplate
        self.summary = summary
        self.description = description

    def __repr__(self):
        return 'Collection(%r, %r, %r, %r, publishurltemplate=%r,' \
                ' pendingurltemplate=%r, summary=%r, description=%r)' % (
                self.name, self.version, self.statuscode, self.owner,
                self.publishurltemplate, self.pendingurltemplate,
                self.summary, self.description)

    def api_repr(self, version):
        """ Used by fedmsg to serialize Collections in messages. """
        if version == 1:
            return dict(
                name=self.name,
                version=self.version,
                publishurltemplate=self.publishurltemplate,
                pendingurltemplate=self.pendingurltemplate,
            )
        else:
            raise NotImplementedError("Unsupported version %r" % version)

    @property
    def simple_name(self):
        '''Return a simple name for the Collection
        '''
        try:
            # :E1101: If Collection is actually a branch, it will have a
            # branchname attribute given it by SQLAlchemy
            # pylint: disable-msg=E1101
            simple_name = self.branchname
        except AttributeError:
            simple_name = '-'.join((self.name, self.version))
        return simple_name

    @classmethod
    def by_simple_name(cls, simple_name):
        '''Return the Collection that matches the simple name

        :arg simple_name: simple name for a Collection
        :returns: The Collection that matches the name
        :raises sqlalchemy.InvalidRequestError: if the simple name is not found

        simple_name will be looked up first as the Branch name.  Then as the
        Collection name joined by a hyphen with the version.  ie:
        'Fedora EPEL-5'.
        '''
        # :E1101: SQLAlchemy adds many methods to the Branch and Collection
        # classes
        # pylint: disable-msg=E1101
        try:
            collection = Branch.query.filter_by(branchname=simple_name).one()
        except InvalidRequestError:
            name, version = simple_name.rsplit('-')
            collection = Collection.query.filter_by(name=name,
                    version=version).one()
        return collection


class Branch(Collection):
    '''Collection that has a physical existence.

    Some Collections are only present as a name and collection of packages.  The
    Collections that have a branch record are also present in our VCS and
    download repositories.

    Table -- Branch
    '''

    __tablename__ = 'Branch'
    collectionId = sa.Column(sa.Integer,
                             sa.ForeignKey('Collection.id',
                                         ondelete="CASCADE",
                                         onupdate="CASCADE"
                                         ),
                             nullable=False,
                             primary_key=True,
                             )
    branchName = sa.Column(sa.String(32), unique=True, nullable=False)
    distTag = sa.Column(sa.String(32), unique=True, nullable=False)
    parentId = sa.Column(sa.Integer,
                         sa.ForeignKey('Collection.id',
                                         ondelete="SET NULL",
                                         onupdate="CASCADE"
                                         ),
                           nullable=False,
                           )

    # pylint: disable-msg=R0902, R0903
    def __init__(self, collectionid, branchname, disttag, parentid,
                 gitbranchname=None, *args):
        # pylint: disable-msg=R0913
        branch_mapping = {'F-13': 'f13', 'F-12': 'f12', 'F-11': 'f11',
                          'F-10': 'f10', 'F-9': 'f9', 'F-8': 'f8',
                          'F-7': 'f7', 'FC-6': 'fc6', 'EL-6': 'el6',
                          'EL-5': 'el5', 'EL-4':'el4', 'OLPC-3': 'olpc3'}

        super(Branch, self).__init__(args)
        self.collectionid = collectionid
        self.branchname = branchname
        self.disttag = disttag
        self.parentid = parentid

        if (not gitbranchname):
            if (branchname in branch_mapping):
                self.gitbranchname = branch_mapping[branchname]

    def __repr__(self):
        return 'Branch(%r, %r, %r, %r, %r, %r, %r, %r,' \
                ' publishurltemplate=%r, pendingurltemplate=%r,' \
                ' summary=%r, description=%r, gitbranchname=%r)' % \
                (self.collectionid, self.branchname, self.disttag,
                 self.parentid, self.name, self.version, self.statuscode,
                 self.owner, self.publishurltemplate, self.pendingurltemplate,
                 self.summary, self.description, self.gitbranchname)

    def api_repr(self, version):
        """ Used by fedmsg to serialize Branches in messages. """
        if version == 1:
            return dict(
                name=self.name,
                version=self.version,
                publishurltemplate=self.publishurltemplate,
                pendingurltemplate=self.pendingurltemplate,
                branchname=self.branchname,
                disttag=self.disttag,
            )
        else:
            raise NotImplementedError("Unsupported version %r" % version)

## TODO: this was not described in the pkgdb.sql file
class Repo(BASE):
    '''Repos are actual yum repositories.

    Table -- Repos
    '''
    def __init__(self, name, shortname, url, mirror, active, collectionid):
        super(Repo, self).__init__()
        self.name  = name
        self.shortname = shortname
        self.url = url
        self.mirror = mirror
        self.active = active
        self.collectionid = collectionid

    def __repr__(self):
        return 'Repo(%r, %r, url=%r, mirror=%r, active=%r, collectionid=%r)' % (
            self.name, self.shortname, self.url, self.mirror, self.active,

            self.collectionid)

## TODO: this is a view, create it as such...
class CollectionPackage(BASE):
    '''Information about how many `Packages` are in a `Collection`

    View -- CollectionPackage
    '''

    __tablename__ = 'CollectionPackage'
    id = sa.Column(sa.Integer, nullable=False, primary_key=True)
    statuscode = sa.Column(sa.Integer,
                           sa.ForeignKey('collectionstatuscode.statuscodeid'),
                           )

    # pylint: disable-msg=R0902, R0903
    def __repr__(self):
        # pylint: disable-msg=E1101
        return 'CollectionPackage(id=%r, name=%r, version=%r,' \
            ' statuscode=%r, numpkgs=%r,' \
                % (self.id, self.name, self.version, self.statuscode,
                   self.numpkgs)

#
# TODO: port this part of the code to declarative
#

#mapper(Collection, CollectionJoin,
        #polymorphic_on=CollectionJoin.c.kind,
        #polymorphic_identity='c',
        #with_polymorphic='*',
        #properties={
            ## listings is deprecated.  It will go away in 0.4.x
            #'listings': relation(PackageListing),
            ## listings2 is slower than listings.  It has a front-end cost to
            ## load the data into the dict.  However, if we're using listings
            ## to search for multiple packages, this will likely be faster.
            ## Have to look at how it's being used in production and decide
            ## what to do.
            #'listings2': relation(PackageListing,
                #backref=backref('collection'),
                #collection_class=attribute_mapped_collection('packagename')),
            #'repos': relation(Repo, backref=backref('collection'))
        #})

## No idea how to implement this part
#mapper(Branch, BranchTable, inherits=Collection,
        #inherit_condition=CollectionJoin.c.id==BranchTable.c.collectionid,
        #polymorphic_identity='b')
