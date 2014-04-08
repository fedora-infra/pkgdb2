%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from
%distutils.sysconfig import get_python_lib; print (get_python_lib())")}

Name:           pkgdb2
Version:        0.6
Release:        1%{?dist}
Summary:        The Fedora package database

License:        GPLv2+
URL:            http://fedorahosted.org/pkgdb2/
Source0:        https://fedorahosted.org/releases/p/k/pkgdb2/%{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python2-devel
BuildRequires:  python-flask
BuildRequires:  python-flask-wtf
BuildRequires:  python-wtforms
BuildRequires:  python-kitchen
BuildRequires:  python-fedora >= 0.3.33
BuildRequires:  python-fedora-flask >= 0.3.33
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
install -m 644 utility/pkgdb2.conf $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/pkgdb2.conf

# Install configuration file
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/pkgdb2
install -m 644 utility/pkgdb2.cfg.sample $RPM_BUILD_ROOT/%{_sysconfdir}/pkgdb2/pkgdb2.cfg

# Install WSGI file
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/pkgdb2
install -m 644 utility/pkgdb2.wsgi $RPM_BUILD_ROOT/%{_datadir}/pkgdb2/pkgdb2.wsgi

# Install the createdb script
install -m 644 createdb.py $RPM_BUILD_ROOT/%{_datadir}/pkgdb2/pkgdb2_createdb.py

%files
%doc README.rst COPYING doc/
%config(noreplace) %{_sysconfdir}/httpd/conf.d/pkgdb2.conf
%config(noreplace) %{_sysconfdir}/pkgdb2/pkgdb2.cfg
%dir %{_sysconfdir}/pkgdb2/
%{_datadir}/pkgdb2/
%{python_sitelib}/pkgdb2/
%{python_sitelib}/%{name}*.egg-info

%changelog
* Tue Apr 08 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.6-1
- Update to 0.6
- Update the api endpoint /api/notify to list only people with commit and
  approveacls ACL
- Fix the backward compatibility for this endpoint
- Add api endpoint /api/notify/all to list all people having at least one ACLs
  for each package
- Change the branchname format from F-x to fx
- Getride of the git_branch_name option in the collection table
- Add `eol` argument in the api endpoint /api/vcs use to include as well data
  for eol'd release
- Document the extras api endpoints in the api documentation

* Tue Mar 18 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.5-1
- Update to 0.5
- Add support for the ``poc`` argument in the packager endpoint of the API
- Improved unit-tests
- Make sure the total_page if always returned on all pages that are paginated

* Thu Mar 13 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.4-1
- Update to 0.4
- Add support for the ``eol`` argument in the API, this argument allows
  retrieving information for all collections (including EOL'd ones) in
  the API.

* Thu Mar 13 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.3-1
- Update to 0.3
- The packager API now allows to filter for some ACLs only

* Tue Mar 11 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.2.1-1
- Update to 0.2.1
- Fix documentation for /api/package/

* Tue Mar 11 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.2-1
- Update to 0.2
- Let /api/package/ allow filter for multiple branches

* Wed Nov 27 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.0-1
- Initial packaging work for Fedora
