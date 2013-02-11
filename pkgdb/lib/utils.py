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
Utilities for all classes to use
'''

import sys
import os
import gzip
import bz2
import subprocess
import logging

try:
    # Note: Ran profile of crc32, md5, sha1, sha256 over our key values
    # crc32 is almost twice as fast.
    # md5, sha1, sha256 are comparable to each other
    # No collisions in our current set
    from hashlib import sha1 as Hasher
except ImportError:
    from sha import new as Hasher

import rpm
import rpmUtils.transaction

from sqlalchemy import select, and_
from sqlalchemy.exc import DataError

from bugzilla import Bugzilla, RHBugzilla3
import memcache

# The Fedora Account System Module
from fedora.client.fas2 import AccountSystem

from pkgdb.lib.model.statuses import StatusTranslationTable
from pkgdb import _

MEMCACHE = memcache.Client(config.get('memcached.servers', []))

STATUS = None
fas = None
LOG = None
_bugzilla = None

# Get the admin group if one is specified.
admin_grp = config.get('pkgdb.admin_grp', 'cvsadmin')

# Get the packager group if one is specified.
pkger_grp = config.get('pkgdb.pkger_grp', 'packager')

# Get the moderator group if one is specified.
mod_grp = config.get('pkgdb.mod_grp', 'sysadmin')

# Get the provenpackager group if one is specified.
provenpkger_grp = config.get('pkgdb.provenpkger_grp', 'provenpackager')

# Get the newpackager group if one is specified.
newpkger_grp = config.get('pkgdb.newpkger_grp', 'newpackager')

# Get the critpath groups if specfied
critpath_grps = config.get('pkgdb.critpath_grps', (admin_grp,))


def to_unicode(obj, encoding='utf-8', errors='replace'):
    '''return a unicode representation of the object.

    :arg obj: object to attempt to convert to unicode.  Note: If this is
        not a str or unicode object then the conversion might not be
        what you want (as it converts the __str__ of the obj).
    :kwarg encoding: encoding of the byte string to convert from.
    :kwarg errors:
        :strict: raise an error if it won't convert
        :replace: replace non-converting chars with a certain char for
            the encoding.  (For instance, ascii substitutes a ?).
        :ignore: silently drop the bad characters

    '''
    if isinstance(obj, unicode):
        return obj
    if isinstance(obj, str):
        return unicode(obj, encoding, errors)
    return unicode(obj)


class UserCache(dict):
    '''Naive cache for user information.

    This cache can go out of date so use with caution.

    Use clear() to remove all entries from the cache.
    Use del cache[username] to remove a specific entry.
    '''
    def __init__(self, fas_connection):
        super(UserCache, self).__init__()
        self.fas = fas_connection

    def __getitem__(self, username):
        '''Retrieve a user for a username.

        First read from the cache.  If not in the cache, refresh from
        the server and try again.

        If the user does not exist then, KeyError will be raised.
        '''
        username = username.strip()
        if username not in self:
            if not username:
                # If the key is just whitespace, raise KeyError immediately,
                # don't try to pull from fas
                raise KeyError(username)
            LOG.debug(_('refresh forced for %(user)s') % {'user':  username})
            person = self.fas.person_by_username(username)
            if not person:
                # no value for this username
                raise KeyError(username)
            self[username] = person
        return super(UserCache, self).__getitem__(username)


class StatusCache(dict):
    def __init__(self, timeout=3600):
        self.timeout = timeout

    def __getitem__(self, status_id):
        '''Return the other half of status from memcache or the database

        :arg status_id: This can be either a statuscode or a statusname.
            If it's a statusname, the statuscode will be returned.  If
            it's a statusname, the statuscode will be returned.
        '''
        if isinstance(status_id, basestring):
            # Have a statusname, looking for an id

            # First ask memcache server for the value
            mc_id = 'pkgdb:status:%s' % Hasher(status_id).hexdigest()
            status_value = MEMCACHE.get(mc_id)

            if not status_value:
                status = select((StatusTranslationTable,), and_(
                    StatusTranslationTable.c.language=='C',
                    StatusTranslationTable.c.statusname==status_id))\
                            .execute().fetchone()
        else:
            # Have an id, look for a statusname

            # Ask memcache server for the value
            mc_id = 'pkgdb:status:%s' % str(status_id)
            status_value = MEMCACHE.get(mc_id)

            if not status_value:
                try:
                    status = select((StatusTranslationTable,), and_(
                        StatusTranslationTable.c.language=='C',
                        StatusTranslationTable.c.statuscodeid==status_id))\
                                .execute().fetchone()
                except DataError:
                    # If status_id was not an integer we get a DataError.  In
                    # that case, we know we won't find the value we want
                    status = None

        if not status_value:
            if not status:
                raise KeyError(_('Unknown status: %(status)s') %
                    {'status': status_id})

            status_value = status.statuscodeid
            # Save in memcache for the next status lookup
            MEMCACHE.set(mc_id, status_value, self.timeout)

        return status_value

    def __setitem__(self, statusname, value):
        raise TypeError(_('\'StatusCache\' object does not support item'
                        ' assignment'))

    def refresh_status(self):
        '''Recache all the status types
        '''
        status_map = {}
        for status in select((StatusTranslationTable,),
                StatusTranslationTable.c.language=='C').execute():
            status_map[Hasher(status.statusname).hexdigest()
                       ] = status.statuscodeid
            status_map[status.statuscodeid] = status.statusname
        MEMCACHE.set_multi(status_map, key_prefix='pkgdb:status:',
            time=self.timeout)


def get_bz():
    '''Retrieve a connection to bugzilla

    :raises xmlrpclib.ProtocolError: If we're unable to contact bugzilla
    '''
    global _bugzilla
    if _bugzilla:
        return _bugzilla
    # Get a connection to bugzilla
    bz_server = config.get('bugzilla.queryurl', config.get('bugzilla.url',
        'https://bugzilla.redhat.com'))
    bz_url = bz_server + '/xmlrpc.cgi'
    bz_user = config.get('bugzilla.user')
    bz_pass = config.get('bugzilla.password')
    _bugzilla = RHBugzilla3(url=bz_url, user=bz_user, password=bz_pass,
            cookiefile=None)
    return _bugzilla


def custom_template_vars(new_vars):
    return new_vars.update({'fas_cache': fas.cache})


def init_globals():
    '''Initialize global variables.

