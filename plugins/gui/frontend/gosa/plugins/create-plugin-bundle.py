#!/usr/bin/env python2
import sys
import os
import zipfile

app_name = sys.argv[1]
path = sys.argv[2]
archive_path = os.path.join(path, "%s.zip" % app_name)
if os.path.exists(path):
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
        # add scripts
        for root, dirs, files in os.walk(os.path.join(path, 'script')):
            for f in files:
                archive.write(os.path.join(root, f), f)

        # add resources
        for root, dirs, files in os.walk(os.path.join(path, 'resource')):
            for f in files:
                archive.write(os.path.join(root, f), os.path.join(root.replace(path, "", 1), f))

print("%s written" % archive_path)