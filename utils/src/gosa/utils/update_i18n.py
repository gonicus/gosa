#!/usr/bin/env python3
# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import os
import sys
import subprocess


def update(path):
    basename = os.path.splitext(os.path.basename(path))[0]

    # Find existing translations
    tspath = os.path.join(os.path.dirname(path), "i18n")
    for dirpath, dirnames, filenames in os.walk(tspath):
        for filename in filenames:
            if filename.startswith(basename + "_") and filename.endswith(".ts"):
                ret = subprocess.call(["lupdate", path, "-silent", "-ts", os.path.join(dirpath, filename)])
                if ret:
                    print("! Failed to update locales for %s" % path)
                else:
                    print("Processed %s" % path)

def main():
    # Check for optional parameters
    args = sys.argv[1:]

    if not args:
        args.append(os.getcwd())

    # Loop thru sources and call lupdate
    for arg in args:

        if arg.endswith(".ui"):
            update(arg)

        else:
            for dirpath, dirnames, filenames in os.walk(arg):
                for filename in [fn for fn in filenames if fn.endswith(".ui")]:
                    update(os.path.join(dirpath, filename))


if __name__ == "__main__":
    main()
