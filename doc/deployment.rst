Deployment
==========

From sources
------------

Clone the source::

 git clone http://git.fedorahosted.org/git/pkgdb2.git

Install the dependencies listed in the ``requirements.txt`` file.

.. note:: The ``requirements.txt`` file require flask>=0.10 but this is only
          required for the unit-tests and in fact flask<0.10 is **required** for
          python-fedora to work at the moment.
          The next release of python-fedora should fix this problem.

Copy the configuration files::

  cp pkgdb2.cfg.sample pkgdb2.cfg

Adjust the configuration files (secret key, database URL, admin group...).
See :doc:`configuration` for detailed information about the configuration.


Create the database scheme::

   PKGDB_CONFIG=/path/to/pkgdb2.cfg python createdb.py

Set up the WSGI as described below.


From system-wide packages
-------------------------

Start by install pkgdb2::

  yum install pkgdb2

Adjust the configuration files: ``/etc/pkgdb2/pkgdb2.cfg``.
See :doc:`configuration` for detailed information about the configuration.

Find the file used to create the database::

  rpm -ql pkgdb2 |grep createdb.py

Create the database scheme::

   PKGDB_CONFIG=/etc/pkgdb2/pkgdb2.cfg python path/to/createdb.py

Set up the WSGI as described below.


Set-up WSGI
-----------

Start by installing ``mod_wsgi``::

  yum install mod_wsgi


Then configure apache::

 sudo vim /etc/httd/conf.d/pkgdb2.conf

uncomment the content of the file and adjust as desired.


Then edit the file ``/usr/share/pkgdb2/pkgdb2.wsgi`` and
adjust as needed.


Then restart apache and you should be able to access the website on
http://localhost/pkgdb


.. note:: `Flask <http://flask.pocoo.org/>`_ provides also  some documentation
          on how to `deploy Flask application with WSGI and apache
          <http://flask.pocoo.org/docs/deploying/mod_wsgi/>`_.


For testing
-----------

See :doc:`development` if you want to run pkgdb2 just to test it.

