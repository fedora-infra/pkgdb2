Deployment
==========

From sources
------------

Clone the source::

 git clone http://git.fedorahosted.org/git/packagedb.git


Copy the configuration files::

  cp pkgdb.cfg.sample pkgdb.cfg

Adjust the configuration files (secret key, database URL, admin group...).
See :doc:`configuration` for detailed information about the configuration.


Create the database scheme::

   sh createdb

or::

   PKGDB_CONFIG=/path/to/pkgdb.cfg python createdb.py

Set up the WSGI as described below.


From system-wide packages
-------------------------

Start by install pkgdb::

  yum install packagedb

Adjust the configuration files: ``/etc/pkgdb/pkgdb.cfg``.
See :doc:`configuration` for detailed information about the configuration.

Find the file used to create the database::

  rpm -ql packagedb |grep createdb.py

Create the database scheme::

   PKGDB_CONFIG=/etc/pkgdb/pkgdb.cfg python path/to/createdb.py

Set up the WSGI as described below.


Set-up WSGI
-----------

Start by installing ``mod_wsgi``::

  yum install mod_wsgi


Then configure apache::

 sudo vim /etc/httd/conf.d/pkgdb.conf

uncomment the content of the file and adjust as desired.


Then edit the file ``/usr/share/pkgdb/pkgdb.wsgi`` and
adjust as needed.


Then restart apache and you should be able to access the website on
http://localhost/pkgdb


.. note:: `Flask <http://flask.pocoo.org/>`_ provides also  some documentation
          on how to `deploy Flask application with WSGI and apache
          <http://flask.pocoo.org/docs/deploying/mod_wsgi/>`_.


For testing
-----------

See :doc:`development` if you want to run pkgdb just to test it.

