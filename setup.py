#!/usr/bin/env python

"""
Setup script
"""

# Required to build on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

from setuptools import setup
from pkgdb2 import __version__


def get_requirements(requirements_file='requirements.txt'):
    """Get the contents of a file listing the requirements.

    :arg requirements_file: path to a requirements file
    :type requirements_file: string
    :returns: the list of requirements, or an empty list if
              `requirements_file` could not be opened or read
    :return type: list
    """

    lines = open(requirements_file).readlines()
    return [
        line.rstrip().split('#')[0]
        for line in lines
        if not line.startswith('#')
    ]


setup(
    name='pkgdb2',
    description='Pkgdb2 is the newest Package database for Fedora.',
    version=__version__,
    author='Pierre-Yves Chibon',
    author_email='pingou@pingoured.fr',
    maintainer='Pierre-Yves Chibon',
    maintainer_email='pingou@pingoured.fr',
    license='GPLv3+',
    download_url='https://fedorahosted.org/releases/p/k/pkgdb2/',
    url='https://fedorahosted.org/pkgdb2/',
    packages=['pkgdb2'],
    include_package_data=True,
    install_requires=get_requirements(),
    scripts=[
        'utility/pkgdb2_branch.py',
        'utility/pkgdb-sync-bugzilla',
        'utility/update_package_info.py',
    ],
)
