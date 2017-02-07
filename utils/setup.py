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

try:
    from babel.messages import frontend as babel
except:
    pass


setup(
    name = "gosa.utils",
    version = "3.0",
    author = "GONICUS GmbH",
    author_email = "info@gonicus.de",
    description = "Identity-, system- and configmanagement middleware",
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
    package_dir = {'': 'src'},
    namespace_packages = ['gosa'],

    include_package_data = False,
    zip_safe = False,

    setup_requires = ['babel', 'pytest-runner', 'hidraw-pure'],
    install_requires = ['gosa.common'],
    tests_require=[
        'pytest',
        'pytest-cov',
        'coveralls'
    ],
    entry_points = """
        [console_scripts]
        acl-admin = gosa.utils.acl_admin:main
        gosa-ldap-monitor = gosa.utils.gosa_ldap_monitor:main
        gosa-plugin-skel = gosa.utils.gosa_plugin_skel:main
        schema2xml = gosa.utils.schema2xml:main
        update-i18n = gosa.utils.update_i18n:main
    """,
)
