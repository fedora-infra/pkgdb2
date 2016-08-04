# -*- coding: utf-8 -*-
#
# Copyright © 2013  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
#

'''
pkgdb tests for the Flask API regarding collections.
'''

__requires__ = ['SQLAlchemy >= 0.8']
import pkg_resources

import json
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import pkgdb2
from tests import (Modeltests, create_package_acl, create_package_acl2,
                   create_package_critpath, create_retired_pkgs,
                   create_docker_packages)


def clean_since_pending_acls(data):
    ''' Clean the dates from the pendinacls text output as it will change
    for every run of the tests. '''
    text = []
    for row in data.split('\n'):
        if 'since' in row:
            row = row.rsplit(' ', 2)[0] + ' ...'
        text.append(row)
    data = '\n'.join(text)
    return data


class FlaskApiExtrasTest(Modeltests):
    """ Flask API extras tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskApiExtrasTest, self).setUp()

        pkgdb2.APP.config['TESTING'] = True
        pkgdb2.SESSION = self.session
        pkgdb2.api.extras.SESSION = self.session
        self.app = pkgdb2.APP.test_client()

        # Let's make sure the cache is empty for the tests
        pkgdb2.CACHE.invalidate()

    def test_api_bugzilla_empty(self):
        """ Test the api_bugzilla function with an empty database. """

        # Empty DB
        output = self.app.get('/api/bugzilla/')
        self.assertEqual(output.status_code, 200)

        expected = """# Package Database VCS Acls
# Text Format
# Collection|Package|Description|Owner|Initial QA|Initial CCList
# Backslashes (\) are escaped as \u005c Pipes (|) are escaped as \u007c

"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/bugzilla/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/bugzilla/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        expected = {
            u'bugzillaAcls': {},
            u'title': u'Fedora Package Database -- Bugzilla ACLs'
        }

        self.assertEqual(data, expected)

        output = self.app.get(
            '/api/bugzilla/',
            environ_base={'HTTP_ACCEPT': 'application/json'})
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        self.assertEqual(data, expected)

    def test_api_bugzilla_filled(self):
        """ Test the api_bugzilla function with a filled database. """
        # Fill the DB
        create_package_acl2(self.session)

        output = self.app.get('/api/bugzilla/')
        self.assertEqual(output.status_code, 200)

        expected = """# Package Database VCS Acls
# Text Format
# Collection|Package|Description|Owner|Initial QA|Initial CCList
# Backslashes (\) are escaped as \u005c Pipes (|) are escaped as \u007c

Fedora|fedocal|A web-based calendar for Fedora|pingou||pingou
Fedora|geany|A fast and lightweight IDE using GTK2|group::gtk-sig||
Fedora|guake|Top down terminal for GNOME|pingou||spot"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/bugzilla/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/bugzilla/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            u'bugzillaAcls': {
                'Fedora': {
                    "fedocal": {
                        "owner": "pingou",
                        "cclist": {
                            "groups": [],
                            "people": ["pingou"]
                        },
                        "qacontact": None,
                        "summary": "A web-based calendar for Fedora"
                    },
                    'geany': {
                        'owner': '@gtk-sig',
                        'cclist': {
                            'groups': [],
                            'people': []
                        },
                        'qacontact': None,
                        'summary': 'A fast and lightweight IDE using '
                        'GTK2'
                    },
                    'guake': {
                        'owner': 'pingou',
                        'cclist': {
                            'groups': [],
                            'people': ['spot']
                        },
                        'qacontact': None,
                        'summary': 'Top down terminal for GNOME'
                    }
                }
            },
            'title': 'Fedora Package Database -- Bugzilla ACLs'
        }

        self.assertEqual(data, expected)

        # Filter for a collection
        output = self.app.get('/api/bugzilla/?collection=Fedora EPEL')
        self.assertEqual(output.status_code, 200)

        expected = """# Package Database VCS Acls
