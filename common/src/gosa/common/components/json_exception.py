# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.


class JSONRPCException(Exception):
    """
    Exception raises if there's an error when processing JSONRPC related
    tasks.
    """
    def __init__(self, rpcError):
        super(JSONRPCException, self).__init__(rpcError)
        self.error = rpcError
