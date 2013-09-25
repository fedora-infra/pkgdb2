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
pkgdb tests for the Flask application.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import json
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import pkgdb
from pkgdb.lib import model
from tests import (Modeltests, FakeFasUser, create_package_acl)


class FlaskTest(Modeltests):
    """ Flask tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskTest, self).setUp()

        pkgdb.APP.config['TESTING'] = True
        pkgdb.SESSION = self.session
        pkgdb.api.acls.SESSION = self.session
        self.app = pkgdb.APP.test_client()

    def test_index(self):
        """ Test the index function. """
        output = self.app.get('/')
        self.assertEqual(output.status_code, 200)

        expected = """
The Package Database is a central repository of package information in
Fedora. You will eventually be able to find and change all the
metainformation about a package by searching the database. The current
implementation is focused on the data that package developers and release
engineers need to create packages and spin them into a distribution."""

        self.assertTrue(expected in output.data)

    def test_list_packages(self):
        """ Test the list_packages function. """
        output = self.app.get('/packages')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/packages/')
        self.assertEqual(output.status_code, 200)

        expected = "<h1>Search packages</h1>"

        self.assertTrue(expected in output.data)

    def test_list_packagers(self):
        """ Test the list_packagers function. """
        output = self.app.get('/packagers')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/packagers/')
        self.assertEqual(output.status_code, 200)

        expected = "<h1>Search packagers</h1>"

        self.assertTrue(expected in output.data)

    def test_list_collections(self):
        """ Test the list_collections function. """
        output = self.app.get('/collections')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/collections/')
        self.assertEqual(output.status_code, 200)

        expected = "<h1>Search collections</h1>"

        self.assertTrue(expected in output.data)

    def test_stats(self):
        """ Test the stats function. """
        output = self.app.get('/stats')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/stats/')
        self.assertEqual(output.status_code, 200)

        expected = """<h1>Fedora Package Database</h1>

<p>
    PkgDB stores currently information about 6
    Fedora releases.
</p>"""

        self.assertTrue(expected in output.data)

    def test_api(self):
        """ Test the api function. """

        output = self.app.get('/api/')
        self.assertEqual(output.status_code, 200)

        expected = """
<h2>Collections</h2>

<div class="document">
<blockquote>
<dl class="docutils">
<dt><code>/api/collection/new/</code></dt>
<dd><p class="first">Create a new collection.</p>
<p>Accept POST queries only.</p>
<table class="last docutils field-list" frame="void" rules="none">
<col class="field-name" />
<col class="field-body" />
<tbody valign="top">
<tr class="field"><th class="field-name" colspan="2">arg collection_name:</th></tr>
<tr class="field"><td>&nbsp;</td><td class="field-body">String of the collection name to be created.</td>
</tr>
<tr class="field"><th class="field-name" colspan="2">arg collection_version:</th></tr>
<tr class="field"><td>&nbsp;</td><td class="field-body">String of the version of the collection.</td>
</tr>"""
        self.assertTrue(expected in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
