#!/usr/bin/env python
import os
import sys

modules = [
  'common',
  'backend',
  'client',
  'shell',
  'utils',
]
paths = []
return_code = 0

# fix for multiple addopts parameters
for idx, arg in enumerate(sys.argv):
    if arg.startswith("--addopts"):
        sys.argv[idx] = '--addopts="%s"' % arg.split("=")[1]

for module in modules:
    paths.append("%s/" % module)
    return_code = max(return_code, os.system("cd %s && ./setup.py %s" % (module, " ".join(sys.argv[1:]))) >> 8)

for root, dirs, files in os.walk("plugins"):
    if "setup.py" in files:
        os.system("cd %s && ./setup.py %s" % (root, " ".join(sys.argv[1:])))
        paths.append("%s/" % root)

if sys.argv[1] == "test" and return_code == 0:
    os.system("coverage combine %s.coverage" % ".coverage ".join(paths))
    os.system("coverage report -m")
    os.system("coverage html -d htmlcov")

sys.exit(return_code)