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
from math import ceil

import pkgdb2.forms
import pkgdb2.lib as pkgdblib
from pkgdb2 import SESSION, APP, is_admin
from pkgdb2.ui import UI


## Some of the object we use here have inherited methods which apparently
## pylint does not detect.
# pylint: disable=E1101


@UI.route('/collections/')
@UI.route('/collections/page/<int:page>/')
@UI.route('/collections/<motif>/')
@UI.route('/collections/<motif>/page/<int:page>/')
def list_collections(motif=None, page=1):
    ''' Display the list of collections corresponding to the motif. '''

    pattern = flask.request.args.get('motif', motif) or '*'
    limit = flask.request.args.get('limit', APP.config['ITEMS_PER_PAGE'])

    try:
        int(limit)
    except ValueError:
        limit = APP.config['ITEMS_PER_PAGE']
        flask.flash('Incorrect limit provided, using default', 'errors')

    collections = pkgdblib.search_collection(
        SESSION,
        pattern=pattern,
        page=page,
        limit=limit,
    )
    collections_count = pkgdblib.search_collection(
        SESSION,
        pattern=pattern,
        page=page,
        limit=limit,
        count=True
    )
    total_page = int(ceil(collections_count / float(limit)))

    return flask.render_template(
        'list_collections.html',
        collections=collections,
        motif=motif,
        total_page=total_page,
        page=page
    )


@UI.route('/collection/<collection>/')
def collection_info(collection):
    ''' Display the information about the specified collection. '''

    try:
        collection = pkgdblib.search_collection(SESSION, collection)[0]
    except IndexError:
        flask.flash('No collection of this name found.', 'errors')
        return flask.render_template('msg.html')

    return flask.render_template(
        'collection.html',
        collection=collection,
    )


@UI.route('/collection/<collection>/edit', methods=('GET', 'POST'))
@is_admin
def collection_edit(collection):
    ''' Allows to edit the information about the specified collection. '''

    try:
        collection = pkgdblib.search_collection(SESSION, collection)[0]
    except IndexError:
        flask.flash('No collection of this name found.', 'errors')
        return flask.render_template('msg.html')

    clt_status = pkgdblib.get_status(SESSION, 'clt_status')['clt_status']
    form = pkgdb2.forms.AddCollectionForm(
        clt_status=clt_status
    )

    if form.validate_on_submit():
        clt_name = form.collection_name.data
        clt_version = form.collection_version.data
        clt_status = form.collection_status.data
        clt_branchname = form.collection_branchname.data
        clt_disttag = form.collection_distTag.data
        clt_gitbranch = form.collection_git_branch_name.data
        clt_koji_name = form.collection_kojiname.data

        try:
            pkgdblib.edit_collection(
                SESSION,
                collection=collection,
                clt_name=clt_name,
                clt_version=clt_version,
                clt_status=clt_status,
                clt_branchname=clt_branchname,
                clt_disttag=clt_disttag,
                clt_gitbranch=clt_gitbranch,
                clt_koji_name=clt_koji_name,
                user=flask.g.fas_user,
            )
            SESSION.commit()
            flask.flash('Collection "%s" edited' % clt_branchname)
            return flask.redirect(flask.url_for(
                '.collection_info', collection=collection.branchname))
        # In theory we should never hit this
        except pkgdblib.PkgdbException, err:  # pragma: no cover
            SESSION.rollback()
            flask.flash(str(err), 'errors')
    elif flask.request.method == 'GET':
        form = pkgdb2.forms.AddCollectionForm(
            clt_status=clt_status,
            collection=collection
        )

    return flask.render_template(
        'collection_edit.html',
        form=form,
        collection=collection,
    )


@UI.route('/new/collection/', methods=('GET', 'POST'))
@is_admin
def collection_new():
    ''' Page to create a new collection. '''

    clt_status = pkgdblib.get_status(SESSION, 'clt_status')['clt_status']
    form = pkgdb2.forms.AddCollectionForm(clt_status=clt_status)
    if form.validate_on_submit():
        clt_name = form.collection_name.data
        clt_version = form.collection_version.data
        clt_status = form.collection_status.data
        clt_branchname = form.collection_branchname.data
        clt_disttag = form.collection_distTag.data
        clt_gitbranch = form.collection_git_branch_name.data
        clt_koji_name = form.collection_kojiname.data

        try:
            message = pkgdblib.add_collection(
                SESSION,
                clt_name=clt_name,
                clt_version=clt_version,
                clt_status=clt_status,
                clt_branchname=clt_branchname,
                clt_disttag=clt_disttag,
                clt_gitbranch=clt_gitbranch,
                clt_koji_name=clt_koji_name,
                user=flask.g.fas_user,
            )
            SESSION.commit()
            flask.flash(message)
            return flask.redirect(flask.url_for('.list_collections'))
        # In theory we should never hit this
        except pkgdblib.PkgdbException, err:  # pragma: no cover
            SESSION.rollback()
            flask.flash(str(err), 'errors')

    return flask.render_template(
        'collection_new.html',
        form=form,
    )
