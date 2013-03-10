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
Mapping of python classes to Database Tables.
'''

__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

import datetime
import logging

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import relation
from sqlalchemy.orm import backref
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.collections import mapped_collection
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import and_
from sqlalchemy.sql.expression import Executable, ClauseElement

BASE = declarative_base()

error_log = logging.getLogger('pkgdb.lib.model.packages')

DEFAULT_GROUPS = {'provenpackager': {'commit': True}}


def create_tables(db_url, alembic_ini=None, debug=False):
    """ Create the tables in the database using the information from the
    url obtained.

    :arg db_url, URL used to connect to the database. The URL contains
        information with regards to the database engine, the host to
        connect to, the user and password and the database name.
          ie: <engine>://<user>:<password>@<host>/<dbname>
    :kwarg alembic_ini, path to the alembic ini file. This is necessary
        to be able to use alembic correctly, but not for the unit-tests.
    :kwarg debug, a boolean specifying wether we should have the verbose
        output of sqlalchemy or not.
    :return a session that can be used to query the database.

    """
    engine = create_engine(db_url, echo=debug)
    BASE.metadata.create_all(engine)
    engine.execute(collection_package_create_view(driver=engine.driver))

    if alembic_ini is not None:  # pragma: no cover
        # then, load the Alembic configuration and generate the
        # version table, "stamping" it with the most recent rev:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config(alembic_ini)
        command.stamp(alembic_cfg, "head")

    sessionmak = sessionmaker(bind=engine)
    return sessionmak()


## TODO: this is a view, create it as such...
class CollectionPackage(Executable, ClauseElement):
    '''Information about how many `Packages` are in a `Collection`

    View -- CollectionPackage
    '''

    __tablename__ = 'CollectionPackage'
    id = sa.Column(sa.Integer, nullable=False, primary_key=True)
    name = sa.Column(sa.Text, nullable=False)
    version = sa.Column(sa.Text, nullable=False)
    status = sa.Column(sa.Enum('EOL', 'Active', 'Under Development',
                                name='collection_status'),
                        nullable=False)
    numpkgs = sa.Column(sa.Integer, nullable=False)

    # pylint: disable-msg=R0902, R0903
    def __repr__(self):
        # pylint: disable-msg=E1101
        return 'CollectionPackage(id=%r, name=%r, version=%r,' \
            ' status=%r, numpkgs=%r,' \
                % (self.id, self.name, self.version, self.status,
                   self.numpkgs)


@compiles(CollectionPackage)
def collection_package_create_view(*args, **kw):
    sql_string = 'CREATE OR REPLACE VIEW'
    if 'driver' in kw:
        if kw['driver'] == 'pysqlite':
            sql_string = 'CREATE VIEW IF NOT EXISTS'
    return '%s CollectionPackage AS '\
    'SELECT c.id, c.name, c.version, c.status, count(*) as numpkgs '\
    'FROM "PackageListing" pl, "Collection" c '\
    'WHERE pl.collectionid = c.id '\
    'AND pl.status = "Approved" '\
    'GROUP BY c.id, c.name, c.version, c.status '\
    'ORDER BY c.name, c.version;' % sql_string


class PersonPackageListingAcl(BASE):
    '''Acl on a package that a person owns.

    Table -- PersonPackageListingAcl
    '''

    __tablename__ = 'PersonPackageListingAcl'

    id = sa.Column(sa.Integer, primary_key=True)
    acl = sa.Column(sa.Enum('commit', 'build', 'watchbugzilla',
                            'watchcommits', 'approveacls',
                            name='acl'),
                    nullable=False
                    )
    status = sa.Column(sa.Enum('Approved', 'Awaiting Review', 'Denied',
                               'Obsolete', 'Removed',
                               name='package_status'),
                        nullable=False)
    personpackagelistingid = sa.Column(sa.Integer,
                                       sa.ForeignKey('PersonPackageListing.id',
                                                     ondelete='CASCADE',
                                                     onupdate='CASCADE'
                                                     ),
                                       nullable=False,
                                       )

    date_created = sa.Column(sa.DateTime, nullable=False,
                             default=datetime.datetime.utcnow())

    __table_args__ = (
        sa.UniqueConstraint('personpackagelistingid', 'acl'),
    )

    @classmethod
    def all(cls, session):
        ''' Return the list of all Collections present in the database.

        :arg cls: the class object
        :arg session: the database session used to query the information.

        '''
        return session.query(cls).all()

    @classmethod
    def get_or_create_personpkgid_acl(cls, session, personpkg_id, acl):
        """ Return the PersonPackageListingAcl for the provided
        PersonPackageListing identifier and ACL.
        
        :arg session:
        :arg personpkg_id:
        :arg acl:
        """
        try:
            pkgacl = session.query(cls).filter_by(personpackagelistingid=personpkg_id
                                                  ).filter_by(acl=acl).one()
        except NoResultFound:
            pkgacl = PersonPackageListingAcl(personpackagelistingid=personpkg_id,
                                             status=None,
                                             acl=acl)
        return pkgacl

    def __init__(self, acl, status, personpackagelistingid):
        self.personpackagelistingid = personpackagelistingid
        self.acl = acl
        self.status = status

    def __repr__(self):
        return 'PersonPackageListingAcl(%r, %r, personpackagelistingid=%r)' \
            % (self.acl, self.status, self.personpackagelistingid)


class GroupPackageListingAcl(BASE):
    '''Acl on a package that a group owns.

    Table -- GroupPackageListingAcl
    '''

    __tablename__ = 'GroupPackageListingAcl'

    id = sa.Column(sa.Integer, primary_key=True)
    acl = sa.Column(sa.Enum('commit', 'build', 'watchbugzilla',
                            'watchcommits', 'approveacls',
                            name='acl'),
                    nullable=False
                    )
    status = sa.Column(sa.Enum('Approved', 'Awaiting Review', 'Denied',
                               'Obsolete', 'Removed',
                               name='package_status'),
                        nullable=False)
    group_packagelisting_id = sa.Column(sa.Integer,
                                      sa.ForeignKey('GroupPackageListing.id',
                                                    ondelete='CASCADE',
                                                    onupdate='CASCADE'
                                                    ),
                                      nullable=False,
                                      )

    date_created = sa.Column(sa.DateTime, nullable=False,
                             default=datetime.datetime.utcnow())

    __table_args__ = (
        sa.UniqueConstraint('group_packagelisting_id', 'acl'),
    )

    def __init__(self, acl, status=None, group_packagelisting_id=None):
        self.group_packagelisting_id = group_packagelisting_id
        self.acl = acl
        self.status = status

    def __repr__(self):
        return 'GroupPackageListingAcl(%r, %r, group_packagelisting_id=%r)'\
            % (self.acl, self.status, self.group_packagelisting_id)


class PersonPackageListing(BASE):
    '''Associate a person with a PackageListing.

    People who are watching or can modify a packagelisting.

    Table -- PersonPackageListing
    '''

    __tablename__ = 'PersonPackageListing'

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, nullable=False)
    packagelisting_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('PackageListing.id',
                      ondelete='CASCADE',
                      onupdate='CASCADE'
                      ),
        nullable=False,
    )

    acls = relation(PersonPackageListingAcl)
    acls2 = relation(PersonPackageListingAcl,
                     backref=backref('personpackagelisting'),
                     collection_class=attribute_mapped_collection('acl')
                     )

    date_created = sa.Column(sa.DateTime, nullable=False,
                             default=datetime.datetime.utcnow())

    __table_args__ = (
        sa.UniqueConstraint('user_id', 'packagelisting_id'),
    )

    @classmethod
    def all(cls, session):
        ''' Return the list of all Collections present in the database.

        :arg cls: the class object
        :arg session: the database session used to query the information.

        '''
        return session.query(cls).all()

    @classmethod
    def by_userid_pkglistid(cls, session, user_id, packagelisting_id):
        return session.query(cls).filter(
        PersonPackageListing.user_id == user_id).filter(
        PersonPackageListing.packagelisting_id == packagelisting_id).one()

    @classmethod
    def get_or_create(cls, session, user_id, packagelisting_id):
        """ Retrieve the PersonPackageListing which associates a person
        with a package in a certain collection.

        :arg session: the database session used to connect to the
            database
        :arg user_id: the identifier (integer) of the user
        :arg packagelisting_id: the identifier of the PackageListing
            entry.
        """
        try:
            personpkg = session.query(cls).filter(
        PersonPackageListing.user_id == user_id).filter(
        PersonPackageListing.packagelisting_id == packagelisting_id).one()
        except NoResultFound:
            personpkg = PersonPackageListing(user_id=user_id,
                                             packagelisting_id=packagelisting_id)
            session.add(personpkg)
            session.flush()

        return personpkg


    # pylint: disable-msg=R0903
    def __init__(self, user_id, packagelisting_id):
        self.user_id = user_id
        self.packagelisting_id = packagelisting_id

    def __repr__(self):
        return 'PersonPackageListing(%r, %r)' % (self.user_id,
                                                 self.packagelisting_id)


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
                      ondelete='CASCADE',
                      onupdate='CASCADE'
                      ),
        nullable=False,
    )

    acls = relation(GroupPackageListingAcl)
    acls2 = relation(GroupPackageListingAcl,
                     backref=backref('grouppackagelisting'),
                     collection_class=attribute_mapped_collection('acl')
                     )

    date_created = sa.Column(sa.DateTime, nullable=False,
                             default=datetime.datetime.utcnow())

    __table_args__ = (
        sa.UniqueConstraint('groupid', 'packageListingId'),
    )

    def __init__(self, groupname, packagelistingid=None):
        self.groupname = groupname
        self.packagelistingid = packagelistingid

    def __repr__(self):
        return 'GroupPackageListing(%r, %r)' % (self.groupname,
                                                self.packagelistingid)

class Collection(BASE):
    '''A Collection of packages.

    Table -- Collection
    '''

    __tablename__ = 'Collection'
    id = sa.Column(sa.Integer, nullable=False, primary_key=True)
    name = sa.Column(sa.Text, nullable=False)
    version = sa.Column(sa.Text, nullable=False)
    status = sa.Column(sa.Enum('EOL', 'Active', 'Under Development',
                                name='collection_status'),
                        nullable=False)
    owner = sa.Column(sa.Integer, nullable=False)
    publishURLTemplate = sa.Column(sa.Text)
    pendingURLTemplate = sa.Column(sa.Text)
    summary = sa.Column(sa.Text)
    description = sa.Column(sa.Text)
    branchname = sa.Column(sa.String(32), unique=True, nullable=False)
    distTag = sa.Column(sa.String(32), unique=True, nullable=False)
    git_branch_name = sa.Column(sa.Text)

    date_created = sa.Column(sa.DateTime, nullable=False,
                             default=datetime.datetime.utcnow())

    __table_args__ = (
        sa.UniqueConstraint('name', 'version'),
    )

    # pylint: disable-msg=R0902, R0903
    def __init__(self, name, version, status, owner,
            publishurltemplate=None, pendingurltemplate=None, summary=None,
            description=None, branchname=None, distTag=None,
            git_branch_name=None):
        self.name = name
        self.version = version
        self.status = status
        self.owner = owner
        self.publishURLTemplate = publishurltemplate
        self.pendingURLTemplate = pendingurltemplate
        self.summary = summary
        self.description = description
        self.branchname = branchname
        self.distTag = distTag
        self.git_branch_name = git_branch_name

    def __repr__(self):
        return 'Collection(%r, %r, %r, %r, publishurltemplate=%r,' \
                ' pendingurltemplate=%r, summary=%r, description=%r)' % (
                self.name, self.version, self.status, self.owner,
                self.publishURLTemplate, self.pendingURLTemplate,
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

    @classmethod
    def by_name(cls, session, branch_name):
        '''Return the Collection that matches the simple name

        :arg branch_name: branch name for a Collection
        :returns: The Collection that matches the name
        :raises sqlalchemy.InvalidRequestError: if the simple name is not found

        simple_name will be looked up as the Branch name.
        '''
        collection = session.query(cls).filter(
            Collection.branchname == branch_name).one()
        return collection

    @classmethod
    def all(cls, session):
        ''' Return the list of all Collections present in the database.

        :arg cls: the class object
        :arg session: the database session used to query the information.

        '''
        return session.query(cls).all()


def collection_alias(pkg_listing):
    '''Return the collection_alias that a package listing belongs to.

    :arg pkg_listing: PackageListing to find the Collection for.
    :returns: Collection Alias.  This is either the branchname or a combination
        of the collection name and version.

    This is used to make Branch keys for the dictionary mapping of pkg listings
    into packages.
    '''
    return pkg_listing.collection.simple_name

# Package and PackageListing are straightforward translations.  Look at these
# if you're looking for a straightforward example.

class PackageListing(BASE):
    '''This associates a package with a particular collection.

    Table -- PackageListing
    '''

    __tablename__ = 'PackageListing'
    id = sa.Column(sa.Integer, nullable=False, primary_key=True)
    packageid = sa.Column(sa.Integer,
                          sa.ForeignKey('Package.id',
                                         ondelete="CASCADE",
                                         onupdate="CASCADE"
                                         ),
                          nullable=False)
    collectionid = sa.Column(sa.Integer,
                          sa.ForeignKey('Collection.id',
                                         ondelete="CASCADE",
                                         onupdate="CASCADE"
                                         ),
                          nullable=False)
    owner = sa.Column(sa.Integer, nullable=False)
    qacontact = sa.Column(sa.Integer)
    status = sa.Column(sa.Enum('Approved', 'Removed', 'Deprecated', 'Orphaned',
                                name='pl_status'),
                        nullable=False)
    statuschange = sa.Column(sa.DateTime, nullable=False,
                             default=datetime.datetime.utcnow())
    __table_args__ = (
        sa.UniqueConstraint('packageid', 'collectionid'),
    )

    package = relation("Package")
    collection = relation("Collection")
    people = relation(PersonPackageListing)
    people2 = relation(PersonPackageListing, backref=backref('packagelisting'),
        collection_class = attribute_mapped_collection('username'))
    groups = relation(GroupPackageListing)
    groups2 = relation(GroupPackageListing, backref=backref('packagelisting'),
        collection_class = attribute_mapped_collection('groupname'))

    def __init__(self, owner, status, packageid=None, collectionid=None,
            qacontact=None):
        self.packageid = packageid
        self.collectionid = collectionid
        self.owner = owner
        self.qacontact = qacontact
        self.status = status

    packagename = association_proxy('package', 'name')

    @classmethod
    def by_package_id(cls, session, pkgid):
        """ Return the PackageListing object based on the Package ID.

        :arg pkgid: Integer, identifier of the package in the Package
            table

        """

        return session.query(cls).filter(PackageListing.packageid == pkgid).all()

    @classmethod
    def by_pkgid_collectionid(cls, session, pkgid, collectionid):
        '''Return the PackageListing for the provided package in the
        specified collection.

        :arg pkgid: Integer, identifier of the package in the Package
            table
        :arg collectionid: Integer, identifier of the collection in the
            Collection table
        :returns: The PackageListing that matches this package identifier
            and collection iddentifier
        :raises sqlalchemy.InvalidRequestError: if the simple name is not found

        '''
        return session.query(cls).filter(
            PackageListing.packageid == pkgid).filter(
            PackageListing.collectionid == collectionid).one()

    def __repr__(self):
        return 'PackageListing(%r, %r, packageid=%r, collectionid=%r,' \
               ' qacontact=%r)' % (self.owner, self.status,
                        self.packageid, self.collectionid, self.qacontact)

    def api_repr(self, version):
        """ Used by fedmsg to serialize PackageListing in messages. """
        if version == 1:
            return dict(
                package=self.package.api_repr(version),
                collection=self.collection.api_repr(version),
                owner=self.owner,
                qacontact=self.qacontact,
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
        # Retrieve the PackageListing for the to clone branch
        try:
            #pylint:disable-msg=E1101
            clone_branch = PackageListing.query.join('package'
                    ).join('collection').filter(
                        and_(Package.name==self.package.name,
                            Collection.branchname==branch)).one()
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
                      'pkg': self.package.name,
                      'branch': branch}
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
                            GroupPackageListingAcl(acl_name, acl.status)
                else:
                    # Set the acl to have the correct status
                    if acl.status != clone_group.acls2[acl_name].status:
                        clone_group.acls2[acl_name].status = acl.status

                #TODO: Create a log message for this acl

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
                            PersonPackageListingAcl(acl_name, acl.status)
                else:
                    # Set the acl to have the correct status
                    if clone_person.acls2[acl_name].status \
                            != acl.status:
                        clone_person.acls2[acl_name].status = acl.status
                #TODO: Create a log message for this acl

        return clone_branch


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
    review_url = sa.Column(sa.Text)
    upstream_url = sa.Column(sa.Text)
    status = sa.Column(sa.Enum('Approved', 'Awaiting Review', 'Denied',
                                'Obsolete', 'Removed',
                                name='package_status'),
                        nullable=False)
    shouldopen = sa.Column(sa.Boolean, nullable=False, default=True)

    listings = relation(PackageListing)
    listings2 = relation(PackageListing,
                         #backref=backref('package'),
                         collection_class=mapped_collection(collection_alias)
                         )

    date_created = sa.Column(sa.DateTime, nullable=False,
                             default=datetime.datetime.utcnow())

    @classmethod
    def by_name(cls, session, pkgname):
        """ Return the package associated to the given name.

        :raises sqlalchemy.InvalidRequestError: if the package name is not found
        """
        return session.query(cls).filter(Package.name == pkgname).one()

    def __init__(self, name, summary, status, reviewurl=None,
                 shouldopen=None, review_url=None, upstream_url=None):
        self.name = name
        self.summary = summary
        self.status = status
        self.review_url = review_url
        self.shouldopen = shouldopen
        self.upstream_url = upstream_url

    def __repr__(self):
        return 'Package(%r, %r, %r, ' \
               'upstreamurl=%r, reviewurl=%r, shouldopen=%r)' % (
                self.name, self.summary, self.status,
                self.upstream_url, self.review_url, self.shouldopen)

    def api_repr(self, version):
        """ Used by fedmsg to serialize Packages in messages. """
        if version == 1:
            return dict(
                name=self.name,
                summary=self.summary,
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
        pkg_listing = PackageListing(owner=owner,
                                     status=statusname,
                                     collectionid=collection.id,
                                     qacontact=qacontact)
        pkg_listing.packageid = self.id
        for group in DEFAULT_GROUPS:
            new_group = GroupPackageListing(groupname=group,
                                            packagelistingid=pkg_listing.id)
            #pylint:disable-msg=E1101
            #pkg_listing.groups2[group] = new_group
            #pylint:enable-msg=E1101
            for acl, status in DEFAULT_GROUPS[group].iteritems():
                if status:
                    acl_status = 'Approved'
                else:
                    acl_status = 'Denied'
                group_acl = GroupPackageListingAcl(acl=acl,
                                                   status=acl_status,
                                                   group_packagelisting_id=new_group.id)

        #TODO: Create a log message

        return pkg_listing

    @classmethod
    def all(cls, session):
        ''' Return the list of all Collections present in the database.

        :arg cls: the class object
        :arg session: the database session used to query the information.

        '''
        return session.query(cls).all()


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
