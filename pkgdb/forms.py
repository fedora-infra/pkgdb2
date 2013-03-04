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
    collection_status = wtf.SelectField('Status',
        [wtf.validators.Required()],
        choices=[('EOL', 'EOL'),
                 ('Active', 'Active'),
                 ('Under Development', 'Under Development')]
        )
    collection_numpkgs = wtf.FloatField('numpkgs')


class AddPackageForm(wtf.Form):
    pkg_name = wtf.TextField('Package name',
                                    [wtf.validators.Required()])
    pkg_summary = wtf.TextField('Summary',
                                    [wtf.validators.Required()])
    pkg_description = wtf.TextField('Summary',
                                    [wtf.validators.optional()])
    pkg_reviewURL = wtf.URL('Review URL', [wtf.validators.Required(),
                            wtf.validators.URL()])
    pkg_status = wtf.SelectField('Status',
        [wtf.validators.Required()],
        choices=[('Approved', 'Approved'),
                 ('Awaiting Review', 'Awaiting Review'),
                 ('Denied', 'Denied'),
                 ('Obsolete', 'Obsolete'),
                 ('Removed', 'Removed')]
        )
    pkg_shouldopen = wtf.BooleanField('Should open',
                                      [wtf.validators.Required()],
                                      value=True)
    pkg_collection = wtf.SelectMultipleField('Collection',
        [wtf.validators.Required()],
        choices=[(item, item) for item in []])
    pkg_owner = wtf.TextField('Owner', [wtf.validators.optional()])
