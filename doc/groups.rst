Group maintainership
====================

PkgDB2 integrates the possibility for FAS group to get ``watchcommits``,
``watchbugzilla`` and ``commit`` ACLs.

.. note:: Please note that FAS group cannot get ``approveacls`` permissions.
          This is to prevent anyone in the group to approve him/herself and drop
          the ACLs for everybody else.


There are some requirements for the FAS group:

* name must end with ``-sig``
* must be of type ``pkgdb``
* must require people to be in the ``packager`` group
* must have a mailing list address
* must require sponsoring


One requirement for the mailing list address:

* The mailing list address given to the FAS group must have a corresponding
  bugzilla account


.. note:: If you wish to share you ACLs with a FAS group, open a new ticket on
          the `infrastructure pagure.io tracker <https://pagure.io/fedora-infrastructure/new_issue>`_.



Once the group has been created in FAS, you may give it ``commit``,
``watchcommits`` and ``watchbugzilla`` ACLs using the ``Manage`` button on
the package's page.

On the manage page, you will have to click on ``Add someone`` and specify
which ACL you want to give and on which branch.

.. note:: For groups, the packager name will then have the format
    ``group::<fas_group_name>``.
    If you do not respect this format, pkgdb2 will refuse to add the group as
    co-maintainer.


The suggested package configuration for groups maintenance is:

* Since group cannot have ``approveacls`` permissions, there have to be
  at least one explicit "human" package administrator.
* Group should have ``commits`` bit. This allows every member of the
  group to make changes to package in dist-git. This is actually the main
  purpose of groups.
* Add ``watchcommits`` bit to allow notification of the group members about
  changes in the package dist-git.
* Group should have ``watchbugzilla`` permissions to allow group to be
  notified about bugzilla issues associated with the package.
* Optionally, the group can become PoC of the package. This effectively
  results only in change of default assignee in bugzilla, nothing else.
* All users who are members of the group might be optionally removed from
  the ``commits``, ``watchcommits`` and ``watchbugzilla`` lists, since they
  inherit the group rights.
