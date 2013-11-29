Fedora PackageDB
================

PackageDB2 is a rewrite of `packagedb <https://fedorahosted.org/packagedb/>`_
using flask.

PackageDB is the package database for Fedora.

It is the application handling who is allowed to commit on the git of the
Fedora packages, it also handles who is the person getting the bugs on the
bugzilla and who get the notifications for changes in the git, builds or bugs.


:Project page: https://fedorahosted.org/packagedb/
:Documentation: http://packagedb.rtfd.org
:Git repository: http://git.fedorahosted.org/git/packagedb
:Github mirror: https://github.com/fedora-infra/packagedb2
:Mailing list: https://lists.fedorahosted.org/mailman/listinfo/packagedb


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

You should then create your own sqlite database for your development instance of
pkgdb2::

    (my-pkgdb2-env)$ python createdb.py

If all goes well, you can start a development instance of the server by
running::

    (my-pkgdb2-env)$ python runserver.py

Open your browser and visit http://localhost:5000 to check it out.


For more information about the project configuration or deployment, check out
the `documentation <http://packagedb.rtfd.org>`_
