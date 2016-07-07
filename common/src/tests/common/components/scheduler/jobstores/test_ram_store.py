#!/usr/bin/python3

import unittest
import datetime
import time
from gosa.common.components.scheduler.jobstores.ram_store import *
from gosa.common.components.scheduler.triggers.simple import *
from gosa.common.components.scheduler.job import *

def dummy():
    pass

class RAMJobStoreTestCase(unittest.TestCase):
    def test_RAMJobStore(self):
        job_store = RAMJobStore()
        job_store.add_job(Job(SimpleTrigger("2016-12-12"), dummy, (), {}, 1, 0))
        job_store.load_jobs()
        job_store.update_job(None)
        job_store.migrate_jobs(None, None)
        assert len(job_store.jobs) == 1
        job_store.remove_job(job_store.jobs[0])
        assert len(job_store.jobs) == 0
        assert repr(job_store) == "<RAMJobStore>"
