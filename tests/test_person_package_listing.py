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
pkgdb tests for the PersonPackageListing object.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

from pkgdb.lib import model
from tests import (Modeltests, create_person_package,
                   create_person_package_acl)


class PersonPackageListingtests(Modeltests):
    """ PersonPackageListing tests. """

    def test_init_package(self):
        """ Test the __init__ function of PersonPackageListing. """
        create_person_package(self.session)
        self.assertEqual(3,
                         len(model.PersonPackageListing.all(self.session))
                         )

    def test_to_json(self):
        """ Test the to_json function of PersonPackageListing. """
        packager = model.PersonPackageListing.get_acl_packager(
            self.session, 'pingou')
        self.assertEqual(0, len(packager))

        create_person_package_acl(self.session)

        packager = model.PersonPackageListing.get_acl_packager(
            self.session, 'pingou')
        self.assertEqual(2, len(packager))
        output = packager[0].to_json()
        self.assertEqual(output,
        {'acls': [{'status': u'Approved', 'acl': u'commit'}],
         'user': u'pingou',
         'package': {'owner': u'pingou', 'qacontact': None,
         'collection': {'pendingurltemplate': None,
                        'publishurltemplate': None,
                        'version': u'18', 'name': u'Fedora'},
         'package': {'upstreamurl': u'http://guake.org',
                     'name': u'guake',
                     'reviewurl': u'https://bugzilla.redhat.com/450189',
                     'summary': u'Top down terminal for GNOME'}
         }
        })

    def test___repr__(self):
        """ Test the __repr__ function of PersonPackageListing. """
        create_person_package_acl(self.session)

        packager = model.PersonPackageListing.get_acl_packager(
            self.session, 'pingou')
        self.assertEqual(2, len(packager))
        output = packager[0].__repr__()
        self.assertEqual(output, "PersonPackageListing(u'pingou', 1)")


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(PersonPackageListingtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
