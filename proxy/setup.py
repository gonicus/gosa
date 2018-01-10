#!/usr/bin/env python3
# This file is part of the GOsa framework.
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
with open(os.path.join(here, 'README')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES')) as f:
    CHANGES = f.read()

setup(
    name="gosa.proxy",
    version="1.0",
    author="GONICUS GmbH",
    author_email="info@gonicus.de",
    description="Identity-, system- and configmanagement middleware",
    long_description=README + "\n\n" + CHANGES,
    keywords="system config management ldap groupware",
    license="GPL",
    url="http://gosa-project.org",
    classifiers=[
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

    packages=find_packages('src', exclude=['examples', 'tests']),
    package_dir={'': 'src'},
    namespace_packages=['gosa'],

    include_package_data=True,
    package_data={
        'gosa.proxy': ['data/proxy.conf']
    },

    zip_safe=False,

    setup_requires=[
        'pytest-runner',
        'pylint',
        ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'coveralls'
    ],
    install_requires=[
        'gosa.common',
        'setproctitle',
        'paho-mqtt'
    ],

    entry_points="""
        [console_scripts]
        gosa-proxy=gosa.proxy.main:main

        [gosa.proxy.plugin]
        mqtt = gosa.common.mqtt:MQTTClientHandler
    """
)
