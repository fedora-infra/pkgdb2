%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from
%distutils.sysconfig import get_python_lib; print (get_python_lib())")}

Name:           pkgdb2
Version:        1.28.1
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
BuildRequires:  python-psutil

# EPEL6
%if ( 0%{?rhel} && 0%{?rhel} == 6 )
BuildRequires:  python-sqlalchemy0.8
Requires:  python-sqlalchemy0.8
%else
BuildRequires:  python-sqlalchemy > 0.8
Requires:  python-sqlalchemy > 0.8
%endif

Requires:  python-alembic
Requires:  python-flask
Requires:  python-flask-wtf
Requires:  python-wtforms
Requires:  python-kitchen
Requires:  python-fedora >= 0.3.32.3-3
Requires:  python-fedora-flask
Requires:  python-docutils
Requires:  python-dateutil
Requires:  python-dogpile-cache
Requires:  python-bugzilla >= 1.1.0
Requires:  python-memcached
Requires:  python-setuptools
Requires:  python-psutil
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

mkdir -p $RPM_BUILD_ROOT/%{_datadir}/pkgdb2

# Install WSGI file
install -m 644 utility/pkgdb2.wsgi $RPM_BUILD_ROOT/%{_datadir}/pkgdb2/pkgdb2.wsgi

# Install the createdb script
install -m 644 createdb.py $RPM_BUILD_ROOT/%{_datadir}/pkgdb2/pkgdb2_createdb.py

# Install the pkgdb2_branch script
install -m 644 utility/pkgdb2_branch.py $RPM_BUILD_ROOT/%{_datadir}/pkgdb2/pkgdb2_branch.py

# Install the set_monitoring_script
install -m 644 utility/set_monitoring_status.py $RPM_BUILD_ROOT/%{_datadir}/pkgdb2/set_monitoring_status.py

# Install the alembic files
cp -r alembic $RPM_BUILD_ROOT/%{_datadir}/pkgdb2/
install -m 644 utility/alembic.ini $RPM_BUILD_ROOT/%{_sysconfdir}/pkgdb2/alembic.ini

## Running the tests would require having flask >= 0.10 which is not present in
## epel6
#%check
#./runtests.sh

%files
%doc README.rst COPYING doc/
%config(noreplace) %{_sysconfdir}/httpd/conf.d/pkgdb2.conf
%config(noreplace) %{_sysconfdir}/pkgdb2/pkgdb2.cfg
%config(noreplace) %{_sysconfdir}/pkgdb2/alembic.ini
%dir %{_sysconfdir}/pkgdb2/
%{_datadir}/pkgdb2/
%{python_sitelib}/pkgdb2/
%{python_sitelib}/%{name}*.egg-info
%{_bindir}/pkgdb2_branch.py
%{_bindir}/update_package_info.py
%{_bindir}/pkgdb-sync-bugzilla


%changelog
* Thu Sep 03 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.28.1-1
- Update to 1.28.1
- Let any packager to change the koschei status of a package in the UI as we do
  in the API
- Let the koschei link point to the wiki page about koschei

* Wed Sep 02 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.28-1
- Update to 1.28
- Add koschei integration

* Tue Aug 18 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.27-1
- Update to 1.27
- Fix integration with anitya to not crash upon receiving invalid data
- Fix the upgrade_pkg_info script to rely on the configuration file

* Fri Jun 05 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.26-1
- Update to 1.26
- Fix a typo in the list_actions template (Ralph Bean)
- Adjust unit-tests to prevent re-running into this bug
- Rework the admin action page (text and options)
- Provide a read-only page showing the admin action details
- Add a link to map a project in anitya if it is not already there
- Improve the logout behavior to avoid looping but still returning to the
  current page where possible
- Rework the monitoring flag to be three states
- Inform about the user's vacation status from fedocal if configured to do so

* Thu May 07 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.25.1-1
- Update 1.25.1
- Enforce the master branch when requesting a new package

