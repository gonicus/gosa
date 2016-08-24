#!/usr/bin/env python
# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import os
import platform
from setuptools import setup, find_packages

try:
    from babel.messages import frontend as babel
except:
    pass

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README')).read()
CHANGES = open(os.path.join(here, 'CHANGES')).read()


common_install_requires = [
    'zope.interface>=3.5',
    'babel',
    'pyOpenSSL',
    'sqlalchemy',
    'lxml',
    'dnspython',
    'cryptography>=1.3',
    ],

setup(
    name = "gosa.common",
    version = "1.0",
    author = "Cajus Pollmeier",
    author_email = "pollmeier@gonicus.de",
    description = "Identity-, system- and configmanagement middleware",
    long_description = README + "\n\n" + CHANGES,
    keywords = "system config management ldap groupware",
    license = "LGPL",
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

    packages = find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages = ['gosa'],

    include_package_data = True,
    package_data = {
        'gosa.common': ['data/stylesheets/*', 'data/events/*'],
    },

    zip_safe = False,

    setup_requires = [
        'pytest-runner',
        'pylint',
        'babel',
        ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'coveralls',
        'python-dbusmock'
    ],
    install_requires = common_install_requires,

    entry_points = """
        [gosa.plugin]
        error = gosa.common.error:GosaErrorHandler

        [gosa.json.datahandler]
        datetime = gosa.common.components.jsonrpc_utils:DateTimeHandler
        date = gosa.common.components.jsonrpc_utils:DateTimeDateHandler
        factory = gosa.common.components.jsonrpc_utils:FactoryHandler
        blob = gosa.common.components.jsonrpc_utils:BinaryHandler
    """,
)
