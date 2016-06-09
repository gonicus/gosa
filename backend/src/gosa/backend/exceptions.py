# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.


class ACLException(Exception):
    pass


class CommandInvalid(Exception):
    """ Exception which is raised when the command is not valid. """
    pass


class CommandNotAuthorized(Exception):
    """ Exception which is raised when the call was not authorized. """
    pass


class HTTPException(Exception):
    pass


class LDAPException(Exception):
    pass


class LockError(Exception):
    pass


class ConversationNotSupported(Exception):
    pass


class FilterException(Exception):
    pass


class IndexException(Exception):
    pass


class FactoryException(Exception):
    pass


class ProxyException(Exception):
    pass


class ObjectException(Exception):
    pass


class ElementFilterException(Exception):
    pass


class EntryNotUnique(Exception):
    pass


class EntryNotFound(Exception):
    pass


class DNGeneratorError(Exception):
    """
    Exception thrown for dn generation errors
    """
    pass


class RDNNotSpecified(Exception):
    """
    Exception thrown for missing rdn property in object definitions
    """
    pass


class BackendError(Exception):
    """
    Exception thrown for unknown objects
    """
    pass


class ProxyError(Exception):
    pass
