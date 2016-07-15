#!/usr/bin/env python3
# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
This is a quick hack. Make me pretty.
"""
import re
import os

#TODO: proper input validation
print("Generate plugin skeleton. Please provide some information:\n")
name = raw_input("Plugin name (must be [a-z][a-z0-9]+): ")
p_type = raw_input("Plugin type (agent, client, dbus): ")
version = raw_input("Version: ")
a_name =  raw_input("Authors name: ")
a_email = raw_input("Authors email: ")

if not re.match(r"^(agent|client|dbus)$", p_type):
    raise ValueError("Invalid type supplied.")
if not re.match(r"^[a-z][a-z0-9]+$", name):
    raise ValueError("Invalid name supplied.")

base_path = os.path.join(name, "src", "gosa", p_type, "plugins", name)
os.makedirs(os.path.join(base_path, "locale"))
os.makedirs(os.path.join(base_path, "tests"))

mod = "%s.module" % p_type
req = "gosa.%s" % p_type
p_clazz = "%sPlugin" % name.lower().capitalize()

#TODO: dbus plugins are different
#TODO: gosa agent handler plugins are different


def main():
    # Write setup.py
    with open(os.path.join(name, "setup.py"), "w") as f:
        f.write("""#!/usr/bin/env python
from setuptools import setup, find_packages
import os
import platform

try:
    from babel.messages import frontend as babel
except:
    pass

setup(
    name = "{name}",
    version = "{version}",
    author = "{a_name}",
    author_email = "{a_email}",
    description = "fill me",
    long_description = "fill me",
    keywords = "fill me",
    license = "GPL",
    url = "http://www.gosa-project.org",
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
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
    package_dir={{'': 'src'}},
    namespace_packages = ['gosa'],

    install_requires = [
        '{req}',
        ],

    entry_points = \"\"\"
        [{mod}]
        plugin.{name} = gosa.{p_type}.plugins.{name}.main:{p_clazz}
    \"\"\",
)
""".format(name=name, p_type=p_type, mod=mod, req=req, a_email=a_email,
    a_name=a_name, p_clazz=p_clazz, version=version))

    # Write config
    with open(os.path.join(name, "setup.cfg"), "w") as f:
        f.write("""[egg_info]
tag_build = dev
tag_date = false
tag_svn_revision = false

[nosetests]
verbose = 1
detailed-errors = 1
with-xunit = 1
with-doctest = 1
doctest-tests = 1
where = gosa
with-nosexunit = 1
source-folder = .
core-target = reports/tests
enable-cover = 1
enable-audit = 1
audit-output = text
audit-target = reports/audit
cover-target = reports/cobertura
cover-clean = 1
cover-collect = 1

[extract_messages]
output_file = {base_path}/locale/messages.pot
copyright_holder = {a_name}
msgid_bugs_address = {a_email}
keywords = _ ngettext:1,2 N_
add_comments = TRANSLATOR:
strip_comments = 1
input_dirs = {base_path}

[init_catalog]
output_dir = {base_path}/locale
input_file = {base_path}/locale/messages.pot

[compile_catalog]
directory = {base_path}/locale

[update_catalog]
output_dir = {base_path}/locale
input_file = {base_path}/locale/messages.pot
""".format(base_path=base_path, a_name=a_name, a_email=a_email))

    # Write __init__ stubs
    for fname in [os.path.join(name, "src", "gosa"),
            os.path.join(name, "src", "gosa", p_type),
            os.path.join(name, "src", "gosa", p_type, "plugins"),
            os.path.join(name, "src", "gosa", p_type, "plugins", name)]:
        with open(os.path.join(fname, "__init__.py"), "w") as f:
            f.write("__import__('pkg_resources').declare_namespace(__name__)\n")

    # Write sample module
    with open(os.path.join(name, "src", "gosa", p_type, "plugins", name, "main.py"), "w") as f:
        f.write("""# -*- coding: utf-8 -*-
import gettext
from gosa.common import Environment
from gosa.common.components import Command, Plugin

# Load gettext
t = gettext.translation('messages', resource_filename("{name}", "locale"), fallback=True)
_ = t.ugettext


class {p_clazz}(Plugin):
    _target_ = '{name}'

    def __init__(self):
        self.env = Environment.getInstance()

    @Command(__help__=N_("Return a pre-defined message to the caller"))
    def hello(self, name="unknown"):
        self.env.log.debug("Now calling 'hello' with parameter %s" % name)
        return _("Hello %s!") % name
""".format(name=name, p_clazz=p_clazz))

    # Write README
    with open(os.path.join(name, "README"), "w") as f:
        f.write("""{p_clazz} README
{line}

This is a GOsa {p_type} plugin. It should be installed using the .egg or
packages.

For development installations, please use:

$ ./setup.py develop

<fill me>

---
{p_name} <{p_email}>
""".format(p_clazz=p_clazz, line="-"*len(p_clazz + " README"), p_email=a_email, p_name=a_name, p_type=p_type))

    print("Done. Please check out the '%s' directory." % name)

if __name__ == '__main__':
    main()
