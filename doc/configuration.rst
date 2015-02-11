Configuration
=============

There are the main configuration options to set to have pkgdb2 running.
These options are all present and described in the pkgdb2.cfg file.


Here are listed some configuration options specific to pkgdb2, but as a
Flask application, you may also use the `Flask configuration options
<http://flask.pocoo.org/docs/config/>`_.


The secret key
---------------

Set in the configuration file under the key ``SECRET_KEY``, this is a unique,
random string which is used by `Flask <http://flask.pocoo.org>`_ to generate
the `CSRF <http://en.wikipedia.org/CSRF>`_ key unique for each user.


You can easily generate one using `pwgen <http://sf.net/projects/pwgen>`_
for example to generate a 50 characters long random key
::

  pwgen 50


The database URL
-----------------

PackageDB uses `SQLAlchemy <http://sqlalchemy.org>`_ has Object Relationship
Mapper and thus to connect to the database. You need to provide under the
key ``DB_URL`` in the configuration file the required information to connect
to the database.


Examples URLs are::

  DB_URL=mysql://user:pass@host/db_name
  DB_URL=postgres://user:pass@host/db_name
  DB_URL=sqlite:////full/path/to/database.sqlite


.. note:: The key ``sqlalchemy.url`` of the ``alembic.ini`` file should
          have the same value as the ``DB_URL`` described here.



The admin group
----------------

PackageDB relies on a group of administrator to create calendar which are then
managed by people from this group. The ``ADMIN_GROUP`` field in the
configuration file refers to the
`FAS <https://admin.fedoraproject.org/accounts>`_ group that manages this
pkgdb2 instance.

**Default:** ``ADMIN_GROUP = ['sysadmin-main', 'sysadmin-cvs']``.


Items per page
--------------

The ``ITEMS_PER_PAGE`` allows setting how many items should be presented per
page. Items in this case may be packages, packagers or collections.

**Default:** ``ITEMS_PER_PAGE = 50``.


Auto-approve ACLs
-----------------

The ``AUTO_APPROVE`` lists the ACLs we handle, there are a couple which
that can be automatically approved when a user requests them.

**Default:** ``AUTO_APPROVE = ['watchcommits', 'watchbugzilla']``.


Caching configuration
---------------------

Pkgdb2 uses `dogplie.cache <https://pypi.python.org/pypi/dogpile.cache>`_
for caching. This caching is used in the extra API endpoints.

There are two configuration keys for this caching system.

``PKGDB2_CACHE_BACKEND`` which specifies which backend to use for the caching

``PKGDB2_CACHE_KWARGS`` which allows passing arguments to this backend

**Default:**

::

    PKGDB2_CACHE_BACKEND = 'dogpile.cache.memcached'
    PKGDB2_CACHE_KWARGS = {
        'arguments': {
            'url': "127.0.0.1:11211",
        }
    }


More information about the possible backends and configurations can be found
in the `dogpile.cache documentation <http://dogpilecache.readthedocs.org/en/latest/>`_.

Bugzilla integration
--------------------

``PKGDB2_BUGZILLA_IN_TESTS`` is used to test the integration of pkgdb2 with
bugzilla in the unit-tests. This setting has no effect with the actual
application, as such there is no point changing it in production.

**Default:** ``PKGDB2_BUGZILLA_IN_TESTS = False``.


``PKGDB2_BUGZILLA_NOTIFICATION`` is used to change the owner of a component
in bugzilla upon changes of the point of contact of a package. If False,
the owner of the component in bugzilla will not reflect the change in the
point of contact in packagedb.
This should set to ``True`` in production.

**Default:** ``PKGDB2_BUGZILLA_NOTIFICATION = False``.


``PKGDB2_BUGZILLA_URL`` is the url to the bugzilla instance the packagedb
application should synchronize with.

**Default:** ``PKGDB2_BUGZILLA_URL = 'https://bugzilla.redhat.com'``.


``PKGDB2_BUGZILLA_USER`` is the bugzilla user the packagedb application can
log in with onto the bugzilla server set.

**Default:** ``PKGDB2_BUGZILLA_USER = None``.


``PKGDB2_BUGZILLA_PASSWORD`` is the password of the bugzilla user the
packagedb application can log in with onto the bugzilla server set.

**Default:** ``PKGDB2_BUGZILLA_PASSWORD = None``.


FAS integration
---------------