* Mon Apr 27 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.25-1
- Update to 1.25
- css fix to make pkgdb2 prettier on high resolution display
- Add fedmenu (Ralph Bean)
- Fix toggling the monitoring flag on a package
- Add a new API endpoint listing the package retired on all active branches of a
  specified collection
- Turn off monitoring when the package is retired on all branches

* Wed Apr 08 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.24.3-1
- Update to 1.24.3
- Fix the pkgdb-sync-bugzilla script to notify the user only once per hour

* Tue Apr 07 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.24.2-1
- Update to 1.24.2
- Fix the pkgdb-sync-bugzilla script to actually CC who it says it is CC'ing

* Tue Mar 31 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.24.1-1
- Update to 1.24.1
- No automatic update of the branch where the user is Approved when editing ACL
  tables
- Fix 'undefined' when clicking monitor toggle (Ricky Elrod)
- Adjust update_package_info for F22, F21 and F19

* Thu Mar 19 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.24-1
- Fix orphaning package having a group as PoC
- Fix excluding provenpackager from some packages specified in the configuration
- Monkey patch flask.jsonify to handle JSONP responses on GET requests (Ralph
  Bean)
- Anitya integration
- Allow package admins to retire a package

* Fri Feb 20 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.23.995-1
- Update to 1.23.995 (pre-release of 1.24)
- Fix the link to `My Requests` on the API documentation page

* Fri Feb 20 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.23.994-1
- Update to 1.23.994 (pre-release of 1.24)
- Do not use insecure connection to pkgdb in set_monitoring_status (Till Maas)
- Add documentation for the API endpoint to set the monitoring status of a
  package
- Replace the monitoring toggle button by one that might be clearer
- Fix actually setting the monitoring flag of new package to True (and adjust
  the tests for this)

* Thu Feb 19 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.23.993-1
- Update to 1.23.993 (pre-release of 1.24)
- Drop the package name from the URL to edit a request (fix few bugs in the
  process)
- If requested is a package admin, request is set to Awaiting Review
- Use secure=True against prod pkgdb in set_monitoring_status.py (Ralph Bean)

* Wed Feb 18 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.23.992-1
- Update to 1.23.992 (pre-release for 1.24)
- Add a `My Request` tab in the main menu
- Adjust copyright year in the master template
- Monitor package set as True by default (Ralph Bean)
- Drop the branch from field when requesting branch for a package
- Add the possibility to Edit one's request directly via the `My Requests` page
- Increase the width of the field in the form to request a new package

* Tue Feb 17 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.23.991-1
- Update to 1.23.991 (pre-release for 1.24)
- Fix documentation to reflect the correct variable name
- Add a link to the request made by someone on the user's page (where all the
  packages of that person are listed)
- Simplify the form to request a package to be added to pkgdb
- Ensure we check that a group is valid before giving it some ACLs
- Make it easier to change one's avatar by simply clicking on it (Ralph Bean)
- Add a placeholder for the Review URL field when requesting a package to be
  added to pkgdb
- When giving watch* ACLs to a FAS user, check that this user exists
- Per FESCo decision, Fedora branch requests will have by default a 7 days
  period during which packager with approveacls will be allowed to grant/deny
  the request, this period does not apply if the requester has approveacls on
  the package

* Mon Jan 26 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.23.99-1
- Update to 1.23.99 (pre-release for 1.24)
- New processes to request a new package or a new branch of a package directly
  in pkgdb instead of relying on bugzilla

* Wed Jan 21 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.23-2
- Test running the unit-tests at build time but doesn't work with EPEL6
- Bump requirement to python-sqlalchemy 0.8+

* Wed Jan 21 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.23-1
- Update to 1.23
- Increase the max width of the page
- Added a public timeline to access the history of the package according to
  pkgdb (button in the package page)

* Tue Jan 13 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.22.2-1
- Update to 1.22.2
- Fix the get_groups query to actually return all the groups in a timely
  manner (Thanks Patrick Uiterwijk)
- Fix the CSS on the blue buttons on the update ACLs page when hovering over
- Add a title to the 'Retired' status to mention they are clickable.

