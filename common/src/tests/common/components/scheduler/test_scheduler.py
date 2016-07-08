#!/usr/bin/python3

import unittest
import pytest
import threading
import os
from io import StringIO
from gosa.common.components.scheduler.scheduler import *
from gosa.common.components.scheduler.events import *
from gosa.common.components.scheduler.jobstores.ram_store import *

class CallHandler:
    def __init__(self):
        self.lock = threading.Lock()
        self.i = 0
    def count(self):
        self.lock.acquire()
        self.i += 1
        self.lock.release()
    def get_count(self):
        self.lock.acquire()
        retval = self.i
        self.lock.release()
        return retval
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
        while len(s.get_jobs()) == 0:
            pass
        while handler.get_count() < 2:
            pass
        for j in s.get_jobs():
            s.unschedule_job(j)
        s.reschedule()
        s.refresh()
        
    @pytest.mark.skip(reason="Long running")
    def test_interval_jobs(self):
        s = Scheduler()
        s.add_jobstore(RAMJobStore(), "ram1")
        handler = CallHandler()
        s.add_interval_job(process, args=(handler,), seconds=1)
        s.start()
        self.assert_jobs(s, handler)
        s.shutdown()
    @pytest.mark.skip(reason="Long running")
    def test_cron_jobs(self):
        s = Scheduler()
        s.add_jobstore(RAMJobStore(), "ram1")
        handler = CallHandler()
        s.add_cron_job(process, args=(handler,))
        s.start()
        self.assert_jobs(s, handler)
        s.shutdown()
    @pytest.mark.skip(reason="Long running")
    def test_date_jobs(self):
        s = Scheduler()
        with unittest.mock.patch.object(datetime, "datetime", unittest.mock.Mock(wraps=datetime.datetime)) as datetimeMock:
            datetimeMock.now.return_value = datetime.datetime(2016, 12, 12)
            s.add_jobstore(RAMJobStore(), "ram1")
            s.start()
            handler = CallHandler()
            s.add_date_job(process, "2016-12-12", args=(handler,))
            while len(s.get_jobs()) == 0:
                pass
            while handler.get_count() < 1:
                pass
            for j in s.get_jobs():
                s.unschedule_job(j)
            s.shutdown()



#from gosa.common.components.scheduler.job import *
#from gosa.common.components.scheduler import *

#class InstantTrigger(object):
    #def __init__(self):
        #self.done = False
#
    #def get_next_fire_time(self, n):
        #if self.done:
            #return datetime.datetime(1995, 1, 1)
        #self.done = True
        #return datetime.datetime.now()
#
    #def __str__(self):
        #return 'now'
#
    #def __repr__(self):
        #return '<%s (run_date=now)>' % (
            #self.__class__.__name__,)
#
#def callback(arg, kwarg="TEST"):
    #assert arg == "TEST"
    #assert kwarg == "TEST2"
    #time.sleep(5)
    #assert 0
#class RAMJobStoreTestCase(unittest.TestCase):
    #def test_RAMJobStore(self):
        #s = Scheduler()
        #s.add_interval_job(callback, seconds=1, args=("TEST",), kwargs={"kwarg": "TEST2"})
        #s.start()
        #time.sleep(1)
        #while s._threadpool.num_threads:
            #pass
        #time.sleep(2)
        #assert s.get_jobs()
        #j = RAMJobStore()
        #s.add_job(InstantTrigger(), callback, ("TEST",), dict(kwarg="TEST2"))
        #time.sleep(0.1)
        #j.remove_job(j.jobs[0])
        #assert repr(j) == "<RAMJobStore>"
        #pass
