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

import hashlib
import urllib

import pkgdb2
import pkgdb2.lib.exceptions

from bugzilla import Bugzilla

# The Fedora Account System Module
from fedora.client.fas2 import AccountSystem


## We use global variable for a reason
# pylint: disable=W0603
## Some variable/method cannot be inferred from the inheritance
# pylint: disable=E1103
# pylint: disable=E1101


# Have a global connection to bugzilla open.
_BUGZILLA = None
# Have a global connection to FAS open.
_FAS = None


def get_fas():  # pragma: no cover
    ''' Retrieve a connection to the Fedora Account System.
    '''
    global _FAS
    if _FAS is not None:
        return _FAS

    # Get a connection to FAS
    fas_url = pkgdb2.APP.config['PKGDB2_FAS_URL']
    if not fas_url:
        raise pkgdb2.lib.PkgdbException('No PKGDB2_FAS_URL configured')

    fas_user = pkgdb2.APP.config['PKGDB2_FAS_USER']
    if not fas_user:  # pragma: no cover
        raise pkgdb2.lib.PkgdbException('No PKGDB2_FAS_USER configured')

    fas_pass = pkgdb2.APP.config['PKGDB2_FAS_PASSWORD']
    if not fas_pass:  # pragma: no cover
        raise pkgdb2.lib.PkgdbException(
            'No PKGDB2_FAS_PASSWORD configured')

    fas_insecure = pkgdb2.APP.config.get('PKGDB2_FAS_INSECURE', False)

    _FAS = AccountSystem(
        fas_url, username=fas_user, password=fas_pass, cache_session=False,
        insecure=fas_insecure)

    return _FAS


@pkgdb2.CACHE.cache_on_arguments(expiration_time=3600)
def __get_fas_grp_member(group='packager'):  # pragma: no cover
    ''' Retrieve from FAS the list of users in the packager group.
    '''
    fas = get_fas()

    return fas.group_members(group)


def get_packagers():  # pragma: no cover
    """ Return a list containing the name of all the packagers. """
    output = []
    for user in __get_fas_grp_member('packager'):
        if user.role_type in ('user', 'sponsor', 'administrator'):
            output.append(user.username)
    return output


@pkgdb2.CACHE.cache_on_arguments(expiration_time=3600)
def get_fas_group(group):  # pragma: no cover
    """ Return group information from FAS based on the specified group name.
    """
    fas = get_fas()

    return fas.group_by_name(group)


@pkgdb2.CACHE.cache_on_arguments(expiration_time=3600)
def get_bz_email_user(username):  # pragma: no cover
    ''' Retrieve the bugzilla email associated to the provided username.
    '''
    fas = get_fas()

    return fas.person_by_username(username)


def get_bz():  # pragma: no cover
    '''Retrieve a connection to bugzilla

    :raises xmlrpclib.ProtocolError: If we're unable to contact bugzilla
    '''
    global _BUGZILLA
    if _BUGZILLA:  # pragma: no cover
        return _BUGZILLA

    # Get a connection to bugzilla
    bz_server = pkgdb2.APP.config['PKGDB2_BUGZILLA_URL']
    if not bz_server:
        raise pkgdb2.lib.PkgdbException('No PKGDB2_BUGZILLA_URL configured')
    bz_url = bz_server + '/xmlrpc.cgi'
    bz_user = pkgdb2.APP.config['PKGDB2_BUGZILLA_USER']
    bz_pass = pkgdb2.APP.config['PKGDB2_BUGZILLA_PASSWORD']

    _BUGZILLA = Bugzilla(url=bz_url, user=bz_user, password=bz_pass,
                         cookiefile=None, tokenfile=None)
    return _BUGZILLA


