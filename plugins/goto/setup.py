#!/usr/bin/env python3
# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from setuptools import setup, find_packages
import os
import platform

try:
    from babel.messages import frontend as babel
except:
    pass

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES')).read()

data_files = []
for path, dirs, files in os.walk("src/gosa/plugins/goto/data"):
    for f in files:
        data_files.append(os.path.join(path[14:], f))

setup(
    name = "gosa.plugins.goto",
    version = "3.0",
    author = "GONICUS GmbH",
    author_email = "info@gonicus.de",
    description = "GOsa client integration",
    long_description = README + "\n\n" + CHANGES,
    keywords = "system config management ldap groupware",
    license = "GPL",
    url = "http://gosa-project.org",
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: Systems Administration :: Authentication/Directory',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Monitoring',
    ],

    packages = find_packages('src', exclude=['examples', 'tests']),
    package_dir={'': 'src'},
    namespace_packages = ['gosa'],

    include_package_data = True,
    package_data = {
        'gosa.plugins.goto': data_files
    },

    zip_safe = False,

    setup_requires = [
        'pytest-runner',
        'pylint',
        ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'coveralls',
        'tornado'
    ],
    install_requires = [
        'gosa.backend',
        'netaddr',
        'dnspython3'
        ],

    entry_points = """
        [gosa.plugin]
        goto.network = gosa.plugins.goto.network:NetworkUtils
        goto.client_service = gosa.plugins.goto.client_service:ClientService

        [gosa.object.filter]
        registereddevicestatusin = gosa.plugins.goto.in_out_filters:registeredDeviceStatusIn
        registereddevicestatusout = gosa.plugins.goto.in_out_filters:registeredDeviceStatusOut
    """,
)
