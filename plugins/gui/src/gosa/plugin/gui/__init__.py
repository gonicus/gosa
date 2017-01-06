# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

__import__('pkg_resources').declare_namespace(__name__)

import os

frontend_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..', '..', 'frontend'))