* Mon Jan 12 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.22.1-1
- Update to 1.22.1
- Fix the tooltips on the update ACLs pages
  fixes https://fedorahosted.org/pkgdb2/ticket/37
- Revert the changes made to generate the JSON manually and pull back to
  flask.jsonify() as the JSON we were generated was invalid

* Mon Jan 12 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.22-1
- Update to 1.22
- Add the `set_monitoring_status` utility script (installed on /usr/share/pkgdb2)
- Improve documentation and default files (Thanks Michael Cronenworth)
- Make the project name configuration for example if you want to run pkgdb
  for RPMFusion or another organization (Thanks Michael Cronenworth)
- Optimize the /api/vcs endpoint by generating the JSON output directly
- Optimize the /api/bugzilla endpoint by generating the JSON output directly
- Add a dedicated API endpoint to retrieve the content of the dead.package
  file from cgit
- Retrieve the content of the dead.package file when clicking on 'Retired'
  on the package page

* Fri Nov 21 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.21-1
- Update to 1.21
- DB optimization: do not use LIKE in queries where there is no '%'
- Update the layout of the user list page
- Add flag to set/update the monitoring flag on packages. This flag tells
  the-new-hotness whether the maintainers are interested in getting bugzilla
  tickets about updates available on their package (updates being monitored
  via anitya: release-monitoring.org)
- Clean(er) logic to mark the fields mandatory in the forms
- Fix indentation in the mail_logging module
- Branch orphaned packages as well as we branch for new releases (Subho-bcrec)
- Auto select packagers search in packager details page. (Ratnadeep Debnath)
- Obsolete all ACLs on a package that is retired
- Nicer docstring and API documentation by using textwrap.dedent()
- Add a `former_poc` argument to the orphan API endpoint allowing to restrict
  the orphan to only the package of a certain packager
- Add the former_poc keyword argument to api_acl_reassign, same principle as
  when orphaning a package
- DB optimization: optimize the API endpoint returning the packager's ACLs
- Include the monitoring state in the GET API. (Ralph Bean)
- Include the api_groups and api_monitored in the API documentation
- Update the update_package_info script to include other releases than rawhide

* Sat Nov 08 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.20.1-4
- Backport into 1.20.1 fix to api_acl_reassign from
  https://github.com/fedora-infra/pkgdb2/pull/110

* Fri Nov 07 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.20.1-3
- Fix patch 0001-Fix-the-api-to-orphan-package-of-a-specified-user.patch
  former_poc is single element, not a list

* Fri Nov 07 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.20.1-2
- Backport into 1.20.1 the changes from
  https://github.com/fedora-infra/pkgdb2/pull/109

* Sun Oct 05 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.20.1-1
- Update to 1.20.1
- Better email handler for the logs
- Re-write update_package_info cron script using yum's metadata instead of
  pkgwat

* Thu Oct 02 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.20-1
- Update to 1.20
- Store the list of requirements in the requirements.txt only
  (and the spec file)
- Give an indication that some buttons have a pop-up by adding `...` to their
  title
  https://fedorahosted.org/pkgdb2/ticket/33
- Upon changing the status for the first collection, propagate the change
  to all of them
  https://github.com/fedora-infra/pkgdb2/issues/84
- Include the update_package_info script in the releases and install it in
  the spec file
- Drop commit and approveacl of the person orphaning a package
  https://github.com/fedora-infra/pkgdb2/issues/60
- Add a hover over title to the section's titles to explain to which ACL
  they refer
  https://fedorahosted.org/pkgdb2/ticket/24

* Sat Sep 13 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.19-1
- Update to 1.19
- Publish a fedmsg message when adding a new branch to a package
- Restrict /api/vcs to list only those with commit on active branches
- Do not check if the user is packager when we are removing ACLs
- Update the opensearch xml returned (to prevent FF to associate the Fedora
  keyword to it)
- When listing packages in the API do not set the critpath to False if it is not
  specified