# Text Format
# Collection|Package|Description|Owner|Initial QA|Initial CCList
# Backslashes (\) are escaped as \u005c Pipes (|) are escaped as \u007c

"""
        self.assertEqual(output.data, expected)

    def test_api_bugzilla_filled_docker(self):
        """ Test the api_bugzilla function with a filled database with
        namespaces. """
        # Fill the DB
        create_package_acl2(self.session)
        create_docker_packages(self.session)

        output = self.app.get('/api/bugzilla/')
        self.assertEqual(output.status_code, 200)

        expected = """# Package Database VCS Acls
# Text Format
# Collection|Package|Description|Owner|Initial QA|Initial CCList
# Backslashes (\) are escaped as \u005c Pipes (|) are escaped as \u007c

Fedora|fedocal|A web-based calendar for Fedora|pingou||pingou
Fedora|geany|A fast and lightweight IDE using GTK2|group::gtk-sig||
Fedora|guake|Top down terminal for GNOME|pingou||spot
Fedora Docker|cockpit|Server Management GUI|puiterwijk||group::gtk-sig,pingou
Fedora Docker|fedocal|A web-based calendar for Fedora|pingou||spot"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/bugzilla/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/bugzilla/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            u'bugzillaAcls': {
                'Fedora': {
                    "fedocal": {
                        "owner": "pingou",
                        "cclist": {
                            "groups": [],
                            "people": ["pingou"]
                        },
                        "qacontact": None,
                        "summary": "A web-based calendar for Fedora"
                    },
                    'geany': {
                        'owner': '@gtk-sig',
                        'cclist': {
                            'groups': [],
                            'people': []
                        },
                        'qacontact': None,
                        'summary': 'A fast and lightweight IDE using '
                        'GTK2'
                    },
                    'guake': {
                        'owner': 'pingou',
                        'cclist': {
                            'groups': [],
                            'people': ['spot']
                        },
                        'qacontact': None,
                        'summary': 'Top down terminal for GNOME'
                    }
                },
                "Fedora Docker": {
                  "cockpit": {
                    "cclist": {
                      "groups": [
                        "@gtk-sig"
                      ],
                      "people": ["pingou"]
                    },
                    "owner": "puiterwijk",
                    "qacontact": None,
                    "summary": "Server Management GUI"
                  },
                  "fedocal": {
                    "cclist": {
                      "groups": [],
                      "people": [
                        "spot"
                      ]
                    },
                    "owner": "pingou",
                    "qacontact": None,
                    "summary": "A web-based calendar for Fedora"
                  }
                }
            },
            'title': 'Fedora Package Database -- Bugzilla ACLs'
        }
        self.assertEqual(data, expected)

        # Filter for a collection
        output = self.app.get('/api/bugzilla/?collection=Fedora EPEL')
        self.assertEqual(output.status_code, 200)

        expected = """# Package Database VCS Acls
# Text Format
# Collection|Package|Description|Owner|Initial QA|Initial CCList
# Backslashes (\) are escaped as \u005c Pipes (|) are escaped as \u007c

"""
        self.assertEqual(output.data, expected)


    def test_api_notify_empty(self):
        """ Test the api_notify function with an empty database. """

        # Empty DB
        output = self.app.get('/api/notify/')
        self.assertEqual(output.status_code, 200)

        expected = ""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/notify/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/notify/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        expected = {
            u'packages': {},
            u'title': u'Fedora Package Database -- Notification List',
            u'name': None,
            u'version': None,
            u'eol': False
        }

        self.assertEqual(data, expected)

        output = self.app.get(
            '/api/notify/',
            environ_base={'HTTP_ACCEPT': 'application/json'})
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        self.assertEqual(data, expected)

    def test_api_notify_filled(self):
        """ Test the api_notify function with a filled database. """
        # Filled DB
        create_package_acl(self.session)

        output = self.app.get('/api/notify/')
        self.assertEqual(output.status_code, 200)

        expected = """core|josef
geany|group::gtk-sig,josef
guake|pingou
"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/notify/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/notify/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            u'title': u'Fedora Package Database -- Notification List',
            u'packages': {
                'core': [u'josef'],
                'geany': [u'group::gtk-sig', 'josef'],
                'guake': [u'pingou'],
            },
            u'name': None,
            u'version': None,
            u'eol': False
        }
        self.assertEqual(data, expected)

        output = self.app.get('/api/notify/?name=Fedora')
        self.assertEqual(output.status_code, 200)

        expected = """core|josef
