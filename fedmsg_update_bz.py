# -*- coding: utf-8 -*-

""" A fedmsg consumer that listens to pkgdb messages and update bugzilla
for change in PoC in rawhide.

Authors:    Pierre-Yves Chibon <pingou@pingoured.fr>

"""

import pprint
import fedmsg.consumers

import pkgdb2.lib.exceptions
import pkgdb2.lib.utils


class UpdateBZConsumer(fedmsg.consumers.FedmsgConsumer):

    # Because we are interested in a variety of topics, we tell moksha that
    # we're interested in all of them (it doesn't know how to do complicated
    # distinctions).  But then we'll filter later in our consume() method.
    topic = 'org.fedoraproject.prod.pkgdb.owner.update'

    config_key = 'pkgdb.bz_consumer.enabled'

    def __init__(self, hub):
        super(UpdateBZConsumer, self).__init__(hub)

    def consume(self, msg):
        msg = msg['body']
        self.log.info("Got a message %r" % msg['topic'])

        pkg_poc = msg['msg'].get('username')
        if not pkg_poc:
            msg['msg']['package_listing']['point_of_contact']
        pkg_prev_poc = msg['msg'].get('previous_owner')
        pkg_name = msg['msg'].get('package_name')
        if not pkg_name:
            pkg_name = msg['msg']['package_listing']['package']['name']
        clt_name = msg['msg']['package_listing']['collection']['name']
        clt_version = msg['msg']['package_listing']['collection']['version']

        namespace = msg['msg']['package_listing']['package'].get(
            'namespace', 'rpms')
        if namespace != 'rpms':
            return

        try:
            pkgdb2.lib.utils.set_bugzilla_owner(
                pkg_poc, pkg_prev_poc, pkg_name, clt_name, clt_version)
        except pkgdb2.lib.exceptions.PkgdbBugzillaException, err:
            self.log.exception(
                'Error while updating bugzilla for %s -> %s' % (
                    pkg_prev_poc, pkg_poc))