- Include in the /api/vcs output packages that are orphaned but have no
  maintainer left
- Adjust unit-tests accordingly for each of these changes

* Thu Aug 21 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.18.6-1
- Update to 1.18.6
- When branching keep the critpath flag consistent
- Handle the situation where the user tries to update the critpath flag on a
  branch a package does not have
- Add unit-tests for the situtation described above

* Mon Aug 18 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.18.5-1
- Update to 1.18.5
- Fix the pending ACL page to show only the branch where the user has had
  his/her approveacls ACL Approved
- Fix the pkgdb-sync-bugzilla script to work fine and w/o warnings on python 2.6

* Mon Aug 18 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.18.4-1
- Update to 1.18.4
- Fix link to FAS for groups
- Fix the pending ACLs page to show all pending ACL requests for which the user
  has approveacls on the package
- pkgdb-sync-bugzilla is now part of the sources

* Thu Aug 07 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.18.3-1
- Update to 1.18.3
- Fix re-assigning bugs on bugzilla if the new POC is a group
- Use permanent session so that we can time then out via the configuration file

* Wed Aug 06 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.18.2-1
- Update to 1.18.2
- Improve the unit-test suite
- Fix bug that was checking if a collection is `EPEL` instead of `Fedora EPEL`
- Raise exception if someone is trying to orphan/retire a package on a branch
  that this package does not have

* Sat Aug 02 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.18.1-1
- Update to 1.18.1
- Allow user to retire package on collections `Under Development`

* Thu Jul 24 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.18-1
- Update to 1.18
- Add script to sync package summary and description from the packages
  application (that retrieves the information from yum)
- Add new api endpoint /api/groups/ listing all the FAS groups having one
  or more ACLs in the database
- Fix /api/pendingacls to exclude package that are Retired or Orphaned

* Mon Jul 21 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.17-1
- Update to 1.17
- Fix login to account for group maintainership (ask the appropriate group
  upon login)
- Improve unit-tests coverage especially for the group maintainership
- Removed un-used imports
- In /api/bugzilla's json output, not the groups as @group even in the group
  section

* Thu Jul 17 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.16-1
- Update to 1.16
- Add buttons in the pending ACLs page to Approve/Deny all the pending requests
- Add buttons to the matrix management page for the watch* ACLs
- Add the possibility to not include the ACLs in /api/package/<pkgname>

* Tue Jul 15 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.15-1
- Update to 1.15
- Avatar integration (thanks to Ralph Bean)
- Security fix: keep the ADMIN_GROUP stable accross requests
- Update /api/packager/package to support filtering for one or more branches
- pep8 cleanup

* Tue Jul 08 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.14.4-1
- Update to 1.14.4
- Fix pkgdb2.lib.set_acl_package to handle case where pkglisting isn't found

* Tue Jul 08 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.14.3-1
- Update to 1.14.3
- Fix logging/sending email when editing a collection

* Tue Jul 08 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.14.2-1
- Update to 1.14.2
- Ensure the pkgdb2_branch loads the correct version of jinja on EL6

* Tue Jul 08 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.14.1-1
- Update to 1.14.1
- Ensure the pkgdb2_branch loads SQLAchemy >= 0.7

* Tue Jul 08 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.14-1
- Update to 1.14
- Fix the notify API so that people with the watchcommits ACL actually are
  notified of commits
- Improve the pkgdb2.lib.notifications.email_publish method to allow us to
  re-use it elsewhere
- Improve the pkgdb2_branch to send a report once it is performed and to save
  in the DB the new branches as they are created so that in case of problem
  it can be re-started easily.

* Fri Jul 04 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.13.3-1
- Update to 1.13.3
- Restrict the number of groups asked at login

* Thu Jul 03 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.13.2-1
- Update to 1.13.2
- Fix api for orphan/unorphan/retire and reassign as set are not
  serializable to JSON

* Thu Jul 03 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.13.1-1
- Update to 1.13.1
- Fix the /api/package/acl/reassign endpoint so that it supports giving a
  package on more branches than what the package has

