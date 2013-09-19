#!/usr/bin/env python2
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
Utility script to convert a pkgdb1 database to the pkgdb2 data model.

Note: It will need the SQLAlchemy database url filled at the top of this
file.

'''

import sys
import os

import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy.exc

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import pkgdb.lib
from pkgdb.lib import model


DB_URL_PKGDB1= ''
DB_URL_PKGDB2= ''


STATUS = {
    1: 'Active',
    2: 'Added',
    3: 'Approved',
    4: 'Awaiting Branch',
    5: 'Awaiting Development',
    6: 'Awaiting QA',
    7: 'Awaiting Publish',
    8: 'Awaiting Review',
    9: 'EOL',
    10: 'Denied',
    11: 'Maintenence',
    12: 'Modified',
    13: 'Obsolete',
    14: 'Orphaned',
    15: 'Owned',
    16: 'Rejected',
    17: 'Removed',
    18: 'Under Development',
    19: 'Under Review',
    20: 'Retired',
}


class P1Collection(object):
    pass


class P1Branch(object):
    pass


class P1Package(object):
    pass


class P1Packagelisting(object):
    pass


class P1PersonPackagelisting(object):
    pass


class P1PersonPackagelistingAcl(object):
    pass


def create_session(db_url, debug=False):
    ''' Return a SQLAlchemy session connecting to the provided database.
    This is assuming the db_url provided has the right information.

    '''
    engine = sa.create_engine(db_url, echo=debug)

    metadata = sa.MetaData(engine)
    table = sa.Table('collection', metadata, autoload=True)
    sa.orm.mapper(P1Collection, table)
    table = sa.Table('branch', metadata, autoload=True)
    sa.orm.mapper(P1Branch, table)
    table = sa.Table('package', metadata, autoload=True)
    sa.orm.mapper(P1Package, table)
    table = sa.Table('packagelisting', metadata, autoload=True)
    sa.orm.mapper(P1Packagelisting, table)
    table = sa.Table('personpackagelisting', metadata, autoload=True)
    sa.orm.mapper(P1PersonPackagelisting, table)
    table = sa.Table('personpackagelistingacl', metadata, autoload=True)
    sa.orm.mapper(P1PersonPackagelistingAcl, table)

    scopedsession = orm.scoped_session(orm.sessionmaker(bind=engine))
    return scopedsession


def convert_collections(pkg1_sess, pkg2_sess):
    ''' Convert the Collection from pkgdb1 to pkgdb2.
    '''
    cnt = 0
    for collect in pkg1_sess.query(P1Collection).all():
        branch = pkg1_sess.query(P1Branch).filter(
            P1Branch.collectionid==collect.id).one()
        new_collection = model.Collection(
            name=collect.name,
            version=collect.version,
            status=STATUS[collect.statuscode],
            owner=collect.owner,
            publishURLTemplate=collect.publishurltemplate,
            pendingURLTemplate=collect.pendingurltemplate,
            summary=collect.summary,
            description=collect.description,
            branchname=branch.branchname,
            distTag=branch.disttag,
            git_branch_name=branch.gitbranchname,
        )
        new_collection.id = collect.id
        pkg2_sess.add(new_collection)
        cnt += 1
    pkg2_sess.commit()
    print '%s collections added' % cnt


def convert_packages(pkg1_sess, pkg2_sess):
    ''' Convert the Packages from pkgdb1 to pkgdb2.
    '''
    cnt = 0
    for pkg in pkg1_sess.query(P1Package).all():
        new_pkg = model.Package(
            name=pkg.name,
            summary=pkg.summary,
            status=STATUS[pkg.statuscode],
            shouldopen=pkg.shouldopen,
            review_url=pkg.reviewurl,
            upstream_url=pkg.upstreamurl,
        )
        new_pkg.id = pkg.id
        pkg2_sess.add(new_pkg)
        cnt += 1
    pkg2_sess.commit()
    print '%s packages added' % cnt


def convert_packagelisting(pkg1_sess, pkg2_sess):
    ''' Convert the PackageListing from pkgdb1 to pkgdb2.
    '''
    cnt = 0
    for pkg in pkg1_sess.query(P1Packagelisting).all():
        poc = pkg.owner
        if poc == 'perl-sig':
            poc = 'group::perl-sig'
        new_pkglist = model.PackageListing(
            point_of_contact=poc,
            status=STATUS[pkg.statuscode],
            package_id=pkg.packageid,
            collection_id=pkg.collectionid,
            critpath=pkg.critpath
        )
        new_pkglist.id = pkg.id
        pkg2_sess.add(new_pkglist)
        cnt += 1
    pkg2_sess.commit()
    print '%s Package listing added' % cnt


def convert_packagelistingacl(pkg1_sess, pkg2_sess):
    ''' Convert the PackageListingAcl from pkgdb1 to pkgdb2.
    '''
    cnt = 0
    total = pkg1_sess.query(P1PersonPackagelistingAcl).count()
    page = 0
    page_cnt = total / 10
    done = set()
    while page < 10:
        print page, cnt, page * page_cnt, (page + 1) * page_cnt, total
        for pkg in pkg1_sess.query(P1PersonPackagelistingAcl
                ).offset(
                    page * page_cnt
                ).limit(
                    (page + 1) * page_cnt
                ).all():
            if pkg.acl in ('build', 'checkout'):
                continue
            person = pkg1_sess.query(P1PersonPackagelisting).filter(
                P1PersonPackagelisting.id==pkg.personpackagelistingid
            ).one()
            key = (person.username, pkg.acl, person.packagelistingid)
            if key in done:
                print page, cnt, key
                continue
            else:
                done.add(key)
            new_pkglistacl = model.PackageListingAcl(
                fas_name=person.username,
                packagelisting_id=person.packagelistingid,
                acl=pkg.acl,
                status=STATUS[pkg.statuscode]
            )
            pkg2_sess.add(new_pkglistacl)
            pkg2_sess.flush()
            cnt += 1
        page += 1
        pkg2_sess.commit()
    pkg2_sess.commit()
    print '%s Package listing ACLs added' % cnt


def update_package_owner_acls(pkg2_sess):
    """ All ACLs to package owner, now point of contact.
    """
    cnt = 0
    for pkg in pkg2_sess.query(model.PackageListing).all():
        sys.stdout.write(cnt)
        sys.stdout.flush()
        acls = ['watchcommits', 'watchbugzilla', 'commit', 'approveacls']
        if pkg.point_of_contact == 'perl-sig':
            acls = ['watchcommits', 'watchbugzilla', 'commit']
        for acl in acls:
            new_pkglistacl = model.PackageListingAcl(
                fas_name=pkg.point_of_contact,
                packagelisting_id=pkg.id,
                acl=acl,
                status='Approved'
            )
            pkg2_sess.add(new_pkglistacl)
            try:
                pkg2_sess.flush()
            except sqlalchemy.exc.IntegrityError:
                pkg2_sess.rollback()
                pass
            else:
                cnt += 1
    pkg2_sess.commit()
    print '%s Package ACLs added' % cnt


def main(db_url_pkgdb1, db_url_pkgdb2):
    ''' The methods connect to the two pkgdb database and converts the data
    from one database model to the other.
    '''
    pkg1_sess = create_session(db_url_pkgdb1)
    pkg2_sess = pkgdb.lib.create_session(db_url_pkgdb2)
    convert_collections(pkg1_sess, pkg2_sess)
    convert_packages(pkg1_sess, pkg2_sess)
    convert_packagelisting(pkg1_sess, pkg2_sess)
    convert_packagelistingacl(pkg1_sess, pkg2_sess)
    update_package_owner_acls(pkg2_sess)


if __name__ == '__main__':
    if not DB_URL_PKGDB1 or not DB_URL_PKGDB2:
        print 'You need to set the database(s) URL(s) at the top of this ' \
              'file'
        sys.exit(1)
    main(DB_URL_PKGDB1, DB_URL_PKGDB2)

