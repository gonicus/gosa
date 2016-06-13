#!/usr/bin/env python
import os
import sys

modules = [
  'common',
  'backend',
]

for module in modules:
    os.system("cd %s && ./setup.py %s" % (module, " ".join(sys.argv[1:])))

for root, dirs, files in os.walk("plugins"):
    if "setup.py" in files:
        os.system("cd %s && ./setup.py %s" % (root, " ".join(sys.argv[1:])))
