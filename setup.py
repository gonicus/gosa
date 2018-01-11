#!/usr/bin/env python3
import os
import sys

modules = [
  'common',
  'backend',
  'client',
  'dbus',
  'shell',
  'utils',
  'proxy'
]
paths = []
return_code = 0
skip_tests = ["client", "proxy"]
skip_return_code = ["dbus", "goto", "gui"]

failed_modules = {}

task = sys.argv[1]
testing = task == "test"

# fix for multiple addopts parameters
for idx, arg in enumerate(sys.argv):
    if arg.startswith("--addopts"):
        sys.argv[idx] = '--addopts="%s"' % arg.split("=")[1]

for module in modules:
    if testing and module in skip_tests:
        continue
    paths.append("%s/" % module)
    module_return_code = os.system("cd %s && ./setup.py %s" % (module, " ".join(sys.argv[1:])))
    if module not in skip_return_code:
        return_code = max(return_code, module_return_code >> 8)
    if module_return_code > 0:
        failed_modules[module] = {
            "code": module_return_code,
            "type": "module"
        }
    print("%s returned %s (ignored: %s): %s" % (module, module_return_code, module in skip_return_code, return_code))

for root, dirs, files in os.walk("plugins"):
    if "setup.py" in files:
        plugin = root.split(os.path.sep)[-1:][0]
        if testing and plugin in skip_tests:
            continue
        plugin_return_code = os.system("cd %s && ./setup.py %s" % (root, " ".join(sys.argv[1:])))
        paths.append("%s/" % root)
        if plugin not in skip_return_code:
            return_code = max(return_code, plugin_return_code >> 8)
        if plugin_return_code > 0:
            failed_modules[plugin] = {
                "code": plugin_return_code,
                "type": "plugin"
            }
        print("%s returned %s (ignored: %s): %s" % (plugin, plugin_return_code, plugin in skip_return_code, return_code))

if testing:  # and return_code == 0:
    # check if coverage exists for path
    paths = [x for x in paths if os.path.exists("%s.coverage" % x)]
    os.system("coverage combine %s.coverage" % ".coverage ".join(paths))
    os.system("coverage report -m")
    os.system("coverage html -d htmlcov")

if return_code == 0:
    print(task + " run successful")
else:
    print(task + " run failed with error code " + str(return_code))
    print("Failed parts:")
    for name in failed_modules:
        print("  >>> %s '%s' failed with error code %s" % (failed_modules[name]['type'], name, str(failed_modules[name]['code'])))
sys.exit(return_code)
