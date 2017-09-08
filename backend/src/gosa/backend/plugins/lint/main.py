# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import tempfile

import sys
from io import StringIO

import os
import re
from json import loads
import sh
import logging
from pylint.lint import Run
from gosa.backend.objects.comparator import ElementComparator


class ScriptLint(ElementComparator):
    """
    Lints a script depending on the shebang line
    """

    def process(self, all_props, key, value):
        if value is None or len(value) == 0:
            return True, []

        for index, val in enumerate(value):
            shebang = val.split("\n")[0]
            m = re.search("#!\/(usr\/)?bin\/([^\s]+)\s?(.+)?", shebang)
            if m:
                binary = m.group(3) if m.group(2) == "env" else m.group(2)
                if binary[0:6] == "python":
                    version = int(binary[6:]) if len(binary) > 6 else 2
                    linter = PyLint()
                    return linter.process(all_props, key, [val], version=version, idx=index)
                elif binary == "bash":
                    linter = ShellLint()
                    return linter.process(all_props, key, [val], idx=index)
                else:
                    logging.getLogger(__name__).warning("no linter found for %s" % binary)


class ExecLint(ElementComparator):
    """
    Base class for all Linters that need the content to check in a file
    """
    stdout = None
    file = None

    def __init__(self, replace_stdout=False):
        super(ExecLint, self).__init__()
        self.replace_stdout = replace_stdout

    def prepare(self, value):
        # write script to a temporary file
        if value is None or len(value) == 0:
            return None

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(value.encode('utf-8'))
            self.file = f.name

        if self.replace_stdout:
            self.stdout = sys.stdout
            sys.stdout = StringIO()

        return self.file

    def finish(self):
        if self.replace_stdout:
            sys.stdout.close()
            sys.stdout = self.stdout

        os.unlink(self.file)


class PyLint(ExecLint):
    """
    Lints a python string
    """

    def __init__(self):
        super(PyLint, self).__init__(replace_stdout=True)

    def process(self, all_props, key, value, version=2, idx=None):
        errors = []

        for index, val in enumerate(value):
            real_index = idx if idx is not None else index
            file = self.prepare(val)
            if file is None:
                return True, errors

            try:
                r = Run(['--errors-only', file], exit=False)
                test = sys.stdout.getvalue()
                for err in test.split('\n'):
                    #E:  5, 4: Undefined variable 'sdsd' (undefined-variable)
                    m = re.search("[\w]:\s+([\d]+), ([\d]+): ([^(]+)\s*\(?([^)]+)?\)?", err)
                    if m is not None:
                        errors.append({
                            "index": real_index,
                            "translatable": False,
                            "line": int(m.group(1)),
                            "column":int(m.group(2)),
                            "message": "%s (%s)" % (m.group(3), m.group(4)),
                            "symbol": m.group(4)
                        })

            finally:
                self.finish()

        return len(errors) == 0, errors


class ShellLint(ExecLint):
    """
    Lints a python string
    """

    def process(self, all_props, key, value, version=2, idx=None):
        errors = []

        for index, val in enumerate(value):
            real_index = idx if idx is not None else index
            file = self.prepare(val)
            if file is None:
                return True, errors

            buf = StringIO()
            try:
                sh.shellcheck("-f", "json", file, _out=buf)
                return True, errors
            except sh.ErrorReturnCode_1:
                # spellcheck exists with code 1 when the check failed with errors
                res = buf.getvalue()

                if len(res):
                    parsed_errors = loads(res)
                    for err in parsed_errors:
                        current_error = err
                        current_error["index"] = real_index
                        current_error["translatable"] = False
                        errors.append(current_error)

            finally:
                buf.close()
                self.finish()

        return len(errors) == 0, errors