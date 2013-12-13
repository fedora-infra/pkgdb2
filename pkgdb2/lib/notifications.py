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

""" This is a temporary shim that allows fedmsg to be an optional dependency of
pkgdb.  If fedmsg is installed, these function calls will try to actually send
messages.  If it is not installed, it will return silently.

  :Author: Ralph Bean <rbean@redhat.com>

"""

import smtplib
import warnings

from email.mime.text import MIMEText

import pkgdb2


def fedmsg_publish(*args, **kwargs):  # pragma: no cover
    ''' Try to publish a message on the fedmsg bus. '''
    ## We catch Exception if we want :-p
    # pylint: disable=W0703
    ## Ignore message about fedmsg import
    # pylint: disable=F0401
    try:
        import fedmsg
        fedmsg.publish(*args, **kwargs)
    except Exception, err:
        warnings.warn(str(err))


def email_publish(user, package, message):  # pragma: no cover
    ''' Send notification by email. '''

    if not package:
        return

    msg = MIMEText(message)
    msg['Subject'] = '[PkgDB] {0} updated {1}'.format(user, package.name)
    from_email = pkgdb2.APP.config.get(
        'PKGDB2_EMAIL_FROM', 'nobody@fedoraproject.org')
    email_to_template = pkgdb2.APP.config.get(
        'PKGDB2_EMAIL_TO', '{pkg_name}-owner@fedoraproject.org')
    to_email = email_to_template.format(pkg_name=package.name)
    msg['From'] = from_email
    msg['To'] = to_email

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    smtp = smtplib.SMTP(pkgdb2.APP.config.get(
        'PKGDB2_EMAIL_SMTP_SERVER', 'localhost'))
    smtp.sendmail(from_email, [to_email], msg.as_string())
    smtp.quit()
