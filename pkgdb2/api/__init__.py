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
API namespace for the Flask application.
'''

import flask


API = flask.Blueprint('api_ns', __name__, url_prefix='/api')

from pkgdb2 import __version__, __api_version__, APP
from pkgdb2.doc_utils import load_doc


def get_limit():
    """ Retrieve the limit used to limit the output retrieved. """
    limit = flask.request.args.get('limit', 250)
    try:
        limit = int(limit)
    except ValueError:
        limit = 250

    if limit > 500:
        limit = 500

    return limit


from pkgdb2.api import acls
from pkgdb2.api import collections
from pkgdb2.api import extras
from pkgdb2.api import packagers
from pkgdb2.api import packages


@APP.template_filter('InsertDiv')
def insert_div(content):
    """ Template filter inserting an opening <div> and closing </div>
    after the first title and then at the end of the content.
    """
    # This is quite a hack but simpler solution using .replace() didn't work
    # for some reasons...
    content = content.split('\n')
    output = []
    for row in content:
        if row.startswith('<div class="document" id='):
            output.append('<div class="accordion">')
            continue
        output.append(row)
    output = "\n".join(output)
    output = output.replace('blockquote', 'div')
    output = output.replace('h1', 'h3')

    return output


@API.context_processor
def inject_pkgdb_version():
    """ Inject whether the pkgdb2 version number on every template of this
    namespace as well.
    """
    return dict(version=__version__)


@API.route('/')
def api():
    ''' Display the api information page. '''
    api_collection_new = load_doc(collections.api_collection_new)
    api_collection_status = load_doc(collections.api_collection_status)
    api_collection_list = load_doc(collections.api_collection_list)

    api_packager_acl = load_doc(packagers.api_packager_acl)
    api_packager_list = load_doc(packagers.api_packager_list)
    api_packager_stats = load_doc(packagers.api_packager_stats)

    api_package_info = load_doc(packages.api_package_info)
    api_package_new = load_doc(packages.api_package_new)
    api_package_orphan = load_doc(packages.api_package_orphan)
    api_package_unorphan = load_doc(packages.api_package_unorphan)
    api_package_retire = load_doc(packages.api_package_retire)
    api_package_unretire = load_doc(packages.api_package_unretire)
    api_package_list = load_doc(packages.api_package_list)

    api_acl_update = load_doc(acls.api_acl_update)
    api_acl_reassign = load_doc(acls.api_acl_reassign)

    api_extras_bugzilla = load_doc(extras.api_bugzilla)
    api_extras_critpath = load_doc(extras.api_critpath)
    api_extras_notify = load_doc(extras.api_notify)
    api_extras_notify_all = load_doc(extras.api_notify_all)
    api_extras_vcs = load_doc(extras.api_vcs)

    return flask.render_template(
        'api.html',
        collections=[
            api_collection_new,
            api_collection_status,
            api_collection_list,
        ],
        packagers=[
            api_packager_list, api_packager_acl, api_packager_stats
        ],
        packages=[
            api_package_info, api_package_list,
            api_package_new, api_package_orphan, api_package_unorphan,
            api_package_retire, api_package_unretire,
        ],
        acls=[
            api_acl_update, api_acl_reassign,
        ],
        extras=[
            api_extras_bugzilla, api_extras_critpath,
            api_extras_notify, api_extras_notify_all,
            api_extras_vcs
        ]
    )


@API.route('/version/')
@API.route('/version')
def api_version():
    ''' Display the api version information. '''
    return flask.jsonify({'version': __api_version__})
