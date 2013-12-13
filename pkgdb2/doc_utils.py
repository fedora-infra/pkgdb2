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
Provide utility function to convert rst in docstring of functions into html
'''

import docutils
import docutils.examples
import markupsafe


def modify_rst(rst):
    """ Downgrade some of our rst directives if docutils is too old. """

    ## We catch Exception if we want :-p
    # pylint: disable=W0703
    try:
        # The rst features we need were introduced in this version
        minimum = [0, 9]
        version = [int(cpt) for cpt in docutils.__version__.split('.')]

        # If we're at or later than that version, no need to downgrade
        if version >= minimum:
            return rst
    except Exception:  # pragma: no cover
        # If there was some error parsing or comparing versions, run the
        # substitutions just to be safe.
        pass

    # On Fedora this will never work as the docutils version is to recent
    # Otherwise, make code-blocks into just literal blocks.
    substitutions = {  # pragma: no cover
        '.. code-block:: javascript': '::',
    }
    for old, new in substitutions.items():  # pragma: no cover
        rst = rst.replace(old, new)

    return rst  # pragma: no cover


def modify_html(html):
    """ Perform style substitutions where docutils doesn't do what we want.
    """

    substitutions = {
        '<tt class="docutils literal">': '<code>',
        '</tt>': '</code>',
    }
    for old, new in substitutions.items():
        html = html.replace(old, new)

    return html


def load_doc(endpoint):
    """ Utility to load an RST file and turn it into fancy HTML. """

    rst = unicode(endpoint.__doc__)

    rst = modify_rst(rst)

    api_docs = docutils.examples.html_body(rst)

    api_docs = modify_html(api_docs)

    api_docs = markupsafe.Markup(api_docs)
    return api_docs
