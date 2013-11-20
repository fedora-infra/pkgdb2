Fedora PackageDB
================

PackageDB2 is a rewrite of `packagedb <https://fedorahosted.org/packagedb/>`_
to use flask.

This project will be merged into packagedb when deemed descent enough and when
we get closer to a release.

This is work in progress, consider it as such.

Hacking
-------

Here are some preliminary instructions about how to stand up your own instance
of packagedb2.  We'll use a virtualenv and a sqlite database and we'll install
our dependencies from the Python Package Index (PyPI).  None of these are best
practices for a production instance, but we haven't gotten around to writing
and testing those instructions yet.

First, set up a virtualenv::

    $ sudo yum install python-virtualenv
    $ virtualenv my-pkgdb2-env
    $ source my-pkgdb2-env/bin/activate

Issueing that last command should change your prompt to indicate that you are
operating in an active virtualenv.

Next, install your dependencies::

    (my-pkgdb2-env)$ pip install kitchen paver urllib3
    (my-pkgdb2-env)$ pip install git+https://github.com/fedora-infra/python-fedora.git
    (my-pkgdb2-env)$ pip install -r requirements.txt
    (my-pkgdb2-env)$ pip install -r test_requirements.txt

You should run the test suite to make sure nothing is broken before proceeding::

    (my-pkgdb2-env)$ ./runtests.sh

They'll take a little while (since they interact with the awesome `faitout
<https://github.com/fedora-infra/faitout>`_ project).

If all goes well, you can start a development instance of the server by
running::

    (my-pkgdb2-env)$ python runserver.py

Open your browser and visit http://localhost:5000 to check it out.


Deploying
---------

We need instructions here for

1. installing packagedb2 from yum
2. installing, initializing, and configuring a postgresql db
3. installing and configuring apache/mod_wsgi
4. setting up any configuration specific to packagedb2 itself.
