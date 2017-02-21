# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

# Global command types
NORMAL = 1
FIRSTRESULT = 2
CUMULATIVE = 4

no_login_commands = []


def Command(**d_kwargs):
    """
    This is the Command decorator. It adds properties based on its
    parameters to the function attributes::

      >>> @Command(type= NORMAL)
      >>> def hello():
      ...

    =============== ============
    Parameter       Description
    =============== ============
    needsUser       indicates if the decorated function needs a user parameter
    needsSession    indicates if the decorated function needs a session parameter
    noLoginRequired indicates if the decorated command can be called via RPC without being logged in
    type            describes the function type
    =============== ============

    Function types can be:

    * **NORMAL** (default)

      The decorated function will be called as if it is local. Which
      node will answer this request is not important.

    * **FIRSTRESULT**

      Some functionality may be distributed on several nodes with
      several information. FIRSTRESULT iterates thru all nodes which
      provide the decorated function and return on first success.

    * **CUMULATIVE**

      Some functionality may be distributed on several nodes with
      several information. CUMULATIVE iterates thru all nodes which
      provide the decorated function and returns the combined result.
    """
    def decorate(f):
        setattr(f, 'isCommand', True)
        for k in d_kwargs:
            setattr(f, k, d_kwargs[k])
            if k == "noLoginRequired" and d_kwargs[k] is True:
                no_login_commands.append(f.__name__)

        # Tweak docstrings
        doc = getattr(f, '__doc__')
        if doc:
            lines = [x.lstrip(' ') for x in doc.split('\n')]
            name = getattr(f, '__name__')
            try:
                hlp = getattr(f, '__help__')
                setattr(f, '__doc__', ".. command:: backend %s\n\n    %s\n\n.. note::\n    **This method will be exported by the CommandRegistry.**\n\n%s" % (name, hlp, "\n".join(lines)))
            except AttributeError:
                setattr(f, '__doc__', ".. command:: client %s\n\n    %s\n\n..  note::\n    **This method will be exported by the CommandRegistry.**\n\n%s" % (name, "\n%s" % doc, "\n".join(lines)))

        return f

    return decorate


class CommandInvalid(Exception):
    """ Exception which is raised when the command is not valid. """
    pass


class CommandNotAuthorized(Exception):
    """ Exception which is raised when the call was not authorized. """
    pass
