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

import pkgdb2
from pkgdb2.lib import model
from tests import (Modeltests, FakeFasUser, create_package_acl, user_set)


class FlaskTest(Modeltests):
    """ Flask tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskTest, self).setUp()

        pkgdb2.APP.config['TESTING'] = True
        pkgdb2.SESSION = self.session
        pkgdb2.ui.SESSION = self.session
        pkgdb2.ui.acls.SESSION = self.session
        pkgdb2.ui.admin.SESSION = self.session
        pkgdb2.ui.collections.SESSION = self.session
        pkgdb2.ui.packagers.SESSION = self.session
        pkgdb2.ui.packages.SESSION = self.session
        self.app = pkgdb2.APP.test_client()

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

        expected = '<p>See the list of <a href="/orphaned/">orphaned</a>\n' \
                   'or <a href="/retired/">retired</a> packages</p>'

        self.assertTrue(expected in output.data)

    def test_list_orphaned(self):
        """ Test the list_orphaned function. """
        output = self.app.get('/orphaned')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/orphaned/')
        self.assertEqual(output.status_code, 200)

        expected = "<h1>Search packages</h1>"

        self.assertTrue(expected in output.data)

        expected = '<p>See the list of <a href="/packages/">active</a>\n' \
                   'or <a href="/retired/">retired</a> packages</p>'

        self.assertTrue(expected in output.data)

    def test_list_retired(self):
        """ Test the list_retired function. """
        output = self.app.get('/retired')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/retired/')
        self.assertEqual(output.status_code, 200)

        expected = "<h1>Search packages</h1>"

        self.assertTrue(expected in output.data)

        expected = '<p>See the list of <a href="/packages/">active</a>\n' \
                   'or <a href="/orphaned/">orphaned</a> packages</p>'

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
    PkgDB stores currently information about 0
    active Fedora releases.
</p>"""

        self.assertTrue(expected in output.data)

    def test_search(self):
        """ Test the search function. """
        output = self.app.get('/search')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/search/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Search packages</h1>' in output.data)

        create_package_acl(self.session)

        output = self.app.get('/search/?term=g*', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Search packages</h1>' in output.data)
        self.assertTrue('<a href="/package/geany/">' in output.data)
        self.assertTrue('<a href="/package/guake/">' in output.data)

        output = self.app.get('/search/?term=p&type=packager',
                              follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Search packagers</h1>' in output.data)
        self.assertTrue('<a href="/packager/pingou/">' in output.data)

        output = self.app.get('/search/?term=g*', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Search packages</h1>' in output.data)
        self.assertTrue('<a href="/package/geany/">' in output.data)
        self.assertTrue('<a href="/package/guake/">' in output.data)

        output = self.app.get('/search/?term=g*&type=orphaned',
                              follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Search packages</h1>' in output.data)
        self.assertTrue('<p>0 packages found</p>' in output.data)
        expected = '<p>See the list of <a href="/packages/">active</a>\n' \
                   'or <a href="/retired/">retired</a> packages</p>'
        self.assertTrue(expected in output.data)

        output = self.app.get('/search/?term=g*&type=retired',
                              follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Search packages</h1>' in output.data)
        self.assertTrue('<p>0 packages found</p>' in output.data)
        expected = '<p>See the list of <a href="/packages/">active</a>\n' \
                   'or <a href="/orphaned/">orphaned</a> packages</p>'
        self.assertTrue(expected in output.data)

    def test_msg(self):
        """ Test the msg function. """
        output = self.app.get('/msg')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/msg/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<a href="javascript:history.back()"><button>'
                        'Back</button></a>' in output.data)

    def test_login(self):
        """ Test the login function. """
        output = self.app.get('/login')
        self.assertEqual(output.status_code, 301)

        #output = self.app.get('/login/')
        #self.assertEqual(output.status_code, 200)
        #print output.data

    def test_logout(self):
        """ Test the logout function. """
        output = self.app.get('/logout')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/logout/')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/logout/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Fedora Package Database -- Version'
                        in output.data)

        user = FakeFasUser()
        with user_set(pkgdb2.APP, user):
            output = self.app.get('/logout/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">You are no longer logged-in</li>'
                in output.data)
            self.assertTrue('<h1>Fedora Package Database -- Version'
                            in output.data)

    def test_api(self):
        """ Test the api function. """

        output = self.app.get('/api/')
        self.assertEqual(output.status_code, 200)

        expected = """
<h2>Collections</h2>


<div class="accordion">
<h3 class="title">New collection</h3>
<div>
<p>Create a new collection.</p>
<pre class="literal-block">
/api/collection/new/
</pre>
<p>Accept POST queries only.</p>
<table class="docutils field-list" frame="void" rules="none">
<col class="field-name" />
<col class="field-body" />
<tbody valign="top">
<tr class="field"><th class="field-name" colspan="2">arg """\
"""collection_name:</th></tr>
<tr class="field"><td>&nbsp;</td><td class="field-body">String of the """\
"""collection name to be created.</td>
"""
        self.assertTrue(expected in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
