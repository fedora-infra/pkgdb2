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
    engine.execute(collection_package_create_view())

    if alembic_ini is not None:
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
                                name='status'),
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
    return "CREATE OR REPLACE VIEW CollectionPackage AS "\
    "SELECT c.id, c.name, c.version, c.status, count(*) as numpkgs "\
    "FROM \"PackageListing\" pl, \"Collection\" c "\
    "WHERE pl.collectionid = c.id "\
    "AND pl.status = 'Approved' "\
    "GROUP BY c.id, c.name, c.version, c.status "\
    "ORDER BY c.name, c.version;"


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
    status = sa.Column(sa.Enum('Approved', 'Awaiting Review', 'Denied', 'Obsolete',
                                name='status'),
                        nullable=False)
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

    def __init__(self, acl, status=None,
                 personpackagelistingid=None):
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
    status = sa.Column(sa.Enum('Approved', 'Awaiting Review', 'Denied', 'Obsolete',
                                name='status'),
                        nullable=False)
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
        sa.UniqueConstraint('user_id', 'packageListingId'),
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

class Collection(BASE):
    '''A Collection of packages.

    Table -- Collection
    '''

    __tablename__ = 'Collection'
    id = sa.Column(sa.Integer, nullable=False, primary_key=True)
    name = sa.Column(sa.Text, nullable=False)
    version = sa.Column(sa.Text, nullable=False)
    status = sa.Column(sa.Enum('EOL', 'Active', 'Under Development',
                                name='status'),
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

    # pylint: disable-msg=R0902, R0903
    def __init__(self, name, version, status, owner,
            publishurltemplate=None, pendingurltemplate=None, summary=None,
            description=None):
        self.name = name
        self.version = version
        self.status = status
        self.owner = owner
        self.publishurltemplate = publishurltemplate
        self.pendingurltemplate = pendingurltemplate
        self.summary = summary
        self.description = description

    def __repr__(self):
        return 'Collection(%r, %r, %r, %r, publishurltemplate=%r,' \
                ' pendingurltemplate=%r, summary=%r, description=%r)' % (
                self.name, self.version, self.status, self.owner,
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
                                name='status'),
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
            qacontact=None, specfile=None):
        self.packageid = packageid
        self.collectionid = collectionid
        self.owner = owner
        self.qacontact = qacontact
        self.status = status
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
        from pkgdb.lib.model.collections import Branch
        from pkgdb.lib.model.logs import GroupPackageListingAclLog, \
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
                            GroupPackageListingAcl(acl_name, acl.status)
                else:
                    # Set the acl to have the correct status
                    if acl.status != clone_group.acls2[acl_name].status:
                        clone_group.acls2[acl_name].status = acl.status

                # Create a log message for this acl
                log_params['acl'] = acl.acl
                log_params['status'] = acl.status
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
                            PersonPackageListingAcl(acl_name, acl.status)
                else:
                    # Set the acl to have the correct status
                    if clone_person.acls2[acl_name].status \
                            != acl.status:
                        clone_person.acls2[acl_name].status = acl.status
                # Create a log message for this acl
                log_params['acl'] = acl.acl
                log_params['status'] = acl.status
                log_msg = '%(user)s set %(acl)s status for %(person)s to' \
                        ' %(status)s on (%(pkg)s %(branch)s)' % log_params
                log = PersonPackageListingAclLog(author_name,
                        acl.status, log_msg)
                log.acl = clone_person.acls2[acl_name]

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
    description = sa.Column(sa.Text)
    reviewURL = sa.Column(sa.Text)
    status = sa.Column(sa.Enum('Approved', 'Awaiting Review', 'Denied',
                                'Obsolete', 'Removed',
                                name='status'),
                        nullable=False)
    shouldopen = sa.Column(sa.Boolean, nullable=False, default=True)

    listings = relation(PackageListing)
    listings2 = relation(PackageListing,
                         backref=backref('package'),
                         collection_class=mapped_collection(collection_alias)
                         )

    def __init__(self, name, summary, status, description=None,
            reviewurl=None, shouldopen=None, upstreamurl=None):
        self.name = name
        self.summary = summary
        self.status = status
        self.description = description
        self.reviewurl = reviewurl
        self.shouldopen = shouldopen
        self.upstreamurl = upstreamurl

    def __repr__(self):
        return 'Package(%r, %r, %r, description=%r, ' \
               'upstreamurl=%r, reviewurl=%r, shouldopen=%r)' % (
                self.name, self.summary, self.status, self.description,
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
                group_acl = GroupPackageListingAcl(acl, acl_status)
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


if __name__ == '__main__':
    db_url = 'sqlite:///pkgdb2.sqlite'
    debug = True
    create_tables(db_url, debug=debug)
