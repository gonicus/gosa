#!/usr/bin/env python3
import os

plugin_name = input("Plugin Name: ")
author_name = input("Author Name: ")
author_email = input("Author Email: ")

# copy files + replace content
name_lower = plugin_name.lower()
os.mkdir(name_lower)
for root, dirs, files in os.walk('_template'):
    for file in files:
        with open(os.path.join(root, file), 'r') as f:
            print(root)
            print(file)
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

print("%s plugin has been created." % plugin_name)
