# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
Stores jobs in a database table using SQLAlchemy.
"""
import pickle
import logging

from gosa.common.components.scheduler.jobstores.base import JobStore
from gosa.common.components.scheduler.job import Job, JOB_WAITING, JOB_ERROR

try:
    from sqlalchemy import create_engine, Table, MetaData, Column, Integer, Sequence, PickleType, Boolean, BigInteger, select, and_, String, Unicode, DateTime
except ImportError:  # pragma: nocover
    raise ImportError('SQLAlchemyJobStore requires SQLAlchemy installed')

logger = logging.getLogger(__name__)


class SQLAlchemyJobStore(JobStore):
    def __init__(self, url=None, engine=None, tablename='gosa.common.components.scheduler_jobs',
                 metadata=None, pickle_protocol=pickle.HIGHEST_PROTOCOL):
        self.jobs = []
        self.pickle_protocol = pickle_protocol

        if engine:
            self.engine = engine
        elif url:
            self.engine = create_engine(url)
        else:
            raise ValueError('Need either "engine" or "url" defined')

        self.jobs_t = Table(tablename, metadata or MetaData(),
            Column('id', Integer,
                   Sequence(tablename + '_id_seq', optional=True),
                   primary_key=True),
            Column('trigger', PickleType(pickle_protocol),
                   nullable=False),
            Column('func_ref', String(1024), nullable=False),
            Column('args', PickleType(pickle_protocol),
                   nullable=False),
            Column('kwargs', PickleType(pickle_protocol),
                   nullable=False),
            Column('name', Unicode(1024)),
            Column('misfire_grace_time', Integer, nullable=False),
            Column('coalesce', Boolean, nullable=False),
            Column('owner', String(1024), nullable=True),
            Column('tag', String(1024), nullable=True),
            Column('description', String(1024), nullable=True),
            Column('callback_ref', String(1024), nullable=True),
            Column('progress', Integer, nullable=False),
            Column('status', Integer, nullable=False),
            Column('max_runs', Integer),
            Column('max_instances', Integer),
            Column('next_run_time', DateTime, nullable=False),
            Column('runs', BigInteger),
            Column('uuid', String(1024), nullable=False),
            Column('job_type', String(1024), nullable=False),
            Column('callback', String(1024), nullable=True))

        self.jobs_t.create(self.engine, True)

    def add_job(self, job):
        job_dict = job.__getstate__()
        result = self.engine.execute(self.jobs_t.insert().values(**job_dict))
        job.id = result.inserted_primary_key[0]
        self.jobs.append(job)

    def remove_job(self, job):
        delete = self.jobs_t.delete().where(self.jobs_t.c.id == job.id)
        self.engine.execute(delete)
        self.jobs.remove(job)

    def load_jobs(self):
        jobs = []
        for row in self.engine.execute(select([self.jobs_t])):
            try:
                job = Job.__new__(Job)
                job_dict = dict(row.items())
                job.__setstate__(job_dict)

                # Set jobs that have not been executed completely to ERROR
                if job.status != JOB_WAITING:
                    job.status = JOB_ERROR

                # Treat our local jobs differently
                jobs.append(job)

            except Exception:
                job_name = job_dict.get('name', '(unknown)')
                logger.exception('Unable to restore job "%s"', job_name)

        self.jobs = jobs

    def update_job(self, job):
        job_dict = job.__getstate__()
        update = self.jobs_t.update().where(self.jobs_t.c.id == job.id).\
            values(next_run_time=job_dict['next_run_time'],
                   runs=job_dict['runs'])
        self.engine.execute(update)

    def close(self):
        self.engine.dispose()

    def __repr__(self):
        return '<%s (url=%s)>' % (self.__class__.__name__, self.engine.url)
