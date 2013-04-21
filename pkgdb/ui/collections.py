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
UI namespace for the Flask application.
'''

import flask
from sqlalchemy.orm.exc import NoResultFound

import pkgdb.forms
import pkgdb.lib as pkgdblib
from pkgdb import SESSION
from pkgdb.ui import UI


class FakeFasUser(object):
    """ Fake FAS user used for the tests. """
    id = 100
    username = 'pingou'
    groups = ['packager', 'cla_done']


@UI.route('/collections/')
@UI.route('/collections/<motif>/')
@UI.route('/collections/<motif>')
def list_collections(motif=None):
    ''' Display the list of collections corresponding to the motif. '''

    pattern = flask.request.args.get('motif', motif) or '*'

    collections = pkgdblib.search_collection(SESSION,
                                             pattern=pattern
                                             )

    return flask.render_template(
        'list_collections.html',
        collections=collections,
    )


@UI.route('/collection/<collection>/')
@UI.route('/collection/<collection>')
def collection_info(collection):
    ''' Display the information about the specified collection. '''

    collections = []
    try:
        collection = pkgdblib.search_collection(SESSION, collection)[0]
    except NoResultFound:
        SESSION.rollback()

    return flask.render_template(
        'collection.html',
        collection=collection,
    )


## TODO: Restricted to admin
@UI.route('/collection/new/', methods=('GET', 'POST'))
def collection_new():
    ''' Page to create a new collection. '''

    form = pkgdb.forms.AddCollectionForm()
    if form.validate_on_submit():
        clt_name = form.collection_name.data
        clt_version = form.collection_version.data
        clt_status = form.collection_status.data
        clt_publishurl = form.collection_publishURLTemplate.data
        clt_pendingurl = form.collection_pendingURLTemplate.data
        clt_summary = form.collection_summary.data
        clt_description = form.collection_description.data
        clt_branchname = form.collection_branchname.data
        clt_disttag = form.collection_distTag.data
        clt_gitbranch = form.collection_git_branch_name.data

        try:
            message = pkgdblib.add_collection(
                SESSION,
                clt_name=clt_name,
                clt_version=clt_version,
                clt_status=clt_status,
                clt_publishurl=clt_publishurl,
                clt_pendingurl=clt_pendingurl,
                clt_summary=clt_summary,
                clt_description=clt_description,
                clt_branchname=clt_branchname,
                clt_disttag=clt_disttag,
                clt_gitbranch=clt_gitbranch,
                ## TODO: switch to flask.g.fas_user
                user=FakeFasUser(),
                #user=flask.g.fas_user,
            )
            SESSION.commit()
            flask.flash(message)
            return flask.redirect(flask.url_for('.list_collections'))
        except pkgdblib.PkgdbException, err:
            SESSION.rollback()
            flask.flash(err.message, 'error')

    return flask.render_template(
        'collection_new.html',
        form=form,
    )
