# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
from gosa.backend.components.scheduler import *
from gosa.common.components.scheduler.job import JOB_WAITING

class SchedulerServiceTestCase(unittest.TestCase):

    def setUp(self):
        self.service = SchedulerService()
        self.service.serve()

    def tearDown(self):
        self.service.stop()


    def test_getScheduler(self):
        assert type(self.service.getScheduler()) == Scheduler


    def test_schedulerAddDateJob(self):
        jobid = self.service.schedulerAddDateJob("admin","queue", "getMethods", [], [], "20990101000000", jobstore='ram')
        jobs = self.service.schedulerGetJobs()
        assert len(jobs) == 1
        assert jobid in jobs
        assert jobs[jobid]['job_type'] == 'date'

        jobs = self.service.schedulerGetJobs({'tag':'service'})
        assert len(jobs) == 0

        jobs = self.service.schedulerGetJobs({'coalesce': True})
        assert len(jobs) == 1
        assert jobid in jobs

    def test_schedulerIntervalJob(self):
        jobid = self.service.schedulerIntervalJob("admin","queue", "getMethods", [], [], days=1, jobstore='ram')
        jobs = self.service.schedulerGetJobs()
        assert len(jobs) == 1
        assert jobid in jobs
        assert jobs[jobid]['job_type'] == 'interval'

    def test_schedulerCronJob(self):
        jobid = self.service.schedulerCronDateJob("admin","queue", "getMethods", [], [], day_of_week=0, jobstore='ram')
        jobs = self.service.schedulerGetJobs()
        assert len(jobs) == 1
        assert jobid in jobs
        assert jobs[jobid]['job_type'] == 'cron'


    def test_schedulerRemoveJob(self):
        jobid = self.service.schedulerAddDateJob("admin", "queue", "getMethods", [], [], "20990101000000", jobstore='ram')
        jobs = self.service.schedulerGetJobs()
        assert len(jobs) == 1
        assert jobid in jobs

        job = self.service.sched.get_job_by_id(jobid)
        job.status = JOB_RUNNING
        assert self.service.schedulerRemoveJob("admin", jobid) is False
        jobs = self.service.schedulerGetJobs()
        assert len(jobs) == 1

        job.status = JOB_WAITING
        assert self.service.schedulerRemoveJob("admin", jobid) is True
        jobs = self.service.schedulerGetJobs()
        assert len(jobs) == 0