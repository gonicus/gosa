#!/usr/bin/python3

import unittest, pytest
import threading
import datetime

from gosa.common.components.scheduler.jobstores.sqlalchemy_store import *
from gosa.common.components.scheduler.triggers.simple import *
from gosa.common.components.scheduler.job import *

def dummy(): pass

class SQLAlchemyJobStoreTestCase(unittest.TestCase):
    @unittest.mock.patch("gosa.common.components.scheduler.jobstores.sqlalchemy_store.Table")
    @unittest.mock.patch("gosa.common.components.scheduler.jobstores.sqlalchemy_store.create_engine")
    def test_SQLAlchemyJobStore(self, createEngineMock, tableMock, full=True):
        engine = unittest.mock.MagicMock()
        engine.url.__repr__ = lambda a: "sqlurl/test"
        def create_engine(url):
            assert url == "sqlurl/test"
            return engine
        createEngineMock.side_effect = create_engine
        
        def create(e, b):
            assert engine == e
            assert b
        tableMock.create.side_effect = create
        
        # Other methods can use this one as constructor if full=False
        if not full:
            return SQLAlchemyJobStore(engine=engine)
        
        with pytest.raises(ValueError):
            SQLAlchemyJobStore()
        
        SQLAlchemyJobStore(engine=engine)
        s = SQLAlchemyJobStore(url="sqlurl/test")
        assert repr(s) == "<SQLAlchemyJobStore (url=sqlurl/test)>"
    
    def test_add_remove_job(self):
        # Add
        job_store = self.test_SQLAlchemyJobStore(full=False)
        job = Job(SimpleTrigger("2016-12-12"), dummy, (), {}, 1, 0)
        
        def execute(arg):
            assert arg == job_store.jobs_t.insert().values(**job.__getstate__())
            result = unittest.mock.MagicMock()
            result.inserted_primary_key = (9876,)
            return result
        job_store.engine.execute.side_effect = execute
        
        job_store.add_job(job)
        assert job in job_store.jobs
        assert job.id == 9876
        assert job_store.engine.execute.call_count == 1
        
        
        # Remove
        def execute(arg):
            assert arg == job_store.jobs_t.delete().where(job_store.jobs_t.c.id == job.id)
        job_store.engine.execute.side_effect = execute
        
        job_store.remove_job(job)
        
        assert job not in job_store.jobs
        assert job_store.engine.execute.call_count == 2
    
    @unittest.mock.patch("gosa.common.components.scheduler.jobstores.sqlalchemy_store.select")
    def test_load_jobs(self, selectMock):
        dummy_ref = "tests.common.components.scheduler.jobstores.test_sqlalchemy_store:dummy"
        dummy_lock = threading.Lock()
        
        job_store = self.test_SQLAlchemyJobStore(full=False)
        
        selectParam = object()
        
        def select(arg):
            assert arg == [job_store.jobs_t]
            return selectParam
        selectMock.side_effect = select
        
        def execute(arg):
            assert arg == selectParam
            row1 = unittest.mock.MagicMock()
            row1.items.return_value = [("instances", 0), ("func_ref", dummy_ref), ("callback_ref", dummy_ref), ("_lock", dummy_lock), ("status", "NOT_WAITING")]
            row2 = unittest.mock.MagicMock()
            row2.items.return_value = [("instances", 0), ("func_ref", dummy_ref), ("callback_ref", dummy_ref), ("_lock", threading.Lock())]
            result = unittest.mock.MagicMock()
            result.__iter__.return_value = [row1, row2]
            return result
        job_store.engine.execute.side_effect = execute
        
        job_store.load_jobs()
        
        assert job_store.jobs[0].instances == 0
        assert job_store.jobs[0].func == dummy
        assert job_store.jobs[0].callback == dummy
        #assert job_store.jobs[0]._lock == dummy_lock
        # Lock is recreated?
        assert job_store.jobs[0].status == JOB_ERROR

    def test_update_job(self):
        job_store = self.test_SQLAlchemyJobStore(full=False)
        
        job = Job(SimpleTrigger("2016-12-12"), dummy, (), {}, 1, 0)
        job.next_run_time = datetime.datetime(2016, 12, 12)
        job_store.add_job(job)
        
        updateParam = object()
        
        def values(next_run_time=None, runs=None):
            assert next_run_time != None
            assert runs != None
            return updateParam
        valuesMock = unittest.mock.MagicMock()
        valuesMock.values.side_effect = values
        def where(arg):
            #assert arg == True
            return valuesMock
        updateMock = unittest.mock.MagicMock()
        updateMock.where.side_effect = where
        job_store.jobs_t.update.return_value = updateMock
        def update(arg):
            assert arg
        
        def execute(arg):
            assert arg == updateParam
        job_store.engine.execute.side_effect = execute
        
        #job.
        
        job_store.update_job(job)

    def test_close(self):
        job_store = self.test_SQLAlchemyJobStore(full=False)
        job_store.close()
        job_store.engine.dispose.assert_called_once_with()
        
    
