Group maintainership
====================

PkgDB2 integrates the possibility for FAS group to get ``watchcommits``,
``watchbugzilla`` and ``commit`` ACLs.


There are some requirements for the FAS group:

* name must end with ``-sig``
* must be of type ``pkgdb``
* must require people to be in the ``packager`` group
* must have a mailing list address
* must require sponsoring


There is one requirement for the bugzilla group:

* The mailing list address given to the FAS group must have a corresponding
  bugzilla account


.. note:: If you wish to share you ACLs with a FAS group, `open a new ticket
          <https://fedorahosted.org/fedora-infrastructure/newticket>`_ on
          the `infrastructure trac <https://fedorahosted.org/fedora-infrastructure/>`_
          (Type: ``New Pkgdb Group``).


Once the group has been created in FAS, you may give it ``commit``,
``watchcommits`` and ``watchbugzilla`` ACLs using the ``Manage`` button on
the package's page.

On the manage page, you will have to click on ``Add someone`` and specify
which ACL you want to give and on which branch.

.. note:: For groups, the packager name will then have the format
    ``group::<fas_group_name>``.
    If you do not respect this format, pkgdb2 will refuse to add the group as
    co-maintainer.
