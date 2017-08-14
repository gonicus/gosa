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

try:
    from babel.messages import frontend as babel
except:
    pass

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README')).read()
CHANGES = open(os.path.join(here, 'CHANGES')).read()


setup(
    name = "gosa.dbus",
    version = "1.0",
    author = "GONICUS GmbH",
    author_email = "info@gonicus.de",
    description = "Identity-, system- and configmanagement middleware",
    long_description = README + "\n\n" + CHANGES,
    keywords = "system config management ldap groupware",
    license = "GPL",
    url = "http://www.gosa-project.org",
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

    download_url = "http://oss.gonicus.de/pub/gosa",
    packages = find_packages('src', exclude=['examples', 'tests']),
    package_dir = {'': 'src'},
    namespace_packages = ['gosa'],

    include_package_data = True,
    package_data = {
        'gosa.dbus.plugins.inventory': ['data/fusionToGosa.xsl'],
    },

    setup_requires = [
        'python_dateutil',
        'pytest-runner',
        'dbus-python',
        'pyinotify'
        ],

    install_requires = [
        'gosa.common',
        'setproctitle'
        ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'coveralls'
    ],

    entry_points = """
        [console_scripts]
        gosa-dbus = gosa.dbus.main:main
        notify-user = gosa.dbus.notify:main

        [gosa.dbus.module]
        unix = gosa.dbus.plugins.services.main:DBusUnixServiceHandler
        inventory = gosa.dbus.plugins.inventory.main:DBusInventoryHandler
        service = gosa.dbus.plugins.services.main:DBusUnixServiceHandler
        notify = gosa.dbus.plugins.notify.main:DBusNotifyHandler
        #wol = gosa.dbus.plugins.wakeonlan.main:DBusWakeOnLanHandler
        #shell = gosa.dbus.plugins.shell.main:DBusShellHandler
    """,
)
