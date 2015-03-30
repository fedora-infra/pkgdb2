#!/usr/bin/env python

"""
This script queries the summary and description information from
yum's metadata and update the pgkdb2 database with them.

Background and history:
https://fedorahosted.org/fedora-infrastructure/ticket/3792
"""

# These two lines are needed to run on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources


import contextlib
import lzma
import os
import requests
import shutil
import sys
import tarfile
import tempfile


if 'PKGDB2_CONFIG' not in os.environ \
        and os.path.exists('/etc/pkgdb2/pkgdb2.cfg'):
    print 'Using configuration file `/etc/pkgdb2/pkgdb2.cfg`'
    os.environ['PKGDB2_CONFIG'] = '/etc/pkgdb2/pkgdb2.cfg'


BASE_URL = 'https://dl.fedoraproject.org/pub/%s/SRPMS/'
VERSIONS = [
    ('rawhide', 'fedora/linux/development/rawhide/source'),
    ('f22_up', 'fedora/linux/updates/22'),
    ('f21_up', 'fedora/linux/updates/21'),
    ('f21_rel', 'fedora/linux/releases/21/Everything/source'),
    ('f20_up', 'fedora/linux/updates/20'),
    ('f20_rel', 'fedora/linux/releases/20/Everything/source'),
    ('el7', 'epel/7'),
    ('el6', 'epel/6'),
    ('el5', 'epel/5'),
]


from sqlalchemy import Column, ForeignKey, Integer, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


BASE = declarative_base()


class Package(BASE):
    __tablename__ = 'packages'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    pkgKey = Column(Integer, primary_key=True)
    name = Column(Text)
    description = Column(Text)
    summary = Column(Text)
    url = Column(Text)


sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))
import pkgdb2
import pkgdb2.lib


class User(object):
    username = 'pkgdb_updater'
    cla_done = True
    groups = ['sysadmin-main']


def get_primary_db_location(base_url):
    ''' Retrieve the latest primary_db from the rawhide repo metadata.
    '''
    data = requests.get(base_url + 'repodata/repomd.xml')
    primary_db = False
    location = None
    for row in data.text.split('\n'):
        if 'type="primary_db"' in row.strip():
            primary_db = True
        if primary_db and row.strip().startswith('<location'):
            location = row.split('"')[1]
            break
    return location


def download_primary_db(base_url, location, target):
    ''' Download the provided location at the specified target. '''
    data = requests.get(base_url + location, stream=True)
    with open(target, 'wb') as stream:
        for chunk in data.iter_content(chunk_size=1024):
            if chunk:
                stream.write(chunk)
                stream.flush()
        stream.flush()


def decompress_primary_db(archive, location):
    ''' Decompress the given XZ archive at the specified location. '''
    if archive.endswith('.xz'):
        import lzma
        with contextlib.closing(lzma.LZMAFile(archive)) as stream_xz:
            data = stream_xz.read()
        with open(location, 'wb') as stream:
            stream.write(data)
    elif archive.endswith('.gz'):
        import tarfile
        with tarfile.open(archive) as tar:
            tar.extractall(path=location)
    elif archive.endswith('.bz2'):
        import bz2
        with open(location, 'w') as out:
            bzar = bz2.BZ2File(archive)
            out.write(bzar.read())
            bzar.close()
    elif archive.endswith('.sqlite'):
        with open(location, 'w') as out:
            with open(archive) as inp:
                out.write(inp.read())


def get_pkg_info(session, pkg_name):
    ''' Query the sqlite database for the package specified. '''
    pkg = session.query(Package).filter(Package.name == pkg_name).one()
    return pkg


def main():
    working_dir = tempfile.mkdtemp()
    print working_dir

    UNKNOWN = set()
    KNOWN = set()
    for name, version in VERSIONS:
        print '%s: %s' % (name, version)
        base_url = BASE_URL % version

        primary_db_location = get_primary_db_location(base_url)

        db_ext = primary_db_location.split('primary.')[1]
        dbfile_xz = os.path.join(working_dir, 'primary_db.%s' % db_ext)
        download_primary_db(base_url, primary_db_location, dbfile_xz)

        dbfile = os.path.join(working_dir, 'primary_db_%s.sqlite' % name)
        decompress_primary_db(dbfile_xz, dbfile)

        db_url = 'sqlite:///%s' % dbfile
        db_session = sessionmaker(bind=create_engine(db_url))
        session = db_session()

        # Update the package in pkgdb
        count = 0
        updated = 0
        if name == 'rawhide':
            for pkg in pkgdb2.lib.search_package(
                    pkgdb2.SESSION, '*', status='Approved'):

                try:
                    pkgobj = get_pkg_info(session, pkg.name)
                except Exception, err:
                    UNKNOWN.add(pkg.name)
                    continue

                if not pkgobj:
                    UNKNOWN.add(pkg.name)
                    continue

                KNOWN.add(pkg.name)
                msg = pkgdb2.lib.edit_package(
                    session=pkgdb2.SESSION,
                    package=pkg,
                    pkg_summary=pkgobj.summary,
                    pkg_description=pkgobj.description,
                    pkg_upstream_url=pkgobj.url,
                    user=User()
                )
                if msg:
                    updated += 1
        else:
            tmp = set()
            for pkgname in UNKNOWN:
                pkg = pkgdb2.lib.search_package(
                    pkgdb2.SESSION, pkgname, status='Approved')

                if len(pkg) == 1:
                    pkg = pkg[0]
                else:
                    print pkgname, pkg

                try:
                    pkgobj = get_pkg_info(session, pkg.name)
                except Exception, err:
                    tmp.add(pkg.name)
                    continue

                if not pkgobj:
                    tmp.add(pkg.name)
                    continue

                KNOWN.add(pkg.name)
                msg = pkgdb2.lib.edit_package(
                    session=pkgdb2.SESSION,
                    package=pkg,
                    pkg_summary=pkgobj.summary,
                    pkg_description=pkgobj.description,
                    pkg_upstream_url=pkgobj.url,
                    user=User()
                )
                if msg:
                    updated += 1
            # Add the package we didn't find here (in case)
            UNKNOWN.update(tmp)
            # Remove the ones we found
            UNKNOWN.difference_update(KNOWN)

        pkgdb2.SESSION.commit()

    print '%s packages found' % len(KNOWN)
    print '%s packages updated' % updated
    print '%s packages not found' % len(UNKNOWN)
    for pkg in sorted(UNKNOWN)[:5]:
        print "No such package %s found in yum's metadata." % pkg


    # Drop the temp directory
    shutil.rmtree(working_dir)


if __name__ == '__main__':
    main()
