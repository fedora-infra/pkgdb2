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

import pkgdb

from bugzilla import Bugzilla, RHBugzilla3

# The Fedora Account System Module
from fedora.client.fas2 import AccountSystem


# Have a global connection to bugzilla open.
_bugzilla = None
# Have a global connection to FAS open.
_fas = None


def get_fas():  # pragma: no cover
    ''' Retrieve a connection to the Fedora Account System.
    '''
    global _fas
    if _fas is not None:
        return _fas

    # Get a connection to FAS
    fas_url = pkgdb.APP.config['PKGDB_FAS_URL']
    if not fas_url:
        raise pkgdb.lib.PkgdbException('No PKGDB_FAS_URL configured')

    fas_user = pkgdb.APP.config['PKGDB_FAS_USER']
    if not fas_user:  # pragma: no cover
        raise pkgdb.lib.PkgdbException('No PKGDB_FAS_USER configured')

    fas_pass = pkgdb.APP.config['PKGDB_FAS_PASSWORD']
    if not fas_pass:  # pragma: no cover
        raise pkgdb.lib.PkgdbException(
            'No PKGDB_FAS_PASSWORD configured')

    _fas = AccountSystem(
        fas_url, username=fas_user, password=fas_pass, cache_session=False)
    return _fas


@pkgdb.cache.cache_on_arguments(expiration_time=3600)
def __get_fas_grp_member(group='packager'):  # pragma: no cover
    ''' Retrieve from FAS the list of users in the packager group.
    '''
    fas = get_fas()

    return fas.group_members(group)


def get_packagers():
    """ Return a list containing the name of all the packagers. """
    output = []
    for user in __get_fas_grp_member('packager'):
        if user.role_type in ('user', 'sponsor', 'admin'):
            output.append(user.username)
    return output


@pkgdb.cache.cache_on_arguments(expiration_time=3600)
def get_fas_group(group):
    """ Return group information from FAS based on the specified group name.
    """
    fas = get_fas()

    return fas.group_by_name(group)


@pkgdb.cache.cache_on_arguments(expiration_time=3600)
def get_bz_email_user(username):  # pragma: no cover
    ''' Retrieve the bugzilla email associated to the provided username.
    '''
    fas = get_fas()

    return fas.person_by_username(username)


def get_bz():
    '''Retrieve a connection to bugzilla

    :raises xmlrpclib.ProtocolError: If we're unable to contact bugzilla
    '''
    global _bugzilla
    if _bugzilla:  # pragma: no cover
        return _bugzilla

    # Get a connection to bugzilla
    bz_server = pkgdb.APP.config['PKGDB_BUGZILLA_URL']
    if not bz_server:
        raise pkgdb.lib.PkgdbException('No PKGDB_BUGZILLA_URL configured')
    bz_url = bz_server + '/xmlrpc.cgi'
    bz_user = pkgdb.APP.config['PKGDB_BUGZILLA_USER']
    bz_pass = pkgdb.APP.config['PKGDB_BUGZILLA_PASSWORD']

    _bugzilla = RHBugzilla3(url=bz_url, user=bz_user, password=bz_pass,
                            cookiefile=None)
    return _bugzilla


def _set_bugzilla_owner(
        username, pkg_name, collectn, collectn_version, bzComment=None):
    '''Change the package owner

     :arg user_email: User email address to change the owner.
     :arg pkg_name: Name of the package to change the owner.
     :arg collectn: Collection name of the package.
     :arg collectn_version: Collection version.
     :kwarg bzComment: the comment of changes, if left to None, rely on a
        default comment.
    '''
    bzComment = 'This package has changed ownership in the Fedora'\
                ' Package Database.  Reassigning to the new owner'\
                ' of this component.'

    user_email = get_bz_email_user(username).bugzilla_email

    bzMail = '%s' % user_email
    bzQuery = {}
    bzQuery['product'] = collectn
    bzQuery['component'] = pkg_name
    bzQuery['bug_status'] = [
        'NEW', 'ASSIGNED', 'ON_DEV', 'ON_QA', 'MODIFIED', 'POST',
        'FAILS_QA', 'PASSES_QA', 'RELEASE_PENDING']
    bzQuery['version'] = collectn_version
    if bzQuery['version'] == 'devel':
        bzQuery['version'] = 'rawhide'
    queryResults = get_bz().query(bzQuery)  # pylint:disable-msg=E1101

    for bug in queryResults:
        if pkgdb.APP.config['PKGDB_BUGZILLA_NOTIFICATION']:  # pragma: no cover
            bug.setassignee(assigned_to=bzMail, comment=bzComment)
        else:
            print(
                'Would have reassigned bug #%(bug_num)s '
                'from %(former)s to %(current)s' % {
                    'bug_num': bug.bug_id, 'former': bug.assigned_to,
                    'current': bzMail})


def _construct_substitutions(msg):
    """ Convert a fedmsg message into a dict of substitutions. """
    subs = {}
    for key1 in msg:
        if isinstance(msg[key1], dict):
            subs.update(dict([
                ('.'.join([key1, key2]), val2)
                for key2, val2 in _construct_substitutions(msg[key1]).items()
            ]))

        subs[key1] = msg[key1]

    return subs


def log(session, package, topic, message):
    """ Take a partial fedmsg topic and message.

    Publish the message and log it in the db.
    """

    # To avoid a circular import.
    import pkgdb.lib.model as model
    import pkgdb.lib.fedmsgshim as fedmsg

    # A big lookup of fedmsg topics to model.Log template strings.
    templates = {
        'acl.update': 'user: %(agent)s set acl: %(acl)s of package: '
            '%(package_name)s from: '
            '%(previous_status)s to: '
            '%(status)s on branch: '
            '%(package_listing.collection.branchname)s',
        'owner.update': 'user: %(agent)s changed owner of package: '
            '%(package_name)s from: '
            '%(previous_owner)s to: '
            '%(username)s on branch: '
            '%(package_listing.collection.branchname)s',
        'branch.start': 'user: %(agent)s started branching from '
            '%(collection_from.branchname)s to '
            '%(collection_to.branchname)s',
        'branch.complete': 'user: %(agent)s finished branching from '
            '%(collection_from.branchname)s to '
            '%(collection_to.branchname)s',
        'package.new': 'user: %(agent)s created package: '
            '%(package_name)s on branch: '
            '%(package_listing.collection.branchname)s for poc: '
            '%(package_listing.point_of_contact)s',
        'package.update': 'user: %(agent)s updated package: '
            '%(package_name)s status from: '
            '%(prev_status)s to '
            '%(status)s',
        'collection.new': 'user: %(agent)s created collection: '
            '%(collection.name)s',
        'collection.update': 'user: %(agent)s edited collection: '
            '%(collection.name)s',
    }
    substitutions = _construct_substitutions(message)
    s = templates[topic] % substitutions

    model.Log.insert(session, message['agent'], package, s)
    fedmsg.publish(topic, message)
