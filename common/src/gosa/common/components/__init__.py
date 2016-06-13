# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

__import__('pkg_resources').declare_namespace(__name__)
from gosa.common.components.objects import ObjectRegistry
from gosa.common.components.command import Command
from gosa.common.components.command import CommandInvalid
from gosa.common.components.command import CommandNotAuthorized
from gosa.common.components.jsonrpc_proxy import JSONRPCException
from gosa.common.components.jsonrpc_proxy import JSONObjectFactory
from gosa.common.components.jsonrpc_proxy import JSONServiceProxy
from gosa.common.components.plugin import Plugin
from gosa.common.components.registry import PluginRegistry
