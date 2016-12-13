#!/usr/bin/python3
# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2036 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
from contextlib import contextmanager
from unittest import mock, TestCase
import pytest
import threading
from io import StringIO

import time
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


class SchedulerTestCase(TestCase):
    def test_SchedulerAlreadyRunningError(self):
        err = SchedulerAlreadyRunningError()
        assert str(err) == "Scheduler is already running"

    def test_configure(self):
        s = Scheduler()
        s.shutdown() # Does nothing
        
        gconfig = {"gosa.common.components.scheduler.jobstore.jobstoredefault.class": "gosa.common.components.scheduler.jobstores.ram_store:RAMJobStore"}
        options = {}
        
        s.configure(gconfig=gconfig)
        s.start()
        
        # If the jobstore "jobstoredefault" does not exist, an exception
        # will be raised.
        s.add_date_job(process, "2036-12-13", args=(mock.MagicMock(),), jobstore="jobstoredefault")
        
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
        trigger = SimpleTrigger("2036-12-12")
        j1 = s.add_job(trigger, dummy, (), {})
        assert isinstance(j1, Job)
        s.start()
        j2 = s.add_job(trigger, dummy, (), {})
        assert isinstance(j2, Job)
        assert len(s.get_jobs()) == 2
        with StringIO("") as buf:
            s.print_jobs(out=buf)
            assert buf.getvalue() == os.linesep.join("""Jobstore default:
    dummy (trigger: date[2036-12-12 00:00:00], next run at: 2036-12-12 00:00:00)
    dummy (trigger: date[2036-12-12 00:00:00], next run at: 2036-12-12 00:00:00)""".splitlines())+os.linesep
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
        with mock.patch.object(s, "_main_loop"):
            s.start()
            m_thread = mock.MagicMock()
            m_thread.isAlive.return_value = True
            s._thread = m_thread

            dummyCallback = mock.MagicMock()
            s.add_listener(dummyCallback)
            job = s.add_date_job(process, "2036-12-12", args=(mock.MagicMock(),))
            assert dummyCallback.called
            e = dummyCallback.call_args[0][0]
            assert isinstance(e, JobStoreEvent)
            assert e.alias == "default"
            assert e.job == job
            s.remove_listener(dummyCallback)
            s.shutdown()

    def test_get_job_by_id(self):
        s = Scheduler()
        s.start()
        job = s.add_date_job(process, "2036-12-12", args=(mock.MagicMock(),))
        assert s.get_job_by_id(job.uuid) == job
        assert s.get_job_by_id("unknown") == None
        s.shutdown()

    def test_unschedule_job(self):
        s = Scheduler()
        s.start()
        job = s.add_date_job(process, "2036-12-12", args=(mock.MagicMock(),))
        assert len(s.get_jobs()) == 1
        s.unschedule_job(job)
        assert len(s.get_jobs()) == 0
        with pytest.raises(KeyError):
            s.unschedule_job(mock.MagicMock())
        s.shutdown()

    def test_reschedule_date_job(self):

        now = datetime.datetime.now()
        with mock.patch("gosa.common.components.scheduler.scheduler.Event", wraps=Event) as m_event:
            m_event.return_value

            s = Scheduler()

            callback = mock.MagicMock()

            time1 = now + datetime.timedelta(seconds=1)

            s.start()
            time.sleep(0.1)
            m_event.return_value.wait.assert_called_with()

            job = s.add_date_job(callback, time1)
            time.sleep(0.1)
            assert round(m_event.return_value.wait.call_args[0][0]) == 1

            time2 = datetime.datetime.now() + datetime.timedelta(seconds=3)
            s.reschedule_date_job(job, time2)
            time.sleep(0.1)
            assert round(m_event.return_value.wait.call_args[0][0]) == 3

            # make sure that the callback really does not ge called on initial time
            time.sleep(1)
            assert not callback.called



        s.shutdown()


    def test_unschedule_func(self):
        s = Scheduler()
        s.start()
        s.add_date_job(process, "2036-12-12", args=(mock.MagicMock(),))
        assert len(s.get_jobs()) == 1
        s.unschedule_func(process)
        assert len(s.get_jobs()) == 0
        with pytest.raises(KeyError):
            s.unschedule_func(mock.MagicMock())
        s.shutdown()

    def assert_jobs(self, s, handler, calls=1):
        while handler.get_count() < calls:
            pass
        for j in s.get_jobs():
            s.unschedule_job(j)
        s.reschedule()
        s.refresh()

    @mock.patch("gosa.common.components.scheduler.scheduler.logger")
    def test_interval_jobs_mocked(self, loggerMock):
        with mock.patch.object(datetime, "datetime", mock.Mock(wraps=datetime.datetime)) as datetimeMock,\
                mock.patch("gosa.common.components.scheduler.scheduler.IntervalTrigger", wraps=IntervalTrigger) as triggerMock:
            datetimeMock.now.return_value = datetime.datetime(2036, 12, 12)
            triggerMock.get_next_fire_time.return_value = datetime.datetime.now()
            s = Scheduler()
            s.add_jobstore(RAMJobStore(), "ram1")
            s.start()
            handler = CallHandler()
            job = s.add_interval_job(process, args=(handler,), seconds=1, start_date=datetime.datetime.now())
            self.assert_jobs(s, handler)
            loggerMock.debug.call_args[-2:-1] == [mock.call("running job \"%s\" (scheduled at %s)" % (job, datetime.datetime.now())),
                    mock.call("job \"%s\" executed successfully" % job)]
            s.shutdown()
    @slow
    def test_interval_jobs(self):
        s = Scheduler()
        s.add_jobstore(RAMJobStore(), "ram1")
        handler = CallHandler()
        s.add_interval_job(process, args=(handler,), seconds=1)
        s.start()
        self.assert_jobs(s, handler)
        s.shutdown()

    @mock.patch("gosa.common.components.scheduler.scheduler.logger")
    def test_cron_jobs_mocked(self, loggerMock):
        with mock.patch.object(datetime, "datetime", mock.Mock(wraps=datetime.datetime)) as datetimeMock,\
                mock.patch("gosa.common.components.scheduler.scheduler.CronTrigger", wraps=CronTrigger) as triggerMock:
            datetimeMock.now.return_value = datetime.datetime(2036, 12, 12)
            triggerMock.get_next_fire_time.return_value = datetime.datetime.now()
            s = Scheduler()
            s.add_jobstore(RAMJobStore(), "ram1")
            s.start()
            handler = CallHandler()
            job = s.add_cron_job(process, args=(handler,))
            self.assert_jobs(s, handler)
            loggerMock.debug.call_args[-2:-1] == [mock.call("running job \"%s\" (scheduled at %s)" % (job, datetime.datetime.now())),
                    mock.call("job \"%s\" executed successfully" % job)]
            s.shutdown()
    @slow
    def test_cron_job(self):
        s = Scheduler()
        s.add_jobstore(RAMJobStore(), "ram1")
        handler = CallHandler()
        s.add_cron_job(process, args=(handler,))
        s.start()
        self.assert_jobs(s, handler)
        s.shutdown()

    @mock.patch("gosa.common.components.scheduler.scheduler.logger")
    def test_date_jobs_mocked(self, loggerMock):
        with mock.patch.object(datetime, "datetime", mock.Mock(wraps=datetime.datetime)) as datetimeMock:
            listener = mock.MagicMock()
            s = Scheduler()
            s.add_listener(listener, mask=EVENT_JOB_EXECUTED)
            datetimeMock.now.return_value = datetime.datetime(2036, 12, 12)
            s.add_jobstore(RAMJobStore(), "ram1")
            s.start()
            handler = CallHandler()
            job = s.add_date_job(process, "2036-12-12", args=(handler,), misfire_grace_time=5, coalesce=False)
            self.assert_jobs(s, handler)
            loggerMock.debug.call_args[-2:-1] == [mock.call("running job \"%s\" (scheduled at %s)" % (job, datetime.datetime.now())),
                    mock.call("job \"%s\" executed successfully" % job)]
            s.shutdown()
            assert listener.call_count == 1
    
    def test_decorators(self):
        s = Scheduler()
        
        @s.cron_schedule()
        def task(): pass
        assert isinstance(task.job, Job)
        
        @s.interval_schedule()
        def task(): pass
        assert isinstance(task.job, Job)
        
        s.shutdown()

    def test_exceptions(self):
        with mock.patch.object(datetime, "datetime", mock.Mock(wraps=datetime.datetime)) as datetimeMock:
            s = Scheduler()
            datetimeMock.now.return_value = datetime.datetime(2036, 12, 12)
            s.start()
            handler = CallHandler()
            with pytest.raises(ValueError): # Would not be run ever
                s.add_date_job(process, "2036-12-11", args=(handler,))
            with pytest.raises(KeyError): # Not existant job store
                s.add_date_job(process, "2036-12-13", args=(handler,), jobstore="notexistant")
            
            dummyCallback = mock.MagicMock() # Trigger error while notifying listener
            s.add_listener(dummyCallback)
            dummyCallback.side_effect = Exception
            s.add_date_job(process, "2036-12-13", args=(handler,))
            
            datetimeMock.now.return_value = datetime.datetime(2036, 12, 13)
            s.shutdown()

    def test_callback(self):
        with mock.patch.object(datetime, "datetime", mock.Mock(wraps=datetime.datetime)) as datetimeMock:
            s = Scheduler()
            datetimeMock.now.return_value = datetime.datetime(2036, 12, 12)
            def dummy(): pass
            callback = mock.MagicMock()
            s.add_job(SimpleTrigger("2036-12-12"), dummy, (), {}, callback=callback)
            s.start()
            while s.get_jobs(): pass
            s.shutdown()
            assert callback.call_count

    def test_missed_job(self):
        with mock.patch.object(datetime, "datetime", mock.Mock(wraps=datetime.datetime)) as datetimeMock:
            listener = mock.MagicMock()
            s = Scheduler()
            s.add_listener(listener, mask=EVENT_JOB_MISSED)
            datetimeMock.now.return_value = datetime.datetime(2036, 12, 12)
            def dummy(): pass
            s.add_job(SimpleTrigger("2036-12-13"), dummy, (), {})
            s.start()
            datetimeMock.now.return_value = datetime.datetime(2036, 12, 15)
            s.refresh()
            while s.get_jobs(): pass
            s.shutdown()
            assert listener.call_count == 1

    def test_max_instances(self):
        with mock.patch.object(datetime, "datetime", mock.Mock(wraps=datetime.datetime)) as datetimeMock:
            listener = mock.MagicMock()
            s = Scheduler()
            s.add_listener(listener, mask=EVENT_JOB_MISSED)
            datetimeMock.now.return_value = datetime.datetime(2036, 12, 11)
            def dummy(): pass
            s.add_job(SimpleTrigger("2036-12-12"), dummy, (), {})
            s.start()
            s.get_jobs()[0].max_instances = 0
            datetimeMock.now.return_value = datetime.datetime(2036, 12, 12)
            s.refresh()
            while s.get_jobs(): pass
            s.shutdown()
            assert listener.call_count == 1

    def test_job_failure(self):
        with mock.patch.object(datetime, "datetime", mock.Mock(wraps=datetime.datetime)) as datetimeMock:
            listener = mock.MagicMock()
            s = Scheduler()
            s.add_listener(listener, mask=EVENT_JOB_ERROR)
            datetimeMock.now.return_value = datetime.datetime(2036, 12, 12)
            def dummy():
                raise Exception
            s.add_job(SimpleTrigger("2036-12-12"), dummy, (), {})
            s.start()
            while s.get_jobs(): pass
            s.shutdown()
            assert listener.call_count == 1

    def test_multiple_jobs(self):
        with mock.patch.object(datetime, "datetime", mock.Mock(wraps=datetime.datetime)) as datetimeMock:
            s = Scheduler()
            datetimeMock.now.return_value = datetime.datetime(2036, 12, 12)
            def dummy(): pass
            s.add_job(SimpleTrigger("2036-12-13"), dummy, (), {})
            s.add_job(SimpleTrigger("2036-12-14"), dummy, (), {})
            s.start()
            s.shutdown()

    @mock.patch("gosa.common.components.scheduler.scheduler.inspect")
    @mock.patch("gosa.common.components.scheduler.scheduler.sys", wraps=sys)
    def test_set_job_property(self, sysMock, inspectMock):
        def dummy(): pass
        j = Job(SimpleTrigger("2036-12-12"), dummy, (), {}, 1, False)
        
        sysMock._getframe.return_value = mock.MagicMock()
        
        def getargvalues(fr):
            if fr:
                self_ = mock.MagicMock(name="Scheduler")
                self_.__class__.__name__ = "Scheduler"
                self_.__contains__.return_value = True
                return [0, 0, 0, {"self": self_, "job": j}]
            else:
                return mock.MagicMock()
        inspectMock.getargvalues.side_effect = getargvalues
        
        set_job_property("key", "value")
        
        assert getattr(j, "key", None) == "value"
        
        inspectMock.getargvalues.side_effect = None
        inspectMock.getargvalues.return_value = [0, 0, 0, {}]
        with pytest.raises(Exception):
            set_job_property("key", "value")
    
    def test_custom_threadpool(self):
        pool = mock.MagicMock()
        s = Scheduler(gconfig={"gosa.common.components.scheduler.threadpool": pool})
        assert pool == s._threadpool
        s.shutdown()    