* Thu Jul 03 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.13-1
- Update to 1.13
- Allow users to retire package that they did not orphan first
- Enable the sorting of the committers table
- Allow the API to orphan/unorphan/retire a package on multiple branches even if
  the package does not have all of them (the branches)
- Adjust unit-tests so that they behave the same in jenkins and locally
- Add a new API endpoint to update critpath status
- Add a new API endpoint to update the information related to a package (summary
  & co)
- Add a new API endpoint to list the pending ACLs requests
- Add a notification system notify the user if he/she has pending ACLs requests
  right after they log in
- Update the unit-tests so that they only run against faitout on jenkins (by
  checking for the BUILD_ID environment variable)

* Wed Jun 18 2014  Pierre-Yves Chibon <pingou@pingoured.fr> - 1.12.1-1
- Update to 1.12.1
- Fix the back link when listing packages and asked for a page outside the
  range

* Wed Jun 18 2014  Pierre-Yves Chibon <pingou@pingoured.fr> - 1.12-1
- Update to 1.12
- Add anchors to the API documentation
- Fix error in the API documentation
- Handle situation when the user asks for a page outside the allowed range
  (Thanks Cydrobolt!)
- Improve unit-test suit
- Fix the pagination while browsing logs with some filtering criteria
- When searching for a package or a packager if there is only 1 result
  possible redirect the user directly to the corresponding page
- Fix typo in the package's detail page

* Tue Jun 10 2014  Pierre-Yves Chibon <pingou@pingoured.fr> - 1.11.1-1
- Update to 1.11.1
- Fix the search to search all packages by default, including orphaned onces
- Fix bugzilla interaction
- Fix bugzilla notifications to not notify is the bug is assigned to someone
  else or to the new point of contact
- Hide the `Take package` button if the user is not logged in
- Mention /api/version in the API documentation
- Catch problem when interacting with bugzilla
- Fix searching pseudo-user while searching packagers
- Fix display in the package's page

