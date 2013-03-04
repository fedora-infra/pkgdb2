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
pkgdb tests.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import sys
import os

from datetime import date
from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

from pkgdb.lib import model

DB_PATH = 'url...'


class Modeltests(unittest.TestCase):
    """ Model tests. """

    def __init__(self, method_name='runTest'):
        """ Constructor. """
        unittest.TestCase.__init__(self, method_name)
        self.session = None

    # pylint: disable=C0103
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        self.session = model.create_tables(DB_PATH)

    # pylint: disable=C0103
    def tearDown(self):
        """ Remove the test.db database if there is one. """
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)


def create_collection(session):
    """ Create some basic collection for testing. """
    collection = model.Collection(
                                  name = 'Fedora',
                                  version = '18',
                                  status = 'Active',
                                  owner = 10,
                                  publishurltemplate=None,
                                  pendingurltemplate=None,
                                  summary='Fedora 18 release',
                                  description=None,
                                  branchname='F18',
                                  distTag='.fc18',
                                  git_branch_name='f18',
                                  )
    session.add(collection)

    collection = model.Collection(
                                  name = 'Fedora',
                                  version = 'devel',
                                  status = 'Under Development',
                                  owner = 11,
                                  publishurltemplate=None,
                                  pendingurltemplate=None,
                                  summary='Fedora rawhide',
                                  description=None,
                                  branchname='devel',
                                  distTag='.fc19',
                                  git_branch_name='master',
                                  )
    session.add(collection)
    session.commit()


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Modeltests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
