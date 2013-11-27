%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from
%distutils.sysconfig import get_python_lib; print (get_python_lib())")}

Name:           packagedb
Version:        0.1.0
Release:        1%{?dist}
Summary:        The Fedora package database

License:        GPLv2+
URL:            http://fedorahosted.org/packagedb/
Source0:        https://fedorahosted.org/releases/p/a/packagedb/%{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python2-devel
BuildRequires:  python-flask
BuildRequires:  python-flask-wtf
BuildRequires:  python-wtforms
BuildRequires:  python-kitchen
BuildRequires:  python-fedora >= 0.3.32.3-3
BuildRequires:  python-fedora-flask
BuildRequires:  python-openid-teams
BuildRequires:  python-openid-cla
BuildRequires:  python-docutils
BuildRequires:  python-dateutil
BuildRequires:  python-dogpile-cache
BuildRequires:  python-mock
BuildRequires:  python-bugzilla
BuildRequires:  python-memcached
BuildRequires:  python-setuptools
BuildRequires:  python-blinker

# EPEL6
%if ( 0%{?rhel} && 0%{?rhel} == 6 )
BuildRequires:  python-sqlalchemy0.7
Requires:  python-sqlalchemy0.7
%else
BuildRequires:  python-sqlalchemy > 0.5
Requires:  python-sqlalchemy > 0.5
%endif

Requires:  python-flask
Requires:  python-flask-wtf
Requires:  python-wtforms
Requires:  python-kitchen
Requires:  python-fedora >= 0.3.32.3-3
Requires:  python-fedora-flask
Requires:  python-docutils
Requires:  python-dateutil
Requires:  python-dogpile-cache
Requires:  python-bugzilla
Requires:  python-memcached
Requires:  python-setuptools
Requires:  mod_wsgi

%description
PackageDB is the package database for Fedora. It is the application handling who
is allowed to commit on the git of the Fedora packages, it also handles who is
the person getting the bugs on the Bugzilla and who get the notifications
for changes in the git, builds or bugs.

%prep
%setup -q

%build
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# Install apache configuration file
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/
install -m 644 utility/pkgdb.conf $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/pkgdb.conf

# Install configuration file
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/pkgdb
install -m 644 utility/pkgdb.cfg.sample $RPM_BUILD_ROOT/%{_sysconfdir}/pkgdb/pkgdb.cfg

# Install WSGI file
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/pkgdb
install -m 644 utility/pkgdb.wsgi $RPM_BUILD_ROOT/%{_datadir}/pkgdb/pkgdb.wsgi

# Install the createdb script
install -m 644 createdb.py $RPM_BUILD_ROOT/%{_datadir}/pkgdb/pkgdb_createdb.py

%files
%doc README.rst COPYING doc/
%config(noreplace) %{_sysconfdir}/httpd/conf.d/pkgdb.conf
%config(noreplace) %{_sysconfdir}/pkgdb/pkgdb.cfg
%dir %{_sysconfdir}/pkgdb/
%{_datadir}/pkgdb/
%{python_sitelib}/pkgdb/
%{python_sitelib}/%{name}*.egg-info

%changelog
* Wed Nov 27 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.0-1
- Initial packaging work for Fedora
