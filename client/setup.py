#!/usr/bin/env python
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
README = open(os.path.join(here, 'README')).read()
CHANGES = open(os.path.join(here, 'CHANGES')).read()


client_install_requires = [
    ],


setup(
    name = "gosa.client",
    version = "1.0",
    author = "GONICUS GmbH",
    author_email = "info@gonicus.de",
    description = "Identity-, system- and configmanagement middleware",
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
        'gosa.client': ['data/client.conf', 'data/*.png'],
        'gosa.client.plugins.inventory': ['data/xmlToChecksumXml.xsl'],
    },

    zip_safe = False,

    setup_requires = [
        'pytest-runner',
        'pylint',
        ],
    tests_require = [
        'pytest',
        'pytest-cov',
        'coveralls'
    ],
    install_requires = [
        'gosa.common',
        'netaddr',
        'netifaces',
        'python_dateutil',
        'setproctitle',
        'pycrypto',
        'paho-mqtt'
    ],

    entry_points = """
        [console_scripts]
        gosa-client = gosa.client.main:main
        gosa-join = gosa.client.join:main

        [gosa.client.join.module]
        join.cli = gosa.client.plugins.join.cli:Cli

        [gosa.client.module]
        command = gosa.client.command:ClientCommandRegistry
        mqtt = gosa.client.mqtt:MQTTClientHandler
        mqtt_service = gosa.client.mqtt_service:MQTTClientService
        notify = gosa.client.plugins.notify.main:Notify
        inventory = gosa.client.plugins.inventory.main:Inventory
        service = gosa.client.plugins.dbus.proxy:DBUSProxy
        powermanagement = gosa.client.plugins.powermanagement.main:PowerManagement
        session = gosa.client.plugins.sessions.main:SessionKeeper
    """
)
