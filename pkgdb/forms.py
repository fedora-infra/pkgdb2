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


class AddCollectionForm(wtf.Form):
    collection_name = wtf.TextField('Collection name',
                                    [wtf.validators.Required()])
    collection_version = wtf.TextField('version',
                                       [wtf.validators.Required()])
    collection_status = wtf.SelectField(
        'Status',
        [wtf.validators.Required()],
        choices=[('EOL', 'EOL'),
                 ('Active', 'Active'),
                 ('Under Development', 'Under Development')]
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
        choices=[('EOL', 'EOL'),
                 ('Active', 'Active'),
                 ('Under Development', 'Under Development')]
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
        choices=[('Approved', 'Approved'),
                 ('Awaiting Review', 'Awaiting Review'),
                 ('Denied', 'Denied'),
                 ('Obsolete', 'Obsolete'),
                 ('Removed', 'Removed')]
    )
    pkg_shouldopen = wtf.BooleanField('Should open',
                                      [wtf.validators.Required()],
                                      default=True)
    pkg_collection = wtf.SelectMultipleField(
        'Collection',
        [wtf.validators.Required()],
        choices=[(item, item) for item in []]
    )
    pkg_owner = wtf.TextField('Owner', [wtf.validators.Required()])
    pkg_upstreamURL = wtf.TextField('Upstream URL',
                                    [wtf.validators.optional()])

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal argument but
        uses the list of collection provided to fill the choices of the
        pkg_collection.
        """
        super(AddPackageForm, self).__init__(*args, **kwargs)
        if 'collections' in kwargs:
            tmp = []
            for collec in kwargs['collections']:
                tmp.append((collec.branchname, collec.branchname))
            self.pkg_collection.choices = tmp



class SetAclPackageForm(wtf.Form):
    pkg_name = wtf.TextField('Package name',
                             [wtf.validators.Required()])
    pkg_branch = wtf.TextField('Fedora branch',
                               [wtf.validators.Required()])
    pkg_acl = wtf.SelectField(
        'ACL',
        [wtf.validators.Required()],
        choices=[('commit', 'commit'),
                 ('build', 'build'),
                 ('watchbugzilla', 'watchbugzilla'),
                 ('watchcommits', 'watchcommits'),
                 ('approveacls', 'approveacls')]
    )
    pkg_user = wtf.TextField('Packager name',
                             [wtf.validators.Required()])
    pkg_status = wtf.SelectField(
        'Status',
        [wtf.validators.Required()],
        choices=[('Approved', 'Approved'),
                 ('Awaiting Review', 'Awaiting Review'),
                 ('Denied', 'Denied'),
                 ('Obsolete', 'Obsolete'),
                 ('Removed', 'Removed')]
    )


class PackageStatusForm(wtf.Form):
    pkg_name = wtf.TextField('Package name',
                             [wtf.validators.Required()])
    collection_name = wtf.TextField('Collection name',
                                    [wtf.validators.Required()])
    pkg_status = wtf.SelectField(
        'Status',
        [wtf.validators.Required()],
        choices=[('Approved', 'Approved'),
                 ('Awaiting Review', 'Awaiting Review'),
                 ('Denied', 'Denied'),
                 ('Obsolete', 'Obsolete'),
                 ('Removed', 'Removed')]
    )


class PackageOwnerForm(wtf.Form):
    pkg_name = wtf.TextField('Package name',
                             [wtf.validators.Required()])
    clt_name = wtf.TextField('Fedora branch',
                             [wtf.validators.Required()])
    pkg_owner = wtf.TextField('New package owner',
                              [wtf.validators.Required()])


class DeprecatePackageForm(wtf.Form):
    pkg_name = wtf.TextField('Package name',
                             [wtf.validators.Required()])
    clt_name = wtf.TextField('Fedora branch',
                             [wtf.validators.Required()])