This is mostly connections to services like FAS, bugzilla, and loading
    constants from the database.
    '''
    global fas, LOG, STATUS
    # Things to do on startup
    STATUS = StatusCache()
    STATUS.refresh_status()
    LOG = logging.getLogger('pkgdb.controllers')

    # Get a connection to the Account System server
    fas_url = config.get('fas.url',
                         'https://admin.fedoraproject.org/accounts/')
    username = config.get('fas.username', 'admin')
    password = config.get('fas.password', 'admin')

    fas = AccountSystem(fas_url, username=username, password=password,
            cache_session=False)
    fas.cache = UserCache(fas)

    view.variable_providers.append(custom_template_vars)


def is_xhr():
    '''Check if the request is coming from AJAX
    '''

    requested_with = request.headers.get('X-Requested-With')
    return requested_with and requested_with.lower() == 'xmlhttprequest'


# Modified from yumUtils rpmUtils.rpm2cpio code.  Need to work on it more
def rpm2cpio(fdno, out=sys.stdout, bufsize=2048):
    """Performs roughly the equivalent of rpm2cpio(8).
       Reads the package from fdno, and dumps the cpio payload to out,
       using bufsize as the buffer size."""
    ts = rpmUtils.transaction.initReadOnlyTransaction()
    hdr = ts.hdrFromFdno(fdno)
    del ts

    compr = hdr[rpm.RPMTAG_PAYLOADCOMPRESSOR] or 'gzip'
    if compr == 'gzip':
        f = gzip.GzipFile(None, 'rb', None, os.fdopen(fdno, 'rb', bufsize))
        while 1:
            tmp = f.read(bufsize)
            if tmp == "": break
            out.write(tmp)
        out.flush()
        f.close()
    elif compr == 'xz':
        # This is a bit hacky
        xz_cmd = subprocess.Popen(['/usr/bin/xzcat'],
                                  stdout=subprocess.PIPE,
                                  stdin=os.fdopen(fdno, 'rb', bufsize),
                                  bufsize=bufsize,
                                  shell=False)
        while 1:
            tmp = xz_cmd.stdout.read(bufsize)
            if tmp == "": break
            out.write(tmp)
        out.flush()
    elif compr == 'bzip2':
        f = os.fdopen(fdno, 'rb', bufsize)
        decompressor = bz2.BZ2Decompressor()
        while 1:
            chunk = f.read(bufsize)
            if chunk == "": break
            try:
                tmp = decompressor.decompress(tmp)
            except EOFError:
                break
            out.write(tmp)
        out.flush()
        f.close()
    else:
        raise rpmUtils.RpmUtilsError, \
              'Unsupported payload compressor: "%s"' % compr

__all__ = [LOG, MEMCACHE, STATUS, admin_grp, critpath_grps, fas, get_bz,
        init_globals, is_xhr, pkger_grp, rpm2cpio, to_unicode]