geany|group::gtk-sig,josef
guake|pingou
"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/notify/?name=Fedora&version=18')
        self.assertEqual(output.status_code, 200)

        expected = """guake|pingou
"""
        self.assertEqual(output.data, expected)

    def test_api_notify_all_empty(self):
        """ Test the api_notify_all function with an empty database. """

        # Empty DB
        output = self.app.get('/api/notify/all')
        self.assertEqual(output.status_code, 200)

        expected = ""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/notify/all?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/notify/all?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        expected = {
            u'packages': {},
            u'title': u'Fedora Package Database -- Notification List',
            u'name': None,
            u'version': None,
            u'eol': False
        }

        self.assertEqual(data, expected)

        output = self.app.get(
            '/api/notify/all',
            environ_base={'HTTP_ACCEPT': 'application/json'})
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        self.assertEqual(data, expected)

    def test_api_notify_all_filled(self):
        """ Test the api_notify_all function with a filled database. """
        # Filled DB
        create_package_acl(self.session)

        output = self.app.get('/api/notify/all')
        self.assertEqual(output.status_code, 200)

        expected = """core|josef
geany|group::gtk-sig,josef
guake|pingou
"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/notify/all?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/notify/all?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            u'title': u'Fedora Package Database -- Notification List',
            u'packages': {
                'core': [u'josef'],
                'geany': [u'group::gtk-sig', 'josef'],
                'guake': [u'pingou'],
            },
            u'name': None,
            u'version': None,
            u'eol': False
        }
        self.assertEqual(data, expected)

        output = self.app.get('/api/notify/all?name=Fedora')
        self.assertEqual(output.status_code, 200)

        expected = """core|josef
geany|group::gtk-sig,josef
guake|pingou
"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/notify/all?name=Fedora&version=18')
        self.assertEqual(output.status_code, 200)

        expected = """guake|pingou
"""
        self.assertEqual(output.data, expected)

    def test_api_vcs_empty(self):
        """ Test the api_vcs function with an empty database. """

        # Empty DB
        output = self.app.get('/api/vcs/')
        self.assertEqual(output.status_code, 200)

        expected = """# VCS ACLs
# avail|@groups,users|namespace/Package/branch

"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/vcs/?eol=True')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/vcs/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/vcs/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        expected = {
            u'title': u'Fedora Package Database -- VCS ACLs'
        }

        self.assertEqual(data, expected)

        output = self.app.get(
            '/api/vcs/',
            environ_base={'HTTP_ACCEPT': 'application/json'})
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        self.assertEqual(data, expected)

    def test_api_vcs_filled(self):
        """ Test the api_vcs function with a filled database. """
        # Filled DB
        create_package_acl2(self.session)

        output = self.app.get('/api/vcs/')
        self.assertEqual(output.status_code, 200)

        expected = """# VCS ACLs
# avail|@groups,users|namespace/Package/branch

avail | @provenpackager, | modules/core/master
avail | @provenpackager,pingou | rpms/fedocal/f17
avail | @provenpackager,pingou | rpms/fedocal/f18
avail | @provenpackager, | rpms/geany/f18
avail | @provenpackager,@gtk-sig,pingou | rpms/geany/master
avail | @provenpackager,pingou | rpms/guake/f18
avail | @provenpackager,pingou,spot | rpms/guake/master
avail | @provenpackager, | docker/offlineimap/master"""
        self.assertEqual(output.data, expected)

        # Including the EOL'd el4 collection
        expected2 = """# VCS ACLs
