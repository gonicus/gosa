#!/usr/bin/python3

import unittest
from gosa.common.components.scheduler.jobstores.base import *

class BaseTestCase(unittest.TestCase):
    def test_add_job(self):
        j = JobStore()
        self.assertRaises(NotImplementedError, j.add_job, None)
    def test_update_job(self):
        j = JobStore()
        self.assertRaises(NotImplementedError, j.update_job, None)
    def test_remove_job(self):
        j = JobStore()
        self.assertRaises(NotImplementedError, j.remove_job, None)
    def test_load_jobs(self):
        j = JobStore()
        self.assertRaises(NotImplementedError, j.load_jobs)
    def test_migrate_jobs(self):
        j = JobStore()
        self.assertRaises(NotImplementedError, j.migrate_jobs, None, None)
