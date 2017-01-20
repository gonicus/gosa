#!/usr/bin/env python2
import subprocess
import sys
import os
import stat
from zipfile import ZipFile, ZIP_DEFLATED

job = sys.argv[1]


def build():
    for file in os.listdir("."):
        if os.path.isdir(file) and not file.startswith("_template"):
            # generate plugin
            subprocess.call("cd %s && ./generate.py build" % file, shell=True)


def deploy():
    for file in os.listdir("."):
        if os.path.isdir(file) and not file.startswith("_template"):
            # find zipfile
            for subfile in os.listdir(os.path.join(file, "build")):
                if subfile.endswith(".zip"):
                    with ZipFile(os.path.join(file, "build", subfile), 'r') as zip:
                        if zip.testzip():
                            print("bad widget zip")
                            return
                        # extract filename from zip
                        zip.extractall(os.path.join("..", "uploads", "widgets"))


def create_plugin():

    plugin_name = input("Plugin Name: ")
    author_name = input("Author Name: ")
    author_email = input("Author Email: ")

    # copy files + replace content
    name_lower = plugin_name.lower()
    os.mkdir(name_lower)
    for root, dirs, files in os.walk('_template'):
        for file in files:
            with open(os.path.join(root, file), 'r') as f:
                content = f.read()
                content = content.replace("###NAME###", plugin_name)
                content = content.replace("###NAME_LOWER###", name_lower)
                content = content.replace("###AUTHOR###", author_name)
                content = content.replace("###EMAIL###", author_email)

                # write
                target_path = root.replace("###NAME_LOWER###", name_lower).replace("_template", name_lower)
                if not os.path.exists(target_path):
                    os.makedirs(target_path)

                with open(os.path.join(target_path, file), 'w') as wf:
                    wf.write(content)

    # make generate.py executable
    os.chmod(os.path.join(name_lower, "generate.py"), stat.S_IRWXU | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
    print("%s plugin has been created." % plugin_name)


def make_plugin_bundle():
    app_name = sys.argv[2]
    path = sys.argv[3]
    archive_path = os.path.join(path, "%s.zip" % app_name)
    if os.path.exists(path):
        with ZipFile(archive_path, 'w', ZIP_DEFLATED) as archive:
            # add manifest
            archive.write(os.path.join(path, "..", "Manifest.json"), os.path.join(app_name, "Manifest.json"))

            # add scripts
            for root, dirs, files in os.walk(os.path.join(path, 'script')):
                for f in files:
                    archive.write(os.path.join(root, f), os.path.join(app_name, f))

            # add resources
            for root, dirs, files in os.walk(os.path.join(path, 'resource')):
                for f in files:
                    archive.write(os.path.join(root, f), os.path.join(root.replace(path, app_name, 1), f))

    print("%s written" % archive_path)

if job == "build":
    build()
elif job == "deploy":
    build()
    deploy()
elif job == "create-plugin":
    create_plugin()
elif job == "bundle-plugin":
    make_plugin_bundle()
else:
    print("Unknown job: %s" % job)