# avail|@groups,users|namespace/Package/branch

avail | @provenpackager, | modules/core/master
avail | @provenpackager,pingou | rpms/fedocal/f17
avail | @provenpackager,pingou | rpms/fedocal/f18
avail | @provenpackager, | rpms/geany/f18
avail | @provenpackager,@gtk-sig,pingou | rpms/geany/master
avail | @provenpackager,pingou | rpms/guake/f18
avail | @provenpackager,pingou,spot | rpms/guake/master
avail | @provenpackager, | docker/offlineimap/el4
avail | @provenpackager, | docker/offlineimap/master"""

        output = self.app.get('/api/vcs/?eol=True')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected2)

        # Including only the f17 collection
        expected3 = """# VCS ACLs
# avail|@groups,users|namespace/Package/branch

avail | @provenpackager,pingou | rpms/fedocal/f17"""
        output = self.app.get('/api/vcs/?collection=f17')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected3)

        # Including only the master (rawhide) collection
        expected4 = """# VCS ACLs
# avail|@groups,users|namespace/Package/branch

avail | @provenpackager, | modules/core/master
avail | @provenpackager,@gtk-sig,pingou | rpms/geany/master
avail | @provenpackager,pingou,spot | rpms/guake/master
avail | @provenpackager, | docker/offlineimap/master"""
        output = self.app.get('/api/vcs/?collection=master')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected4)

        output = self.app.get('/api/vcs/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/vcs/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            "rpms": {
                "fedocal": {
                    "f17": {
                        "commit": {
                            "groups": [
                                "provenpackager"
                            ],
                            "people": [
                                "pingou"
                            ]
                        }
                    },
                    "f18": {
                        "commit": {
                            "groups": [
                                "provenpackager"
                            ],
                            "people": [
                                "pingou"
                            ]
                        }
                    }
                },
                "geany": {
                    "f18": {
                        "commit": {
                            "groups": [
                                "provenpackager"
                            ],
                            "people": []
                        }
                    },
                    "master": {
                        "commit": {
                            "groups": [
                                "provenpackager",
                                "gtk-sig"
                            ],
                            "people": [
                                "pingou"
                            ]
                        }
                    }
                },
                "guake": {
                    "f18": {
                        "commit": {
                            "groups": [
                                "provenpackager"
                            ],
                            "people": [
                                "pingou"
                            ]
                        }
                    },
                    "master": {
                        "commit": {
                            "groups": [
                                "provenpackager"
                            ],
                            "people": [
                                "pingou",
                                "spot"
                            ]
                        }
                    }
                },
            },
            "docker": {
                "offlineimap": {
                    "master": {
                        "commit": {
                            "groups": [
                                "provenpackager"
                            ],
                            "people": []
                        }
                    }
                }
            },
            "modules": {
                "core": {
                    "master": {
                        "commit": {
                            "groups": [
                                "provenpackager"
                            ],
                            "people": []
                        }
                    }
                }
            },
            "title": "Fedora Package Database -- VCS ACLs"
        }

        self.assertEqual(data, expected)

    def test_api_critpath_empty(self):
        """ Test the api_critpath function with an empty database. """

        # Empty DB
        output = self.app.get('/api/critpath/')
        self.assertEqual(output.status_code, 200)

        expected = ""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/critpath/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/critpath/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        expected = {"pkgs": {}}

        self.assertEqual(data, expected)

        output = self.app.get(
            '/api/critpath/',
            environ_base={'HTTP_ACCEPT': 'application/json'})
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        self.assertEqual(data, expected)

    def test_api_critpath_filled(self):
        """ Test the api_critpath function with a filled database. """
        # Fill the DB
        create_package_acl(self.session)
        create_package_critpath(self.session)

        output = self.app.get('/api/critpath/')
        self.assertEqual(output.status_code, 200)

        expected = """== master ==
