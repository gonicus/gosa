# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import json


def dumps(obj):
    return json.dumps(obj, cls=PObjectEncoder)


def loads(json_string):
    return json.loads(json_string, object_hook=PObjectDecoder)


from gosa.common.components.jsonrpc_utils import PObjectEncoder, PObjectDecoder
