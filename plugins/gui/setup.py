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
import sys

try:
    from babel.messages import frontend as babel
except:
    pass

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES')).read()

data_files = []

# noinspection PyRedeclaration
for path, dirs, files in os.walk("src/gosa/plugins/gui/data"):
    for f in files:
        data_files.append(os.path.join(path[21:], f))

setup(
    name = "gosa-plugin-gui",
    version = "3.0",
    author = "GONICUS GmbH",
    author_email = "info@gonicus.de",
    description = "GUI for GOsa",
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
    namespace_packages = ['gosa.plugins.gui'],

    include_package_data = True,
    package_data = {
        'gosa.plugins.gui': data_files
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
        ],

    entry_points = """
        [gosa.route]
        /(?P<path>.*)? = gosa.plugins.gui.main:GuiPlugin

        [gosa.upload_handler]
        widget = gosa.plugins.gui.upload:WidgetUploadHandler

        [gosa.plugin]
        rpc = gosa.plugins.gui.main:RpcPlugin
    """,
)

if sys.argv[1] == "test":
    return_code = os.system('cd frontend/gosa && ./node_modules/grunt/bin/grunt')
    os.system('mv ./frontend/gosa/coverage/coveralls.json ../../')
    if return_code > 0:
        # exit with error code
        sys.exit(return_code >> 8)
