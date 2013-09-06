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


ACLS_CHOICE = [('approveacls', 'approveacls'),
               ('commit', 'commit'),
               ('watchbugzilla', 'watchbugzilla'),
               ('watchcommits', 'watchcommits')]

STATUS_CHOICE = [('Approved', 'Approved'),
                 ('Awaiting Review', 'Awaiting Review'),
                 ('Denied', 'Denied'),
                 ('Obsolete', 'Obsolete'),
                 ('Removed', 'Removed')]

CLT_STATUS_CHOICE = [('EOL', 'EOL'),
                     ('Active', 'Active'),
                     ('Under Development', 'Under Development')]


class AddCollectionForm(wtf.Form):
    collection_name = wtf.TextField('Collection name',
                                    [wtf.validators.Required()])
    collection_version = wtf.TextField('version',
                                       [wtf.validators.Required()])
    collection_status = wtf.SelectField(
        'Status',
        [wtf.validators.Required()],
        choices=CLT_STATUS_CHOICE
    )
    collection_publishURLTemplate = wtf.TextField('Publish URL template')
    collection_pendingURLTemplate = wtf.TextField('Pending URL template')
    collection_summary = wtf.TextField('Summary')
    collection_description = wtf.TextField('Description')
    collection_branchname = wtf.TextField('Branch name',
                                          [wtf.validators.Required()])
    collection_distTag = wtf.TextField('Dist tag',
                                       [wtf.validators.Required()])
    collection_git_branch_name = wtf.TextField('Git branch name')


class CollectionStatusForm(wtf.Form):
    collection_branchname = wtf.TextField('Branch name',
                                          [wtf.validators.Required()])
    collection_status = wtf.SelectField(
        'Status',
        [wtf.validators.Required()],
        choices=CLT_STATUS_CHOICE
    )


class AddPackageForm(wtf.Form):
    pkg_name = wtf.TextField('Package name',
                             [wtf.validators.Required()])
    pkg_summary = wtf.TextField('Summary',
                                [wtf.validators.Required()])
    pkg_reviewURL = wtf.TextField('Review URL',
                                  [wtf.validators.Required()])
    pkg_status = wtf.SelectField(
        'Status',
        [wtf.validators.Required()],
        choices=STATUS_CHOICE
    )
    pkg_shouldopen = wtf.BooleanField('Should open',
                                      [wtf.validators.Required()],
                                      default=True)
    pkg_collection = wtf.SelectMultipleField(
        'Collection',
        [wtf.validators.Required()],
        choices=[(item, item) for item in []]
    )
    pkg_poc = wtf.TextField('Point of contact', [wtf.validators.Required()])
    pkg_upstreamURL = wtf.TextField('Upstream URL',
                                    [wtf.validators.optional()])

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal argument but
        uses the list of collection provided to fill the choices of the
        pkg_collection.
        """
        super(AddPackageForm, self).__init__(*args, **kwargs)
        if 'collections' in kwargs:
            self.pkg_collection.choices = [
                (collec.branchname, collec.branchname)
                for collec in kwargs['collections']
            ]


class SetAclPackageForm(wtf.Form):
    pkg_name = wtf.TextField('Package name',
                             [wtf.validators.Required()])
    pkg_branch = wtf.TextField('Fedora branch',
                               [wtf.validators.Required()])
    pkg_acl = wtf.SelectField(
        'ACL',
        [wtf.validators.Required()],
        choices=ACLS_CHOICE
    )
    pkg_user = wtf.TextField('Packager name',
                             [wtf.validators.Required()])
    pkg_status = wtf.SelectField(
        'Status',
        [wtf.validators.Required()],
        choices=STATUS_CHOICE
    )


class RequestAclPackageForm(wtf.Form):
    pkg_branch = wtf.SelectMultipleField(
        'Branch',
        [wtf.validators.Required()],
        choices=[('', '')])
    pkg_acl = wtf.SelectMultipleField(
        'ACL',
        [wtf.validators.Required()],
        choices=ACLS_CHOICE
    )

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal arguments.
        Fill the SelectField using the additionnal arguments provided.
        """
        super(RequestAclPackageForm, self).__init__(*args, **kwargs)
        if 'collections' in kwargs:
            self.pkg_branch.choices = [
                (collec.branchname, collec.branchname)
                for collec in kwargs['collections']
            ]


class UpdateAclPackageForm(wtf.Form):
    pkg_branch = wtf.SelectMultipleField(
        'Branch',
        [wtf.validators.Required()],
        choices=[('', '')])
    pkg_acl = wtf.SelectMultipleField(
        'ACL',
        [wtf.validators.Required()],
        choices=ACLS_CHOICE
    )
    acl_status = wtf.SelectField(
        'Status',
        [wtf.validators.Required()],
        choices=STATUS_CHOICE
    )

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal arguments.
        Fill the SelectField using the additionnal arguments provided.
        """
        super(UpdateAclPackageForm, self).__init__(*args, **kwargs)
        if 'collections' in kwargs:
            tmp = []
            for collec in kwargs['collections']:
                tmp.append((collec, collec))
            self.pkg_branch.choices = tmp


class PackageStatusForm(wtf.Form):
    pkg_name = wtf.TextField('Package name',
                             [wtf.validators.Required()])
    collection_name = wtf.TextField('Collection name',
                                    [wtf.validators.Required()])
    pkg_status = wtf.SelectField(
        'Status',
        [wtf.validators.Required()],
        choices=STATUS_CHOICE
    )


class PackageOwnerForm(wtf.Form):
    pkg_name = wtf.TextField('Package name',
                             [wtf.validators.Required()])
    clt_name = wtf.TextField('Fedora branch',
                             [wtf.validators.Required()])
    pkg_poc = wtf.TextField('New point of contact',
                              [wtf.validators.Required()])


class DeprecatePackageForm(wtf.Form):
    pkg_name = wtf.TextField('Package name',
                             [wtf.validators.Required()])
    clt_name = wtf.TextField('Fedora branch',
                             [wtf.validators.Required()])