PackageDB queries a `FAS <https://fedorahosted.org/fas/>`_ instance to
ensure users asking for ACL on a package are in fact already approved
packagers.


``PKGDB2_FAS_URL`` is the URL to the FAS instance pkgdb2 should query.

**Default:** ``PKGDB2_FAS_URL = None``.


``PKGDB2_FAS_USER`` is the FAS user pkgdb2 can log in with on the FAS server.

**Default:** ``PKGDB2_FAS_USER = None``.


``PKGDB2_FAS_PASSWORD`` is the FAS user password, pkgdb2 can log in with on
the FAS server.

**Default:** ``PKGDB2_FAS_PASSWORD = None``.


PackageDB authenticates its users with a FAS instance through `FedOAuth
<https://github.com/FedOAuth/FedOAuth>`_. To do so it relies on the
``flask-fas-openid`` plugin which can be configured to usea different endpoint,
thus allowing other project to use pkgdb2.

Here below are listed the configuration keys to use to authenticate your users
against another FedOAuth instance than the default one.


``FAS_OPENID_ENDPOINT`` is the URL for the FedOAuth instance.

**Default:** ``FAS_OPENID_ENDPOINT = https://id.fedoraproject.org``


``FAS_OPENID_CHECK_CERT`` is a boolean to specify if FedOAuth will verify SSL
certificates.

**Default:** ``FAS_OPENID_CHECK_CERT = True``


Notification settings
---------------------

``PKGDB2_FEDMSG_NOTIFICATION`` boolean specifying if the pkgdb2 application
should broadcast notifications via `fedmsg <http://www.fedmsg.com/>`_.

**Default:** ``PKGDB2_FEDMSG_NOTIFICATION = True``.


``PKGDB2_EMAIL_NOTIFICATION`` is a boolean specifying if the pkgdb2 application
should send its notificationds by email.

**Default:** ``PKGDB2_EMAIL_NOTIFICATION = False``.


``PKGDB2_EMAIL_TO`` is a template to specify to which email the email
notifications should be set. This implies there are number of aliases set
redirecting from these emails to the users.

**Default:** ``PKGDB2_EMAIL_TO = '{pkg_name}-owner@fedoraproject.org'``.


``PKGDB2_EMAIL_FROM`` specifies the from field used if the notifications are
sent by emails.

**Default:** ``PKGDB2_EMAIL_FROM = 'nobody@fedoraproject.org'``.


``PKGDB2_EMAIL_SMTP_SERVER`` specifies the SMTP server to use to send the
notifications if they are set to be sent by emails.

**Default:** ``PKGDB2_EMAIL_SMTP_SERVER = 'localhost'``.


Email stacktraces
-----------------

PkgDB2 sends email when it faces an exception (trying to add an existing
package or something alike. These emails are sent to the address set
in the configuration key ``MAIL_ADMIN``

**Default:** ``MAIL_ADMIN = '<my personnal email>'``.


Packages not accessible to provenpackagers
------------------------------------------

On Fedora, some packages are restricted to their maintainers only, even members
of the provenpackager group cannot access them (while they can access every
other packages), this mostly when there is trademark regulations involved.

These packages are listed in the configuration under the configuration key
``PKGS_NOT_PROVENPACKAGER``

**Default** ``PKGS_NOT_PROVENPACKAGER = ['firefox', 'thunderbird', 'xulrunner']``.


Security
--------

It is a good practice to have the cookies require a https connection for
security reason. However, while developing this can prevent the authentication
from working. So by default this is turned off to provide an out-of-the-box
working configuration, however you will want to change it in production.

The setting to change is ``SESSION_COOKIE_SECURE``.

**Default** ``SESSION_COOKIE_SECURE =  False``

To change to ``SESSION_COOKIE_SECURE = True``.


Cookie conflicts
----------------

If you run multiple applications at different level of your server, by default
the ``path`` of the cookie will be ``/``, eventually leading to cookie conflict
but providing a working configuration out of the box

To prevent this, adjust the ``APPLICATION_ROOT`` or ``SESSION_COOKIE_NAME`` as
needed (in Fedora we used ``APPLICATION_ROOT``).

**Default** ``APPLICATION_ROOT = '/'``

.. note:: The application root should start with a ``/`` otherwise the ``path``
          of the cookie is not set correctly

.. note:: More configuration information are described in the `flask
          documentation <http://flask.pocoo.org/docs/latest/config/>`_.
