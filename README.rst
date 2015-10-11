Fedora PackageDB
================

PackageDB2 is a rewrite of `packagedb <https://fedorahosted.org/packagedb/>`_
using flask.

PackageDB is the package database for Fedora.

It is the application handling who is allowed to commit on the git of the
Fedora packages, it also handles who is the person getting the bugs on the
bugzilla and who get the notifications for changes in the git, builds or bugs.


:Project page: https://fedorahosted.org/pkgdb2/
:Documentation: http://pkgdb2.rtfd.org
:Git repository: http://git.fedorahosted.org/git/pkgdb2
:Github mirror: https://github.com/fedora-infra/pkgdb2
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
    (my-pkgdb2-env)$ git clone https://github.com/fedora-infra/pkgdb2.git
    (my-pkgdb2-env)$ cd pkgdb2
    (my-pkgdb2-env)$ pip install -r requirements.txt
    (my-pkgdb2-env)$ pip install -r test_requirements.txt

You should run the test suite to make sure nothing is broken before proceeding::

    (my-pkgdb2-env)$ ./runtests.sh

By default the tests are ran against a local sqlite database, but you can have
them run against `faitout <https://github.com/fedora-infra/faitout>`_ by setting
an environment variable ``BUILD_ID``, for example::

    (my-pkgdb2-env)$ BUILD_ID=1 ./runtests.sh

Similarly, you can set the environment variable ``OFFLINE`` to skip tests
requiring network access (handy if you are, for example, working on a plane),
for example::

    (my-pkgdb2-env)$ OFFLINE=2 ./runtests.sh


You should then create your own sqlite database for your development instance of
pkgdb2::

    (my-pkgdb2-env)$ python createdb.py

Setting up PostgreSQL
=====================

Using PostgreSQL is optional but if you want to work with real datadump then
setting up PostgreSQL will be a better option

For setting up the PostgreSQL database you can look into the `Fedora documentation about PostgresQL
<https://fedoraproject.org/wiki/PostgreSQL>`_

.. note:: If you need/want a copy of the database used in production, follow the
          instructions in the `documentation
          <http://pkgdb2.readthedocs.org/en/latest/development.html#get-a-working-database>`_

After executing all the above steps, you now need to  `Adjust Postgresql Connection Settings
<https://github.com/fedora-infra/bodhi#3-adjust-postgresql-connection-settings>`_

Now, you need to edit `/pkgdb2/default_config.py` file and replace::

    DB_URL = 'sqlite:////var/tmp/pkgdb2_dev.sqlite'

by::

    DB_URL = 'postgresql://postgres:whatever@localhost/pkgdb2'

If all goes well, you can start a development instance of the server by
running::

    (my-pkgdb2-env)$ python runserver.py

Open your browser and visit http://localhost:5000 to check it out.


For more information about the project configuration or deployment, check out
the `documentation <http://pkgdb2.readthedocs.org>`_
