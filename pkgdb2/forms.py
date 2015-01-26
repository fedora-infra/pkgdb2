# -*- coding: utf-8 -*-
#
# Copyright © 2013-2014  Red Hat, Inc.
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

## pylint cannot import flask extension correctly
# pylint: disable=E0611,F0401
## The forms here don't have specific methods, they just inherit them.
# pylint: disable=R0903
## We apparently use old style super in our __init__
# pylint: disable=E1002
## Couple of our forms do not even have __init__
# pylint: disable=W0232


from flask.ext import wtf
import wtforms


## Yes we do nothing with the form argument but they are required...
# pylint: disable=W0613
def is_number(form, field):
    ''' Check if the data in the field is a number and raise an exception
    if it is not.
    '''
    try:
        float(field.data)
    except ValueError:
        raise wtforms.ValidationError('Field must contain a number')


class AddCollectionForm(wtf.Form):
    """ Form to add or edit collections. """
    clt_name = wtforms.TextField(
        'Collection name',
        [wtforms.validators.Required()]
    )
    version = wtforms.TextField(
        'version',
        [wtforms.validators.Required()]
    )
    clt_status = wtforms.SelectField(
        'Status',
        [wtforms.validators.Required()],
        choices=[(item, item) for item in []]
    )
    branchname = wtforms.TextField(
        'Branch name',
        [wtforms.validators.Required()]
    )
    kojiname = wtforms.TextField(
        'Koji name',
        [wtforms.validators.Required()]
    )
    dist_tag = wtforms.TextField(
        'Dist tag',
        [wtforms.validators.Required()]
    )

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal argument but
        uses the list of collection provided to fill the choices of the
        drop-down list.
        """
        super(AddCollectionForm, self).__init__(*args, **kwargs)
        if 'clt_status' in kwargs:
            self.clt_status.choices = [
                (status, status)
                for status in kwargs['clt_status']
            ]
        if 'collection' in kwargs:
            collection = kwargs['collection']
            self.clt_name.data = collection.name
            self.version.data = collection.version
            self.branchname.data = collection.branchname
            self.dist_tag.data = collection.dist_tag
            self.kojiname.data = collection.koji_name

            # Set the drop down menu to the current value
            opt = (collection.status, collection.status)
            ind = self.clt_status.choices.index(opt)
            del(self.clt_status.choices[ind])
            self.clt_status.choices.insert(
                0, opt)


class CollectionStatusForm(wtf.Form):
    """ Form to update the status of a collection. """
    branch = wtforms.TextField(
        'Branch name',
        [wtforms.validators.Required()]
    )
    clt_status = wtforms.SelectField(
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
            self.clt_status.choices = [
                (status, status)
                for status in kwargs['clt_status']
            ]


class AddPackageForm(wtf.Form):
    """ Form to add or edit packages. """
    pkgname = wtforms.TextField(
        'Package name',
        [wtforms.validators.Required()]
    )
    summary = wtforms.TextField(
        'Summary',
        [wtforms.validators.Required()]
    )
    description = wtforms.TextAreaField(
        'Description',
    )
    review_url = wtforms.TextField(
        'Review URL',
        [wtforms.validators.Required()]
    )
    status = wtforms.SelectField(
        'Status',
        [wtforms.validators.Required()],
        choices=[(item, item) for item in []]
    )
    critpath = wtforms.BooleanField(
        'Package in critpath',
        [wtforms.validators.optional()],
        default=False,
    )
    branches = wtforms.SelectMultipleField(
        'Collection',
        [wtforms.validators.Required()],
        choices=[(item, item) for item in []]
    )
    poc = wtforms.TextField(
        'Point of contact',
        [wtforms.validators.Required()]
    )
    upstream_url = wtforms.TextField(
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
            self.branches.choices = [
                (collec.branchname, collec.branchname)
                for collec in kwargs['collections']
            ]
        if 'pkg_status_list' in kwargs:
            self.status.choices = [
                (status, status)
                for status in kwargs['pkg_status_list']
            ]


class EditPackageForm(wtf.Form):
    """ Form to edit packages. """
    pkgname = wtforms.TextField(
        'Package name',
        [wtforms.validators.Required()]
    )
    summary = wtforms.TextField(
        'Summary',
        [wtforms.validators.optional()]
    )
    description = wtforms.TextField(
        'Description',
    )
    review_url = wtforms.TextField(
        'Review URL',
        [wtforms.validators.optional()]
    )
    status = wtforms.SelectField(
        'Status',
        [wtforms.validators.optional()],
        choices=[(item, item) for item in []]
    )
    upstream_url = wtforms.TextField(
        'Upstream URL',
        [wtforms.validators.optional()]
    )

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal argument but
        uses the list of collection provided to fill the choices of the
        drop-down list.
        """
        super(EditPackageForm, self).__init__(*args, **kwargs)
        if 'pkg_status_list' in kwargs:
            self.status.choices = [
                (status, status)
                for status in kwargs['pkg_status_list']
            ]


