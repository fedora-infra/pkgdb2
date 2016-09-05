Fedora PackageDB
================

PackageDB2 is a rewrite of `packagedb <https://fedorahosted.org/packagedb/>`_
using flask.

PackageDB is the package database for Fedora.

It is the application handling who is allowed to commit on the git of the
Fedora packages, it also handles who is the person getting the bugs on the
bugzilla and who get the notifications for changes in the git, builds or bugs.


:Project page: https://fedorahosted.org/pkgdb2/
:Documentation: https://pkgdb2.readthedocs.org/
:Git repository: https://git.fedorahosted.org/git/pkgdb2
:Github mirror: https://github.com/fedora-infra/pkgdb2
:Mailing list: https://lists.fedorahosted.org/mailman/listinfo/packagedb


Hacking
=======

Hacking with Vagrant
--------------------
Quickly start hacking on pkgdb2 using the vagrant setup that is included in the
pkgdb2 repo is super simple.

First, install Ansible, Vagrant and the vagrant-libvirt plugin from the official Fedora
repos::

    $ sudo dnf install ansible vagrant vagrant-libvirt

The pkgdb2 vagrant setup uses vagrant-sshfs for syncing files between your host
and the vagrant dev machine. vagrant-sshfs is not in the Fedora repos (yet), so
we install the vagrant-sshfs plugin from dustymabe's COPR repo::

    $ sudo dnf copr enable dustymabe/vagrant-sshfs
    $ sudo dnf install vagrant-sshfs

Now, from within main directory (the one with the Vagrantfile in it) of your git
checkout of pkgdb, run the ``vagrant up`` command to provision your dev
environment::

    $ vagrant up

When this command is completed (it may take a while) you will be able to ssh
into your dev VM with ``vagrant ssh`` and then run the command to start the
pkgdb2 server::

    $ vagrant ssh
    [vagrant@localhost ~]$ pushd /vagrant/; ./runserver.py -c pkgdb2/vagrant_default_config.py --host "0.0.0.0";

Once that is running, simply go to http://localhost:5001/ in your browser on
your host to see your running pkgdb2 test instance.

Setting up a Dev Environment by hand
------------------------------------

Here are some preliminary instructions about how to stand up your own instance
of packagedb2.  We'll use a virtualenv and a sqlite database and we'll install
our dependencies from the Python Package Index (PyPI).  None of these are best
practices for a production instance, but we haven't gotten around to writing
and testing those instructions yet.

First, set up a virtualenv::

    $ sudo yum install python-virtualenv
    $ virtualenv my-pkgdb2-env
    $ source my-pkgdb2-env/bin/activate

Issuing that last command should change your prompt to indicate that you are
operating in an active virtualenv.

Next, install your dependencies::

    (my-pkgdb2-env)$ pip install kitchen paver urllib3
    (my-pkgdb2-env)$ git clone https://github.com/fedora-infra/pkgdb2.git
    (my-pkgdb2-env)$ cd pkgdb2
    (my-pkgdb2-env)$ pip install -r requirements.txt
    (my-pkgdb2-env)$ sudo dnf install postgresql-devel  # required for psycopg2
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
~~~~~~~~~~~~~~~~~~~~~

Using PostgreSQL is optional but if you want to work with real datadump then
setting up PostgreSQL will be a better option

For setting up the PostgreSQL database you can look into the `Fedora documentation about PostgresQL
<https://fedoraproject.org/wiki/PostgreSQL>`_

.. note:: If you need/want a copy of the database used in production, follow the
          instructions in the `documentation
          <https://pkgdb2.readthedocs.org/en/latest/development.html#get-a-working-database>`_

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
the `documentation <https://pkgdb2.readthedocs.org>`_
