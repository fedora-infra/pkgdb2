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


BASE_URL = 'https://dl.fedoraproject.org/pub/fedora/linux/development/' + \
    'rawhide/source/SRPMS/'


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


def get_primary_db_location():
    ''' Retrieve the latest primary_db from the rawhide repo metadata.
    '''
    data = requests.get(BASE_URL + 'repodata/repomd.xml')
    primary_db = False
    location = None
    for row in data.text.split('\n'):
        if 'type="primary_db"' in row.strip():
            primary_db = True
        if primary_db and row.strip().startswith('<location'):
            location = row.split('"')[1]
            break
    return location


def download_primary_db(location, target):
    ''' Download the provided location at the specified target. '''
    data = requests.get(BASE_URL + location, stream=True)
    with open(target, 'wb') as stream:
        for chunk in data.iter_content(chunk_size=1024):
            if chunk:
                stream.write(chunk)
                stream.flush()
        stream.flush()


def decompress_primary_db(archive, location):
    ''' Decompress the given XZ archive at the specified location. '''
    with contextlib.closing(lzma.LZMAFile(archive)) as stream_xz:
        data = stream_xz.read()
    with open(location, 'wb') as stream:
        stream.write(data)


def get_pkg_info(session, pkg_name):
    ''' Query the sqlite database for the package specified. '''
    pkg = session.query(Package).filter(Package.name == pkg_name).one()
    return pkg


def main():
    working_dir = tempfile.mkdtemp()
    print working_dir

    primary_db_location = get_primary_db_location()

    dbfile_xz = os.path.join(working_dir, 'primary_db.sqlite.xz')
    download_primary_db(primary_db_location, dbfile_xz)

    dbfile = os.path.join(working_dir, 'primary_db.sqlite')
    decompress_primary_db(dbfile_xz, dbfile)

    db_url = 'sqlite:///%s' % dbfile
    db_session = sessionmaker(bind=create_engine(db_url))
    session = db_session()
    print db_url

    # Update the package in pkgdb
    count = 0
    updated = 0
    cnt = 0
    for cnt, pkg in enumerate(pkgdb2.lib.search_package(
            pkgdb2.SESSION, '*', status='Approved')):
        try:
            pkgobj = get_pkg_info(session, pkg.name)
        except Exception, err:
            print 'No such package %s found in yum\'s metadata.' % pkg.name
            continue

        if not pkgobj:
            print 'No such package %s found in yum\'s metadata.' % pkg.name
            continue

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

    pkgdb2.SESSION.commit()

    print '%s packages checked' % cnt
    print '%s packages updated' % updated

    # Drop the temp directory
    shutil.rmtree(working_dir)


if __name__ == '__main__':
    main()
