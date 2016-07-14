#!/usr/bin/env python
import os
import sys

modules = [
  'common',
  'backend',
  'shell'
]
return_code = 0
for module in modules:
    return_code = max(return_code, os.system("cd %s && ./setup.py %s" % (module, " ".join(sys.argv[1:]))) >> 8)

for root, dirs, files in os.walk("plugins"):
    if "setup.py" in files:
        os.system("cd %s && ./setup.py %s" % (root, " ".join(sys.argv[1:])))

sys.exit(return_code)
