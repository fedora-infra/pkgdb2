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
WTF Forms of the pkgdb Flask application.
'''

import flask
from flask.ext import wtf
import wtforms


class AddCollectionForm(wtf.Form):
    collection_name = wtforms.TextField(
        'Collection name',
        [wtforms.validators.Required()]
    )
    collection_version = wtforms.TextField(
        'version',
        [wtforms.validators.Required()]
    )
    collection_status = wtforms.SelectField(
        'Status',
        [wtforms.validators.Required()],
        choices=[(item, item) for item in []]
    )
    collection_publishURLTemplate = wtforms.TextField('Publish URL template')
    collection_pendingURLTemplate = wtforms.TextField('Pending URL template')
    collection_summary = wtforms.TextField('Summary')
    collection_description = wtforms.TextField('Description')
    collection_branchname = wtforms.TextField(
        'Branch name',
        [wtforms.validators.Required()]
    )
    collection_distTag = wtforms.TextField(
        'Dist tag',
        [wtforms.validators.Required()]
    )
    collection_git_branch_name = wtforms.TextField('Git branch name')

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal argument but
        uses the list of collection provided to fill the choices of the
        drop-down list.
        """
        super(AddCollectionForm, self).__init__(*args, **kwargs)
        if 'clt_status' in kwargs:
            self.collection_status.choices = [
                (status, status)
                for status in kwargs['clt_status']
            ]
        if 'collection' in kwargs:
            collection = kwargs['collection']
            self.collection_name.data = collection.name
            self.collection_version.data = collection.version
            self.collection_publishURLTemplate.data = \
                collection.publishURLTemplate
            self.collection_pendingURLTemplate.data = \
                collection.pendingURLTemplate
            self.collection_summary.data = collection.summary
            self.collection_description.data = collection.description
            self.collection_branchname.data = collection.branchname
            self.collection_distTag.data = collection.distTag
            self.collection_git_branch_name.data = collection.git_branch_name

            # Set the drop down menu to the current value
            opt = (collection.status, collection.status)
            ind = self.collection_status.choices.index(opt)
            del(self.collection_status.choices[ind])
            self.collection_status.choices.insert(
                0, opt)


class CollectionStatusForm(wtf.Form):
    collection_branchname = wtforms.TextField(
        'Branch name',
        [wtforms.validators.Required()]
    )
    collection_status = wtforms.SelectField(
        'Status',
        [wtforms.validators.Required()],
        choices=[(item, item) for item in []]
    )

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal argument but
        uses the list of collection provided to fill the choices of the
        drop-down list.
        """
        super(CollectionStatusForm, self).__init__(*args, **kwargs)
        if 'clt_status' in kwargs:
            self.collection_status.choices = [
                (status, status)
                for status in kwargs['clt_status']
            ]


class AddPackageForm(wtf.Form):
    pkg_name = wtforms.TextField(
        'Package name',
        [wtforms.validators.Required()]
    )
    pkg_summary = wtforms.TextField(
        'Summary',
        [wtforms.validators.Required()]
    )
    pkg_reviewURL = wtforms.TextField(
        'Review URL',
        [wtforms.validators.Required()]
    )
    pkg_status = wtforms.SelectField(
        'Status',
        [wtforms.validators.Required()],
        choices=[(item, item) for item in []]
    )
    pkg_shouldopen = wtforms.BooleanField(
        'Should open',
        [wtforms.validators.Required()],
        default=True
    )
    pkg_collection = wtforms.SelectMultipleField(
        'Collection',
        [wtforms.validators.Required()],
        choices=[(item, item) for item in []]
    )
    pkg_poc = wtforms.TextField(
        'Point of contact',
        [wtforms.validators.Required()]
    )
    pkg_upstreamURL = wtforms.TextField(
        'Upstream URL',
        [wtforms.validators.optional()]
    )

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal argument but
        uses the list of collection provided to fill the choices of the
        drop-down list.
        """
        super(AddPackageForm, self).__init__(*args, **kwargs)
        if 'collections' in kwargs:
            self.pkg_collection.choices = [
                (collec.branchname, collec.branchname)
                for collec in kwargs['collections']
            ]
        if 'pkg_status_list' in kwargs:
            self.pkg_status.choices = [
                (status, status)
                for status in kwargs['pkg_status_list']
            ]


class SetAclPackageForm(wtf.Form):
    pkg_name = wtforms.TextField(
        'Package name',
        [wtforms.validators.Required()]
    )
    pkg_branch = wtforms.TextField(
        'Fedora branch',
        [wtforms.validators.Required()]
    )
    pkg_acl = wtforms.SelectField(
        'ACL',
        [wtforms.validators.Required()],
        choices=[(item, item) for item in []]
    )
    pkg_user = wtforms.TextField(
        'Packager name',
        [wtforms.validators.Required()]
    )
    pkg_status = wtforms.SelectField(
        'Status',
        [wtforms.validators.Required()],
        choices=[(item, item) for item in []]
    )

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal argument but
        uses the list of collection provided to fill the choices of the
        drop-down list.
        """
        super(SetAclPackageForm, self).__init__(*args, **kwargs)
        if 'pkg_status' in kwargs:
            self.pkg_status.choices = [
                (status, status)
                for status in kwargs['pkg_status']
            ]
        if 'acl_status' in kwargs:
            self.pkg_acl.choices = [
                (status, status)
                for status in kwargs['acl_status']
            ]


class RequestAclPackageForm(wtf.Form):
    pkg_branch = wtforms.SelectMultipleField(
        'Branch',
        [wtforms.validators.Required()],
        choices=[('', '')])

    pkg_acl = wtforms.SelectMultipleField(
        'ACL',
        [wtforms.validators.Required()],
        choices=[('', '')]
    )

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal argument but
        uses the list of collection provided to fill the choices of the
        drop-down list.
        """
        super(RequestAclPackageForm, self).__init__(*args, **kwargs)
        if 'collections' in kwargs:
            self.pkg_branch.choices = [
                (collec.branchname, collec.branchname)
                for collec in kwargs['collections']
            ]
        if 'pkg_acl_list' in kwargs:
            self.pkg_acl.choices = [
                (status, status)
                for status in kwargs['pkg_acl_list']
            ]


class UpdateAclPackageForm(wtf.Form):
    pkg_branch = wtforms.SelectMultipleField(
        'Branch',
        [wtforms.validators.Required()],
        choices=[('', '')])
    pkg_acl = wtforms.SelectMultipleField(
        'ACL',
        [wtforms.validators.Required()],
        choices=[(item, item) for item in []]
    )
    acl_status = wtforms.SelectField(
        'Status',
        [wtforms.validators.Required()],
        choices=[(item, item) for item in []]
    )

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal arguments.
        Fill the SelectField using the additionnal arguments provided.
        """
        super(UpdateAclPackageForm, self).__init__(*args, **kwargs)
        if 'collections' in kwargs:
            self.pkg_branch.choices = [
                (collec, collec)
                for collec in kwargs['collections']
            ]
        if 'pkg_status' in kwargs:
            self.acl_status.choices = [
                (status, status)
                for status in kwargs['pkg_status']
            ]
        if 'pkg_acl_list' in kwargs:
            self.pkg_acl.choices = [
                (status, status)
                for status in kwargs['pkg_acl_list']
            ]


class PackageStatusForm(wtf.Form):
    pkg_name = wtforms.TextField(
        'Package name',
        [wtforms.validators.Required()]
    )
    collection_name = wtforms.TextField(
        'Collection name',
        [wtforms.validators.Required()]
    )
    pkg_status = wtforms.SelectField(
        'Status',
        [wtforms.validators.Required()],
        choices=[(item, item) for item in []]
    )

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal argument but
        uses the list of collection provided to fill the choices of the
        drop-down list.
        """
        super(PackageStatusForm, self).__init__(*args, **kwargs)
        if 'pkg_status' in kwargs:
            self.pkg_status.choices = [
                (status, status)
                for status in kwargs['pkg_status']
            ]


class PackageOwnerForm(wtf.Form):
    pkg_name = wtforms.TextField(
        'Package name',
        [wtforms.validators.Required()]
    )
    clt_name = wtforms.TextField(
        'Fedora branch',
        [wtforms.validators.Required()]
    )
    pkg_poc = wtforms.TextField(
        'New point of contact',
        [wtforms.validators.Required()]
    )


class DeprecatePackageForm(wtf.Form):
    pkg_name = wtforms.TextField(
        'Package name',
        [wtforms.validators.Required()]
    )
    clt_name = wtforms.TextField(
        'Fedora branch',
        [wtforms.validators.Required()]
    )


class GivePoCForm(wtf.Form):
    pkg_branch = wtforms.SelectMultipleField(
        'Branch',
        [wtforms.validators.Required()],
        choices=[('', '')])
    pkg_poc = wtforms.TextField(
        'New point of contact',
        [wtforms.validators.Required()]
    )

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal arguments.
        Fill the SelectField using the additionnal arguments provided.
        """
        super(GivePoCForm, self).__init__(*args, **kwargs)
        if 'collections' in kwargs:
            self.pkg_branch.choices = [
                (collec, collec)
                for collec in kwargs['collections']
            ]