* Wed Jun 04 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.11-1
- Update to 1.11
- DB change to the log table to allow deleting packages
- Add a button to completely delete a package from the database, admins only
- Fix displaying the action buttons on the package's page
- Keep the filtering parameters when browsing multiple pages
- Enhance unit-tests
- Add new api endpoint /api/packager/package/ which lists the packages related
  to the specified packager (just like the packager's page does)

* Fri May 30 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.10.1-1
- Update to 1.10.1
- CSS fixes on the package's page (min resolution: 1024x768)

* Fri May 30 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.10-1
- Update to 1.10
- Search for all packages on /api/packages just like it is in the UI
- Always include `acls` on the package representation even if the list is
  empty
- Redirect the user trying to take a package if no branches are orphaned
- Redirect the user that tries to drop some ACLs if that user does not have
  this acl on this branch or any branch
- Prevent anyone except pkgdb admins to retire a non-orphaned package
- Show packagers that are only watching packages (ie: pseudo-user)
- Fix the admins table in the package's page

* Tue May 27 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.9.2-1
- Update to 1.9.2
- Fix displaying the most recent package in the front page

* Tue May 27 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.9.1-1
- Update to 1.9.1
- Fix displaying the branches in the front page

* Tue May 27 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.9-1
- Update to 1.9
- Fix ordering of the branches in the packager view
- Fix ordering of the branches in the list packages view/search
- When updating multiple ACLs, do not fail the whole transaction if one fails
- Do not show the ``Manage the admins`` button if you are not an admin
- Do not show the ``Request Commit ACLs`` button if you are not logged in
- Split up the approved and pending admins
- Put the most recent packages added on the front page of the application
- Update the status_change field upon entry update
- Ensure there are no: user X change ACL Y from Z to Z
- Remove watchcommits and commit ACL owners from the bugzilla CC list
- Add possibility to see someone's ACL on EOL'd releases
- Adjust the title of the email sent

* Thu May 22 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.8.2-1
- Update to 1.8.2
- Fix redirection if someone calls an opensearch endpoints that does not exist
- Fix the link in the email sent

* Wed May 21 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.8.1-1
- Update 1.8.1
- Fix the reverse proxy

* Wed May 21 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.8-1
- Update to 1.8
- Return the critpath status of a package in a collection in the API
- Drop the version from the front page
- Search all packages by default and set a drop-down list to filter by their
  status
- Fix the https redirection by setting pkgdb2 as a reverse proxied application
- Add browser opensearch extension
- Restrict retiring package from the UI to pkgdb admins
- Do not show the pagination block if there is only one page
  (Thanks to Michael Haynes)
- Improve the subject of the emails sent
- Do not update ACL if the ACL already has this status
- Add link to the package's page at the bottom of the emails sent
- Adjust the label of the 'Manage the committers' per person

* Mon May 19 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.7-1
- Update to 1.7
- Fix the pagination in the log viewer
- Allow to filters the logs per user/packager
- Update the logic for the API/bugzilla endpoint
- Allow admin to retire package on multiple branches
- Only show the branches people are allowed to retire package in in the UI
- Have a pop-up for the main buttons (Watch/Unwatch, Request/Drop) for
  confirmation
- Use forms/POST requests for the main buttons allowing CSRF protection
  fixes https://fedorahosted.org/fedora-infrastructure/ticket/4368
- Only give up commit ACL on branches where the user had them
- Add python-alembic as Requires
- Make sure the page is always greater than 0, otherwise we end up with a
  negative offset

* Fri May 16 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.6-1
- Bump to 1.6
- Layout fixes
- When giving a package only allow existing branches
- Typo in the API doc
- Link to upstream website and the packages application
- Fix the category settings when doing a search
- Default search is '*' (instead of 'a*')
- Rewrite the get_pending_acl and order the results

* Fri May 16 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.5-1
- Bump to 1.5
- Drop the shouldopen field of the Package table
- Fix the message in the logs/emails to say to whom the acl was updated for
- s/poc/point of contact in the logs/emails
- Ensure that page and limit cannot be negative
- Make the 'Give Up Commit Access' link working
- Add alembic to get DB schema change working

* Thu May 15 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.4-1
- Bump to 1.4
- Fix http link when editing ACLs
  https://fedorahosted.org/fedora-infrastructure/ticket/4362
- Fix ordering the branches in the ACL overview and editing page
  https://github.com/fedora-infra/pkgdb2/issues/36
- Speed up Package.search should reflect a bit everywhere including the API
- Enhance the critpath API to allow restricting for only one or more branches
  and let it return only Approved package
- More unit-tests
- Code cleaning

* Wed May 14 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.3-1
- Bump to 1.3
- Add the possibility to Cc one or more email addresses to every emails sent

* Wed May 14 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.2-1
- Bump to 1.2
- Fix the API to return provenpackagers where needed (should allow
  provenpackagers to create update for packages they do not own)
- Few layout bug and typos fixes
- Allow to not check the SSL cert for FAS
- Fix updating ACLs for @kevin
- Add koji_tag and dist_tag to the jsoin output of the Collections
- Let pkgdb admin review ACLs
- Show package status per branch

* Wed May 14 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.1-1
- Bump to 1.1
- Add a critpath filter in the list packages method of the API (for bodhi
  consumption)
- Fix bug in the pending ACLs to return them only on non-EOL collections

* Wed May 14 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 1.0-1
- Bump to release 1.0
- Add helping queries in the upgrade script
- Adjust the forms to show the mandatory fields

* Sat May 03 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.8-1
- Update to 0.8
- Rewrite of the ACL overview page
- Rewrite of the update ACL mechanism
- Fix redirect issue

* Tue Apr 22 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.7-1
- Update to 0.7
- Distinguish the two notify api endpoint
- Add script to do branching in pkgdb2 (from one collection to another)
- Fix the /api/bugzilla json output to be fully backward compatible
- Install that script in /usr/share/pkgdb2

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