* kernel
== f18 ==
* kernel
"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/critpath/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/critpath/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            u'pkgs': {
                u'f18': [
                    u"kernel"
                ],
                u'master': [
                    u"kernel"
                ]
            },
        }

        self.assertEqual(data, expected)

        output = self.app.get('/api/critpath/?format=json&branches=master')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            u'pkgs': {
                u'master': [
                    u"kernel"
                ]
            },
        }

        self.assertEqual(data, expected)

    def test_api_pendingacls_empty(self):
        """ Test the api_pendingacls function with an empty database. """

        # Empty DB
        output = self.app.get('/api/pendingacls/')
        self.assertEqual(output.status_code, 200)

        expected = "# Number of requests pending: 0"
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/pendingacls/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        expected = {'pending_acls': [], 'total_requests_pending': 0}
        output = self.app.get('/api/pendingacls/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        self.assertEqual(data, expected)

        output = self.app.get(
            '/api/pendingacls/',
            environ_base={'HTTP_ACCEPT': 'application/json'})
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        self.assertEqual(data, expected)

    def test_api_pendingacls_filled(self):
        """ Test the api_pendingacls function with a filled database. """
        # Fill the DB
        create_package_acl(self.session)
        create_package_critpath(self.session)

        output = self.app.get('/api/pendingacls/')
        self.assertEqual(output.status_code, 200)

        expected = """# Number of requests pending: 2
guake:master has ralph waiting for approveacls since ...
guake:master has toshio waiting for commit since ..."""
        data = clean_since_pending_acls(output.data)
        self.assertEqual(data, expected)

        output = self.app.get('/api/pendingacls/?format=random')
        self.assertEqual(output.status_code, 200)
        data = clean_since_pending_acls(output.data)
        self.assertEqual(data, expected)

        output = self.app.get('/api/pendingacls/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        for req in data['pending_acls']:
            req['since'] = '2015-02-10 15:04:36'

        expected = {
            'pending_acls': [
                {
                    'acl': 'approveacls',
                    'collection': 'master',
                    'namespace': 'rpms',
                    'package': 'guake',
                    'since': '2015-02-10 15:04:36',
                    'status': 'Awaiting Review',
                    'user': 'ralph'
                },
                {
                    'acl': 'commit',
                    'collection': 'master',
                    'namespace': 'rpms',
                    'package': 'guake',
                    'since': '2015-02-10 15:04:36',
                    'status': 'Awaiting Review',
                    'user': 'toshio'
                }
            ],
            'total_requests_pending': 2
        }

        self.assertEqual(data, expected)

        output = self.app.get('/api/pendingacls/?format=json&username=pingou')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        for req in data['pending_acls']:
            req['since'] = '2015-02-10 15:04:36'

        self.assertEqual(data, expected)

        output = self.app.get('/api/pendingacls/?format=json&username=toshio')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        expected = {'pending_acls': [], 'total_requests_pending': 0}

        self.assertEqual(data, expected)

    def test_api_groups_empty(self):
        """ Test the api_groups function with an empty database. """

        output = self.app.get('/api/groups/')
        self.assertEqual(output.status_code, 200)

        expected = "# Number of groups: 0"
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/groups/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/groups/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            'groups': [],
            'total_groups': 0
        }

        self.assertEqual(data, expected)

    def test_api_groups_filled(self):
        """ Test the api_groups function with a filled database. """
        # Fill the DB
        create_package_acl(self.session)
        create_package_critpath(self.session)

        output = self.app.get('/api/groups/')
        self.assertEqual(output.status_code, 200)

        expected = """# Number of groups: 2
gtk-sig
kernel-maint"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/groups/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/groups/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            'groups': [
                'gtk-sig',
                'kernel-maint',
            ],
            'total_groups': 2
        }

        self.assertEqual(data, expected)

        output = self.app.get(
            '/api/groups/',
            environ_base={'HTTP_ACCEPT': 'application/json'})
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        self.assertEqual(data, expected)

    def test_api_monitored_empty(self):
        """ Test the api_monitored function with an empty database. """

        output = self.app.get('/api/monitored/')
        self.assertEqual(output.status_code, 200)

        expected = "# Number of packages: 0"
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/monitored/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/monitored/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            'packages': [
            ],
            'total_packages': 0
        }

        self.assertEqual(data, expected)

        output = self.app.get(
            '/api/monitored/',
            environ_base={'HTTP_ACCEPT': 'application/json'})
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        self.assertEqual(data, expected)

    def test_api_monitored_filled(self):
        """ Test the api_monitored function with a filled database. """
        create_package_acl(self.session)
        create_package_critpath(self.session)

        output = self.app.get('/api/monitored/')
        self.assertEqual(output.status_code, 200)

        expected = "# Number of packages: 1\nkernel"
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/monitored/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/monitored/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            "total_packages": 1,
            "packages": [
                "kernel",
            ],
        }


        self.assertEqual(data, expected)

        output = self.app.get(
            '/api/monitored/',
            environ_base={'HTTP_ACCEPT': 'application/json'})
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        self.assertEqual(data, expected)

    def test_api_retired_empty(self):
        """ Test the api_retired function with an empty database. """

        output = self.app.get('/api/retired/')
        self.assertEqual(output.status_code, 200)

        expected = "# Number of packages: 0\n# collection: Fedora"
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/retired/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/retired/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            'collection': 'Fedora',
            'packages': [
            ],
            'total_packages': 0
        }

        self.assertDictEqual(data, expected)

        output = self.app.get(
            '/api/retired/',
            environ_base={'HTTP_ACCEPT': 'application/json'})
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        self.assertEqual(data, expected)

    def test_api_retired_filled(self):
        """ Test the api_retired function with a filled database. """
        create_retired_pkgs(self.session)

        output = self.app.get('/api/retired/')
        self.assertEqual(output.status_code, 200)

        expected = "# Number of packages: 1\n# collection: Fedora\nfedocal"
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/retired/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/retired/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            'collection': 'Fedora',
            "total_packages": 1,
            "packages": [
                "fedocal",
            ],
        }

        self.assertDictEqual(data, expected)

        output = self.app.get(
            '/api/retired/',
            environ_base={'HTTP_ACCEPT': 'application/json'})
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        self.assertEqual(data, expected)

        output = self.app.get('/api/retired/?collection=Fedora EPEL')
        self.assertEqual(output.status_code, 200)

        expected = "# Number of packages: 1\n"\
        "# collection: Fedora EPEL\nguake"
        self.assertEqual(output.data, expected)


    def test_api_koschei_empty(self):
        """ Test the api_koschei function with an empty database. """

        output = self.app.get('/api/koschei/')
        self.assertEqual(output.status_code, 200)

        expected = "# Number of packages: 0"
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/koschei/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/koschei/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            'packages': [
            ],
            'total_packages': 0
        }

        self.assertEqual(data, expected)

        output = self.app.get(
            '/api/koschei/',
            environ_base={'HTTP_ACCEPT': 'application/json'})
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        self.assertEqual(data, expected)

    def test_api_koschei_filled(self):
        """ Test the api_koschei function with a filled database. """
        create_package_acl(self.session)
        create_package_critpath(self.session)

        output = self.app.get('/api/koschei/')
        self.assertEqual(output.status_code, 200)

        expected = "# Number of packages: 1\nkernel"
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/koschei/?format=random')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/koschei/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            "total_packages": 1,
            "packages": [
                "kernel",
            ],
        }


        self.assertEqual(data, expected)

        output = self.app.get(
            '/api/koschei/',
            environ_base={'HTTP_ACCEPT': 'application/json'})
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        self.assertEqual(data, expected)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskApiExtrasTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
