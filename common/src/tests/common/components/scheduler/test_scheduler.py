#!/usr/bin/python3
# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
import pytest
import threading
import os
from io import StringIO
from gosa.common.components.scheduler.scheduler import *
from gosa.common.components.scheduler.events import *
from gosa.common.components.scheduler.jobstores.ram_store import *
from tests.helper import slow


class CallHandler:
    def __init__(self):
        self.lock = threading.Lock()
        self.i = 0
    def count(self):
        self.lock.acquire()
        self.i += 1
        self.lock.release()
    def get_count(self):
        return self.i
def process(handler):
    handler.count()

class SchedulerTestCase(unittest.TestCase):
    def test_SchedulerAlreadyRunningError(self):
        err = SchedulerAlreadyRunningError()
        self.assertEqual(str(err), 'Scheduler is already running')

    def test_configure(self):
        s = Scheduler()
        s.shutdown() # Does nothing
        s.start()
        with pytest.raises(SchedulerAlreadyRunningError):
            s.start()
        with pytest.raises(SchedulerAlreadyRunningError):
            s.configure()
        s.shutdown()
        
    def test_add_job(self):
        # Adding jobs before and after start()
        def dummy(): pass
        s = Scheduler()
        s.add_jobstore(RAMJobStore(), "default")
        with StringIO("") as buf:
            s.print_jobs(out=buf)
            assert buf.getvalue() == os.linesep.join("""Jobstore default:
    No scheduled jobs""".splitlines())+os.linesep
        trigger = SimpleTrigger("2016-12-12")
        j1 = s.add_job(trigger, dummy, (), {})
        assert isinstance(j1, Job)
        s.start()
        j2 = s.add_job(trigger, dummy, (), {})
        assert isinstance(j2, Job)
        assert len(s.get_jobs()) == 2
        with StringIO("") as buf:
            s.print_jobs(out=buf)
            assert buf.getvalue() == os.linesep.join("""Jobstore default:
    dummy (trigger: date[2016-12-12 00:00:00], next run at: 2016-12-12 00:00:00)
    dummy (trigger: date[2016-12-12 00:00:00], next run at: 2016-12-12 00:00:00)""".splitlines())+os.linesep
        s.shutdown()
        
    def test_jobstores(self):
        s = Scheduler()
        s.add_jobstore(RAMJobStore(), "ram1")
        with pytest.raises(KeyError):
            s.add_jobstore(RAMJobStore(), "ram1")
        s.remove_jobstore("ram1")
        with pytest.raises(KeyError):
            s.remove_jobstore("ram2")

    def test_listeners(self):
        s = Scheduler()
        event = SchedulerEvent(123)
        dummyCallback = unittest.mock.MagicMock()
        s.add_listener(dummyCallback)
        s._notify_listeners(event)
        dummyCallback.assert_called_once_with(event)
        s.remove_listener(dummyCallback)

    def assert_jobs(self, s, handler):
        while handler.get_count() < 2:
            pass
        for j in s.get_jobs():
            s.unschedule_job(j)
        s.reschedule()
        s.refresh()

    @slow
    def test_interval_jobs(self):
        s = Scheduler()
        s.add_jobstore(RAMJobStore(), "ram1")
        handler = CallHandler()
        s.add_interval_job(process, args=(handler,), seconds=1)
        s.start()
        self.assert_jobs(s, handler)
        s.shutdown()

    @slow
    def test_cron_jobs(self):
        s = Scheduler()
        s.add_jobstore(RAMJobStore(), "ram1")
        handler = CallHandler()
        s.add_cron_job(process, args=(handler,))
        s.start()
        self.assert_jobs(s, handler)
        s.shutdown()

    @slow
    def test_date_jobs(self):
        with unittest.mock.patch.object(datetime, "datetime", unittest.mock.Mock(wraps=datetime.datetime)) as datetimeMock:
            s = Scheduler()
            datetimeMock.now.return_value = datetime.datetime(2016, 12, 12)
            s.add_jobstore(RAMJobStore(), "ram1")
            s.start()
            handler = CallHandler()
            s.add_date_job(process, "2016-12-12", args=(handler,), misfire_grace_time=5, coalesce=True)
            while handler.get_count() < 1:
                pass
            for j in s.get_jobs():
                s.unschedule_job(j)
            s.shutdown()