def set_bugzilla_owner(
        username, prev_poc, pkg_name, collectn, collectn_version,
        bz_comment=None):  # pragma: no cover
    '''Change the package owner

     :arg username: Username of the new point of contact.
     :arg prev_poc: Username of the previous point of contact
     :arg pkg_name: Name of the package to change the owner.
     :arg collectn: Collection name of the package.
     :arg collectn_version: Collection version.
     :kwarg bz_comment: the comment of changes, if left to None, rely on a
        default comment.
    '''
    if not bz_comment:
        bz_comment = 'This package has changed ownership in the Fedora'\
                     ' Package Database.  Reassigning to the new owner'\
                     ' of this component.'

    if username.startswith('group::'):
        user_email = get_fas_group(
            username.replace('group::', '')).mailing_list
    else:
        user_email = get_bz_email_user(username).bugzilla_email

    prev_poc_email = ''
    if prev_poc:
        prev_poc_email = get_bz_email_user(prev_poc).bugzilla_email

    bz_mail = '%s' % user_email
    prev_mail = '%s' % prev_poc_email
    bz_query = {}
    bz_query['product'] = collectn
    bz_query['component'] = pkg_name
    bz_query['bug_status'] = [
        'NEW', 'ASSIGNED', 'ON_DEV', 'ON_QA', 'MODIFIED', 'POST',
        'FAILS_QA', 'PASSES_QA', 'RELEASE_PENDING']
    bz_query['version'] = collectn_version
    if bz_query['version'] == 'devel':
        bz_query['version'] = 'rawhide'
    bugz = get_bz()
    query_results = bugz.query(bz_query)

    for bug in query_results:
        if (not prev_poc_email or bug.assigned_to == prev_mail) \
                and bug.assigned_to != bz_mail:
            if pkgdb2.APP.config[
                    'PKGDB2_BUGZILLA_NOTIFICATION']:  # pragma: no cover
                try:
                    bug.setassignee(assigned_to=bz_mail, comment=bz_comment)
                except Exception, err:
                    raise pkgdb2.lib.exceptions.PkgdbBugzillaException(
                        'An error occured while calling bugzilla: %s'
                        % str(err)
                    )
            else:
                print(
                    'Would have reassigned bug #%(bug_num)s '
                    'from %(former)s to %(current)s' % {
                        'bug_num': bug.bug_id, 'former': bug.assigned_to,
                        'current': bz_mail})


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
    import pkgdb2.lib.model as model
    from pkgdb2.lib.notifications import fedmsg_publish, email_publish

    if pkgdb2.APP.config.get('PKGDB2_FEDMSG_NOTIFICATION', True):
        fedmsg_publish(topic, message)

    # A big lookup of fedmsg topics to model.Log template strings.
    templates = {
        'acl.update': 'user: %(agent)s set for %(username)s acl: %(acl)s of'
                      ' package: %(package_name)s from: '
                      '%(previous_status)s to: '
                      '%(status)s on branch: '
                      '%(package_listing.collection.branchname)s',
        'acl.delete': 'user: %(agent)s deleted acl: %(acl.acl)s of '
                      'package: %(acl.packagelist.package.name)s of user: '
                      '%(acl.fas_name)s on: '
                      '%(acl.packagelist.collection.branchname)s',
        'owner.update': 'user: %(agent)s changed point of contact of package: '
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
        'package.branch.delete': 'user: %(agent)s deleted branch: '
                                 '%(package_listing.collection.'
                                 'branchname)s '
                                 'for package %(package_listing.'
                                 'package.name)s ',
        'package.branch.new': 'user: %(agent)s created branch '
                              '%(package_listing.collection.'
                              'branchname)s on package %(package.name)s',
        'package.delete': 'user: %(agent)s deleted package %(package.name)s',
        'package.new': 'user: %(agent)s created package: '
                       '%(package_name)s on branch: '
                       '%(package_listing.collection.branchname)s for point'
                       ' of contact: %(package_listing.point_of_contact)s',
        'package.critpath.update': 'user: %(agent)s updated critpath status'
                                   'for package: %(package.name)s on '
                                   'branches %(branches)s',
        'package.update': 'user: %(agent)s updated %(fields)s package: '
                          '%(package.name)s',
        'package.update.status': 'user: %(agent)s updated package: '
                          '%(package_name)s status from: '
                          '%(prev_status)s to '
                          '%(status)s on branch: '
                          '%(package_listing.collection.branchname)s',
        'collection.new': 'user: %(agent)s created collection: '
                          '%(collection.name)s',
        'collection.update': 'user: %(agent)s edited collection: '
                             '%(collection.name)s',
        'package.monitor.update': 'user: %(agent)s updated the monitoring '
                               'status of %(package.name)s to %(status)s'
    }
    subject_templates = {
        'acl.update': '%(agent)s:%(package_name)s %(acl)s  set to %(status)s',
        'owner.update': '%(agent)s:%(package_name)s set point of contact to: '
                        '%(username)s',
        'package.update': '%(agent)s updated package: '
                          '%(package.name)s',
        'package.update.status': '%(agent)s updated package: '
                          '%(package_name)s status to '
                          '%(status)s ['
                          '%(package_listing.collection.branchname)s]',
    }
    substitutions = _construct_substitutions(message)
    final_msg = templates[topic] % substitutions
    subject = None
    if topic in subject_templates:
        subject = subject_templates[topic] % substitutions

    model.Log.insert(session, message['agent'], package, final_msg)

    if pkgdb2.APP.config.get(
            'PKGDB2_EMAIL_NOTIFICATION', False):  # pragma: no cover
        body_email = final_msg
        if package:
            body_email = '{0}\n\nTo make changes to this package see:\n' \
                '{1}/package/{2}'.format(
                    final_msg, pkgdb2.APP.config.get('SITE_URL'),
                    package.name)
        email_publish(
            message['agent'], package, body_email, subject=subject)

    return final_msg


def avatar_url(username, size=64, default='retro'):
    openid = "http://%s.id.fedoraproject.org/" % username
    return avatar_url_from_openid(openid, size, default)


def avatar_url_from_openid(openid, size=64, default='retro', dns=False):
    """
    Our own implementation since fas doesn't support this nicely yet.
    """

    if dns:  # pragma: no cover
        # This makes an extra DNS SRV query, which can slow down our webapps.
        # It is necessary for libravatar federation, though.
        import libravatar
        return libravatar.libravatar_url(
            openid=openid,
            size=size,
            default=default,
        )
    else:
        query = urllib.urlencode({'s': size, 'd': default})
        hash = hashlib.sha256(openid).hexdigest()
        return "https://seccdn.libravatar.org/avatar/%s?%s" % (hash, query)
