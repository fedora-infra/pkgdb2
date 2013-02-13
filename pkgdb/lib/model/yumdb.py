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
Mapping of tables needed in the sqlite database that goes to yum
'''

import sqlalchemy as sa
from dbtools import BASE


class YumTags(BASE):
    '''YumTags.

    A list of tags associated with packages. This metadata for the
    package can then be used by yum.

    Table -- packagetags
    '''

    __tablename__ = 'packagetags'
    name = sa.Column(sa.Text, nullable=False, primary_key=True)
    tag = sa.Column(sa.Text, nullable=False, primary_key=True)
    score = sa.Column(sa.Integer)

    def __init__(self, name, shortname, score):
        self.name = name
        self.shortname = shortname
        self.score = score

    def __repr__(self):
        return 'YumTags(%r, %r, %r)' % (self.name, self.tag, self.score)
