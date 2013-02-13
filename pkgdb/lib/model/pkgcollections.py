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
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Executable, ClauseElement

import sqlalchemy as sa

from packages import PackageListing

from sqlalchemy.ext.declarative import declarative_base
BASE = declarative_base()


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
    branchName = sa.Column(sa.String(32), unique=True, nullable=False)
    distTag = sa.Column(sa.String(32), unique=True, nullable=False)
    git_branch_name = sa.Column(sa.Text)

    __table_args__ = (
        sa.UniqueConstraint('name', 'version'),
    )

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

    ## TODO: is this correct? -- Should be what is above
    __mapper_args__ = {
        'polymorphic_on': CollectionJoin.c.kind,
        'polymorphic_identity': 'c',
        'with_polymorphic': '*',
        'properties': {
            'listings': relation(PackageListing),
            'listings2': relation(
                PackageListing,
                backref=backref('collection'),
                collection_class=attribute_mapped_collection('packagename')
            ),
            'repos': relation(Repo, backref=backref('collection'))
        }
    }

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


## TODO: this is a view, create it as such...
class CollectionPackage(Executable, ClauseElement):
    '''Information about how many `Packages` are in a `Collection`

    View -- CollectionPackage
    '''

    __tablename__ = 'CollectionPackage'
    id = sa.Column(sa.Integer, nullable=False, primary_key=True)
    name = sa.Column(sa.Text, nullable=False)
    version = sa.Column(sa.Text, nullable=False)
    statuscode = sa.Column(sa.Integer,
                           sa.ForeignKey('CollectionStatusCode.statusCodeId',
                                         ondelete="RESTRICT",
                                         onupdate="CASCADE"
                                         ),
                           nullable=False)
    numpkgs = sa.Column(sa.Integer, nullable=False)

    # pylint: disable-msg=R0902, R0903
    def __repr__(self):
        # pylint: disable-msg=E1101
        return 'CollectionPackage(id=%r, name=%r, version=%r,' \
            ' statuscode=%r, numpkgs=%r,' \
                % (self.id, self.name, self.version, self.statuscode,
                   self.numpkgs)



@compiles(CollectionPackage)
def collection_package_create_view(*args, **kw):
    return "select c.id, c.name, c.version, c.statuscode, count(*) as numpkgs "\
    "from packagelisting as pl, collection as c "\
    "where pl.collectionid = c.id "\
    "and pl.statuscode = 3 "\
    "group by c.id, c.name, c.version, c.statuscode "\
    "order by c.name, c.version;"
