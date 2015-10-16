Pkgdb2
=======

The Pkgdb project is the application handling who is allowed to work on
which package present in the Fedora repositories.



Resources:

- `Home page <http://fedorahosted.org/pkgdb2/>`_
- `Documentation <http://packagedb.rtfd.org/>`_
- `Git repository <http://git.fedorahosted.org/git/pkgdb2>`_
- `Github mirror <https://github.com/fedora-infra/pkgdb2>`_
- `Discussion mailing-list
  <https://lists.fedorahosted.org/mailman/listinfo/packagedb>`_


Contents:

.. toctree::
   :maxdepth: 2

   deployment
   configuration
   groups
   development
   contributing
   contributors



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`



FAQ
===

Here are some answers to frequently-asked questions from IRC and elsewhere.
Got a question that isn't answered here? Try `IRC <irc://irc.freenode.net/fedora-apps>`_,
the `mailing list <https://lists.fedorahosted.org/mailman/listinfo/packagedb>`_.

How do I...
===========

...specify comaintainers on a new package request?
--------------------------------------------------

Once the package is created you can add other packagers, pseudo-users or groups:

    1. Go to one of your package: https://admin.fedoraproject.org/pkgdb/package/<package_name>/
    2. Click on: Manage the committers/watchers/package administrators/main contacts (any of these)
    3. There is then an ``Add`` someone button you can use.

