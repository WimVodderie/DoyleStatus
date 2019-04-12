import logging
import datetime

from app import doylequeuedb

testDbPath="./TestData/TestDb"

class TestDoyleQueueDb:
    def setup(self):
        self.d = doylequeuedb.DoyleQueueDb(testDbPath)

    def teardown(self):
        self.d.quit()

    def test_init(self):
        start_date=datetime.datetime(year=2000,month=1,day=1)
        end_date=datetime.datetime(year=2000,month=12,day=31)
        assert len(self.d.getCounts(start_date,end_date)) == 0