class SetAclPackageForm(wtf.Form):
    """ Form to set ACLs to someone on a package. """
    pkgname = wtforms.TextField(
        'Package name',
        [wtforms.validators.Required()]
    )
    branches = wtforms.SelectMultipleField(
        'Branch',
        [wtforms.validators.Required()],
        choices=[('', '')]
    )
    acl = wtforms.SelectMultipleField(
        'ACL',
        [wtforms.validators.Required()],
        choices=[(item, item) for item in []]
    )
    user = wtforms.TextField(
        'Packager name',
        [wtforms.validators.Required()]
    )
    acl_status = wtforms.SelectField(
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
        if 'collections' in kwargs:
            self.branches.choices = [
                (collec, collec)
                for collec in kwargs['collections']
            ]
        if 'collections_obj' in kwargs:
            self.branches.choices = [
                (collec.branchname, collec.branchname)
                for collec in kwargs['collections_obj']
            ]
        if 'acl_status' in kwargs:
            self.acl_status.choices = [
                (status, status)
                for status in kwargs['acl_status']
            ]
        if 'pkg_acl' in kwargs:
            self.acl.choices = [
                (acl, acl)
                for acl in kwargs['pkg_acl']
            ]


class RequestAclPackageForm(wtf.Form):
    """ Form to request ACLs on a package. """
    branches = wtforms.SelectMultipleField(
        'Branch',
        [wtforms.validators.Required()],
        choices=[('', '')])

    acl = wtforms.SelectMultipleField(
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
            self.branches.choices = [
                (collec.branchname, collec.branchname)
                for collec in kwargs['collections']
            ]
        if 'pkg_acl_list' in kwargs:
            self.acl.choices = [
                (status, status)
                for status in kwargs['pkg_acl_list']
            ]


class GivePoCForm(wtf.Form):
    """ Form to change the Point of Contact of a package. """
    branches = wtforms.SelectMultipleField(
        'Branch',
        [wtforms.validators.Required()],
        choices=[('', '')])
    poc = wtforms.TextField(
        'New point of contact',
        [wtforms.validators.Required()]
    )

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal arguments.
        Fill the SelectField using the additionnal arguments provided.
        """
        super(GivePoCForm, self).__init__(*args, **kwargs)
        if 'collections' in kwargs:
            self.branches.choices = [
                (collec, collec)
                for collec in kwargs['collections']
            ]


class BranchForm(wtf.Form):
    """ Form to perform an action on one or more branches of a package. """
    branches = wtforms.SelectMultipleField(
        'Branch',
        [wtforms.validators.Required()],
        choices=[('', '')])

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal arguments.
        Fill the SelectField using the additionnal arguments provided.
        """
        super(BranchForm, self).__init__(*args, **kwargs)
        if 'collections' in kwargs:
            self.branches.choices = [
                (collec, collec)
                for collec in kwargs['collections']
            ]


class ConfirmationForm(wtf.Form):
    """ The simplest form we can do but that ensures CSRF protection. """
    pass


class NewRequestForm(BranchForm):
    """ Form to perform an action on one or more branches of a package. """
    from_branch = wtforms.SelectField(
        'Branch from which to create this or these new branches',
        [wtforms.validators.Required()],
        choices=[('', '')])

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal arguments.
        Fill the SelectField using the additionnal arguments provided.
        """
        super(NewRequestForm, self).__init__(*args, **kwargs)
        if 'collections' in kwargs:
            self.branches.choices = [
                (collec, collec)
                for collec in kwargs['collections']
            ]
        if 'from_branch' in kwargs:
            self.from_branch.choices = [
                (collec, collec)
                for collec in kwargs['from_branch']
            ]


class EditActionStatusForm(wtf.Form):
    """ Form to update the status of an admin action. """
    id = wtforms.TextField(
        'Action identifier <span class="error">*</span>',
        [wtforms.validators.Required(), is_number]
    )
    status = wtforms.SelectField(
        'Action status',
        [wtforms.validators.Required()],
        choices=[('', '')])
    message = wtforms.TextAreaField('Message')

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal arguments.
        Fill the SelectField using the additionnal arguments provided.
        """
        super(EditActionStatusForm, self).__init__(*args, **kwargs)
        if 'status' in kwargs:
            self.status.choices = [
                (status, status)
                for status in kwargs['status']
            ]
