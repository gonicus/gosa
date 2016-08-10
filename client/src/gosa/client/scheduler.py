# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from gosa.common.components.scheduler import Scheduler
import logging
from zope.interface import implementer
from gosa.common.components.scheduler.jobstores.ram_store import RAMJobStore
from gosa.common.handler import IInterfaceHandler
from gosa.common import Environment


@implementer(IInterfaceHandler)
class SchedulerService(object):
    _priority_ = 0

    def __init__(self):
        env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.debug("initializing scheduler service")
        self.env = env
        self.sched = Scheduler()
        self.sched.daemonic = True
        self.sched.add_jobstore(RAMJobStore(), 'ram', True)

    def serve(self):
        self.sched.start()

    def stop(self):
        self.sched.shutdown()

    def get_scheduler(self):
        return self.sched
