#!/usr/bin/env python3
# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import argparse
from json import loads, dumps

import re
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
for path, dirs, files in os.walk("frontend/gosa/build"):
    for f in files:
        data_files.append(os.path.join(path[14:], f))

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
    namespace_packages = ['gosa'],

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
        [gosa.backend.route]
        /widgets/(?P<path>.*)? = gosa.plugins.gui.main:WidgetsProvider
        /(?P<path>.*)? = gosa.plugins.gui.main:GuiPlugin

        [gosa.upload_handler]
        widget = gosa.plugins.gui.upload:WidgetUploadHandler

        [gosa.backend.plugin]
        rpc = gosa.plugins.gui.main:RpcPlugin
    """,
)

return_code = 0

if sys.argv[1] == "test":
    return_code = os.system('cd frontend/gosa && ./node_modules/grunt/bin/grunt')
    os.system('mv ./frontend/gosa/coverage/coveralls.json ../../')

elif sys.argv[1] == "update_catalog":
    # update frontend translation files
    return_code = os.system('cd frontend/gosa && python2 ./generate.py translation')

elif sys.argv[1] == "init_catalog":
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str)
    parser.add_argument('-l', '--locale', dest="locale", type=str)
    args = parser.parse_args()

    # update frontend translation files
    with open(os.path.join("frontend", "gosa", "config.json"), "r") as f:
        content = []
        write = False
        for line in f:
            match = re.search('("LOCALES"\s*:\s*)\[([^\]]+)\]( *, *)', line)
            if match is not None:
                locales = [x.strip('" ') for x in match.group(2).split(",")]
                if args.locale not in locales:
                    locales.append(args.locale)
                    replaced = line.replace(match.group(0), '%s%s%s' % (match.group(1), dumps(locales), match.group(3)))
                    content.append(replaced)
                    write = True
            else:
                content.append(line)
    if write is True:
        with open(os.path.join("frontend", "gosa", "config.json"), "w") as f:
            f.write("".join(content))
        # run the translation step
        return_code = os.system('cd frontend/gosa && python2 ./generate.py translation')

if return_code > 0:
    # exit with error code
    sys.exit(return_code >> 8)