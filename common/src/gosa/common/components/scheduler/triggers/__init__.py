# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
__import__('pkg_resources').declare_namespace(__name__)

from gosa.common.components.scheduler.triggers.cron import CronTrigger
from gosa.common.components.scheduler.triggers.interval import IntervalTrigger
from gosa.common.components.scheduler.triggers.simple import SimpleTrigger
