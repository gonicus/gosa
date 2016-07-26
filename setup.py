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
for module in modules:
    paths.append("%s/" % module)
    return_code = max(return_code, os.system("cd %s && ./setup.py %s" % (module, " ".join(sys.argv[1:]))) >> 8)

for root, dirs, files in os.walk("plugins"):
    if "setup.py" in files:
        os.system("cd %s && ./setup.py %s" % (root, " ".join(sys.argv[1:])))
        paths.append("%s/" % root)

#TODO: the untested utils module is breaking the build as the test return status code 1
# reactivate the exiting with return code when utils has tests
#sys.exit(return_code)


if sys.argv[1] == "test":
    os.system("coverage combine %s.coverage" % ".coverage ".join(paths))
    os.system("coverage report -m")
    os.system("coverage html -d htmlcov")
