#!/usr/bin/python3

import unittest
import pytest
import threading
from gosa.common.components.scheduler.scheduler import *
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

    def test_interval_jobs(self):
        s = Scheduler()
        s.add_jobstore(RAMJobStore(), "ram1")
        handler = CallHandler()
        s.add_interval_job(process, args=(handler,), seconds=1)
        s.start()
        while len(s.get_jobs()) == 0:
            pass
        while handler.get_count() < 2:
            pass
        for j in s.get_jobs():
            s.unschedule_job(j)
        
            #s.unschedule_func(process)
        #s.stop()
        s.reschedule()
        s.refresh()

    def test_cron_jobs(self):
        s = Scheduler()
        s.add_jobstore(RAMJobStore(), "ram1")
        handler = CallHandler()
        s.add_cron_job(process, args=(handler,))
        s.start()
        while len(s.get_jobs()) == 0:
            pass
        while handler.get_count() < 2:
            pass
        for j in s.get_jobs():
            #s.unschedule_job(j)
        
            s.unschedule_func(process)
        #s.stop()
        s.reschedule()
        s.refresh()



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
